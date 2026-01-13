import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.models.generic_task import GenericTask
from app.models.task_execution_detail import TaskExecutionDetail

@pytest.mark.asyncio
async def test_generic_task_lifecycle(test_client: AsyncClient, test_session: AsyncSession):
    """
    测试通用任务的完整生命周期：
    创建 -> 查询 -> 模拟执行历史 -> 查询历史 -> 更新 -> 删除
    """
    # 1. 创建任务
    task_data = {
        "name": "Integration Test Task",
        "task_category": "test",
        "api_endpoint": "/api/v1/health",
        "api_method": "GET",
        "cron_expression": "*/10 * * * *",
        "description": "Created by unit test",
        "is_active": True
    }
    
    response = await test_client.post("/api/v1/generic-task", json=task_data)
    assert response.status_code == 200, f"Create task failed: {response.text}"
    result = response.json()
    assert result["success"] is True
    task_id = result["data"]["id"]
    assert task_id is not None
    assert result["data"]["name"] == task_data["name"]

    # 2. 获取任务列表
    response = await test_client.get("/api/v1/generic-task")
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    tasks = result["data"]
    assert len(tasks) > 0
    # 确认新创建的任务在列表中
    assert any(t["id"] == task_id for t in tasks)

    # 3. 模拟插入执行历史记录 (直接操作DB)
    # 注意：这里我们手动插入一条记录来验证 history 接口能否查到
    detail = TaskExecutionDetail(
        task_id=task_id,
        start_time=datetime.now(),
        end_time=datetime.now(),
        duration=0.5,
        status="success",
        response_code=200,
        response_data='{"status": "ok"}',
        error_message=None
    )
    test_session.add(detail)
    await test_session.commit()
    await test_session.refresh(detail)

    # 4. 测试获取执行历史接口
    response = await test_client.get(f"/api/v1/generic-task/{task_id}/history")
    assert response.status_code == 200
    result = response.json()
    if not result["success"]:
        print(f"History API failed: {result.get('message')}")
    assert result["success"] is True
    history = result["data"]
    assert len(history) == 1
    record = history[0]
    assert record["task_id"] == task_id
    assert record["status"] == "success"
    assert record["response_code"] == 200
    assert record["duration"] == 0.5

    # 5. 更新任务
    update_data = {
        "name": "Updated Task Name",
        "is_active": False
    }
    response = await test_client.put(f"/api/v1/generic-task/{task_id}", json=update_data)
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert result["data"]["name"] == "Updated Task Name"
    assert result["data"]["is_active"] is False

    # 6. 删除任务
    response = await test_client.delete(f"/api/v1/generic-task/{task_id}")
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True

    # 7. 再次查询确认已删除
    response = await test_client.get("/api/v1/generic-task")
    result = response.json()
    tasks = result["data"]
    assert not any(t["id"] == task_id for t in tasks)


@pytest.mark.asyncio
async def test_generic_task_batch_operations(test_client: AsyncClient, test_session: AsyncSession):
    """
    测试通用任务的批量操作：
    批量创建 -> 批量启用/禁用 -> 验证状态
    """
    # 1. 批量创建
    batch_data = {
        "tasks": [
            {
                "name": "Batch Task 1",
                "task_category": "batch_test",
                "api_endpoint": "/api/v1/health",
                "api_method": "GET",
                "cron_expression": "*/5 * * * *",
                "is_active": True
            },
            {
                "name": "Batch Task 2",
                "task_category": "batch_test",
                "api_endpoint": "/api/v1/health",
                "api_method": "GET",
                "cron_expression": "*/5 * * * *",
                "is_active": True
            }
        ]
    }
    
    response = await test_client.post("/api/v1/generic-task/batch/create", json=batch_data)
    assert response.status_code == 200, f"Batch create failed: {response.text}"
    result = response.json()
    assert result["success"] is True
    created_tasks = result["data"]
    assert len(created_tasks) == 2
    task_ids = [t["id"] for t in created_tasks]
    
    # 2. 批量禁用
    toggle_data = {
        "task_ids": task_ids,
        "is_active": False
    }
    response = await test_client.post("/api/v1/generic-task/batch/toggle", json=toggle_data)
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    
    # 3. 验证状态
    response = await test_client.get("/api/v1/generic-task")
    assert response.status_code == 200
    all_tasks = response.json()["data"]
    for t_id in task_ids:
        task = next((t for t in all_tasks if t["id"] == t_id), None)
        assert task is not None
        assert task["is_active"] is False
        
    # 4. 批量启用
    toggle_data["is_active"] = True
    response = await test_client.post("/api/v1/generic-task/batch/toggle", json=toggle_data)
    assert response.status_code == 200
    
    # 5. 清理
    for t_id in task_ids:
        await test_client.delete(f"/api/v1/generic-task/{t_id}")
