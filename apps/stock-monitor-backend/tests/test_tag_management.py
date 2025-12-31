
import pytest
from httpx import AsyncClient
from app.main import app

# Base URL for tag API
BASE_URL = "/api/v1/tags"

@pytest.mark.asyncio
async def test_create_tag(test_client: AsyncClient):
    # Test creating a new tag
    tag_data = {"name": "TestTag_Unit", "score": 8.5}
    response = await test_client.post(BASE_URL, json=tag_data)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "TestTag_Unit"
    assert float(data["data"]["score"]) == 8.5
    
    # Test duplicate creation
    response = await test_client.post(BASE_URL, json=tag_data)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "already exists" in data["message"]

@pytest.mark.asyncio
async def test_get_tags(test_client: AsyncClient):
    # Create some tags first
    await test_client.post(BASE_URL, json={"name": "Tag1", "score": 1.0})
    await test_client.post(BASE_URL, json={"name": "Tag2", "score": 2.0})
    
    # Test list
    response = await test_client.get(BASE_URL)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["total"] >= 2
    items = data["data"]["items"]
    assert any(item["name"] == "Tag1" for item in items)
    
    # Test search
    response = await test_client.get(BASE_URL, params={"name": "Tag1"})
    data = response.json()
    items = data["data"]["items"]
    assert len(items) >= 1
    assert items[0]["name"] == "Tag1"

@pytest.mark.asyncio
async def test_update_tag(test_client: AsyncClient):
    # Create tag
    create_res = await test_client.post(BASE_URL, json={"name": "TagToUpdate", "score": 5.0})
    tag_id = create_res.json()["data"]["id"]
    
    # Update score
    update_data = {"score": 6.0}
    response = await test_client.put(f"{BASE_URL}/{tag_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert float(data["data"]["score"]) == 6.0
    
    # Update name
    update_data = {"name": "TagUpdated"}
    response = await test_client.put(f"{BASE_URL}/{tag_id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "TagUpdated"

@pytest.mark.asyncio
async def test_delete_tag(test_client: AsyncClient):
    # Create tag
    create_res = await test_client.post(BASE_URL, json={"name": "TagToDelete", "score": 5.0})
    tag_id = create_res.json()["data"]["id"]
    
    # Delete
    response = await test_client.delete(f"{BASE_URL}/{tag_id}")
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # Verify deleted (soft delete usually excludes from list)
    response = await test_client.get(BASE_URL, params={"name": "TagToDelete"})
    items = response.json()["data"]["items"]
    assert len(items) == 0

@pytest.mark.asyncio
async def test_batch_import(test_client: AsyncClient):
    batch_data = [
        {"name": "Batch1", "score": 1.0},
        {"name": "Batch2", "score": 2.0}
    ]
    response = await test_client.post(f"{BASE_URL}/batch", json=batch_data)
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["success"] == 2
    assert data["data"]["failed"] == 0

@pytest.mark.asyncio
async def test_stock_association(test_client: AsyncClient):
    # Create tag
    create_res = await test_client.post(BASE_URL, json={"name": "TagStock", "score": 10.0})
    tag_id = create_res.json()["data"]["id"]
    
    # Associate
    stock_codes = ["000001", "000002"]
    response = await test_client.post(f"{BASE_URL}/{tag_id}/stocks", json={"stock_codes": stock_codes, "tag_id": tag_id})
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # Check Tag Stocks
    response = await test_client.get(f"{BASE_URL}/{tag_id}/stocks")
    assert response.status_code == 200
    stocks = response.json()["data"]
    assert "000001" in stocks
    assert "000002" in stocks
    
    # Check Stock Tags
    response = await test_client.get(f"{BASE_URL}/stocks/000001")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["stock_code"] == "000001"
    assert any(t["name"] == "TagStock" for t in data["tags"])
    assert float(data["total_score"]) == 10.0
    
    # Dissociate
    # Use request method to send body with DELETE
    response = await test_client.request("DELETE", f"{BASE_URL}/{tag_id}/stocks", json={"stock_codes": ["000001"], "tag_id": tag_id})
    assert response.status_code == 200
    
    # Verify dissociation
    response = await test_client.get(f"{BASE_URL}/{tag_id}/stocks")
    stocks = response.json()["data"]
    assert "000001" not in stocks
    assert "000002" in stocks

@pytest.mark.asyncio
async def test_operation_logs(test_client: AsyncClient):
    # Trigger some operations
    await test_client.post(BASE_URL, json={"name": "LogTag", "score": 1.0})
    
    # Get logs
    response = await test_client.get(f"{BASE_URL}/logs")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] > 0
    assert data["items"][0]["target_type"] == "tag"
