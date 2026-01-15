"""
MCP系统集成测试用例
测试DeepSeek + Trae AI模型协作系统的功能
"""
import pytest
import asyncio
import httpx
from pathlib import Path
from app.models.collaboration_log import CollaborationLog, DocumentVersion, CollaborationSession
from app.services.collaboration_service import CollaborationService
from app.services.deepseek_mcp_service import DeepSeekMCPService, DeepSeekMessage
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.database import Base
import os


# 测试数据库URL
TEST_DATABASE_URL = "sqlite:///./test_collaboration.db"


@pytest.fixture
async def db_session():
    """创建测试数据库会话"""
    # 创建测试数据库引擎
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 创建会话工厂
    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # 提供会话
    async with async_session_maker() as session:
        yield session
    
    # 清理
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    # 删除测试数据库
    if os.path.exists("./test_collaboration.db"):
        os.remove("./test_collaboration.db")


@pytest.fixture
def collab_service():
    """创建协作服务实例"""
    return CollaborationService("test_collaboration_docs")


@pytest.fixture
def http_client():
    """创建HTTP客户端"""
    return httpx.AsyncClient(base_url="http://localhost:8000")


# ============================================================================
# 协作文档服务测试
# ============================================================================

class TestCollaborationService:
    """协作文档服务测试"""
    
    @pytest.mark.asyncio
    async def test_create_document(self, collab_service, db_session):
        """测试创建协作文档"""
        result = await collab_service.create_document(
            doc_type="daily_progress",
            title="测试日报",
            content="今日完成了测试工作",
            author="GLM4.7",
            db=db_session
        )
        
        assert result["success"] is True
        assert "filepath" in result
        assert "filename" in result
        assert Path(result["filepath"]).exists()
    
    @pytest.mark.asyncio
    async def test_update_document(self, collab_service, db_session):
        """测试更新协作文档"""
        # 先创建文档
        create_result = await collab_service.create_document(
            doc_type="daily_progress",
            title="测试日报",
            content="原始内容",
            author="GLM4.7",
            db=db_session
        )
        
        # 更新文档
        update_result = await collab_service.update_document(
            doc_path=Path(create_result["filepath"]).relative_to("test_collaboration_docs"),
            content="更新后的内容",
            signature="[2026-01-14 12:00] @GLM4.7: 更新内容",
            author="GLM4.7",
            db=db_session
        )
        
        assert update_result["success"] is True
        assert "backup" in update_result
        assert Path(update_result["backup"]).exists()
    
    @pytest.mark.asyncio
    async def test_get_document(self, collab_service):
        """测试获取协作文档"""
        # 先创建文档
        create_result = await collab_service.create_document(
            doc_type="daily_progress",
            title="测试日报",
            content="测试内容",
            author="GLM4.7",
            db=None
        )
        
        # 获取文档
        doc_path = Path(create_result["filepath"]).relative_to("test_collaboration_docs")
        get_result = await collab_service.get_document(str(doc_path))
        
        assert get_result["success"] is True
        assert "content" in get_result
        assert "metadata" in get_result
    
    @pytest.mark.asyncio
    async def test_list_documents(self, collab_service):
        """测试列出协作文档"""
        # 创建多个文档
        for i in range(3):
            await collab_service.create_document(
                doc_type="daily_progress",
                title=f"测试日报{i}",
                content=f"测试内容{i}",
                author="GLM4.7",
                db=None
            )
        
        # 列出文档
        list_result = await collab_service.list_documents()
        
        assert list_result["success"] is True
        assert list_result["count"] >= 3
        assert "documents" in list_result
    
    @pytest.mark.asyncio
    async def test_invalid_doc_type(self, collab_service):
        """测试无效的文档类型"""
        result = await collab_service.create_document(
            doc_type="invalid_type",
            title="测试日报",
            content="测试内容",
            author="GLM4.7",
            db=None
        )
        
        assert result["success"] is False
        assert "error" in result


# ============================================================================
# MCP API测试
# ============================================================================

class TestMCPAPI:
    """MCP API测试"""
    
    @pytest.mark.asyncio
    async def test_health_check(self, http_client):
        """测试健康检查"""
        response = await http_client.get("/mcp/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self, http_client):
        """测试根路径"""
        response = await http_client.get("/mcp/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
    
    @pytest.mark.asyncio
    async def test_create_collaboration_doc(self, http_client):
        """测试创建协作文档API"""
        response = await http_client.post(
            "/mcp/collaboration/doc/create",
            json={
                "doc_type": "daily_progress",
                "title": "API测试日报",
                "content": "通过API创建的测试文档",
                "author": "GLM4.7"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    @pytest.mark.asyncio
    async def test_list_collaboration_docs(self, http_client):
        """测试列出协作文档API"""
        response = await http_client.get("/mcp/collaboration/docs")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "documents" in data
    
    @pytest.mark.asyncio
    async def test_invalid_model(self, http_client):
        """测试无效的模型"""
        response = await http_client.post(
            "/mcp/collaboration/doc/create",
            json={
                "doc_type": "daily_progress",
                "title": "测试日报",
                "content": "测试内容",
                "author": "InvalidModel"
            }
        )
        
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data


# ============================================================================
# DeepSeek MCP服务测试
# ============================================================================

class TestDeepSeekMCPService:
    """DeepSeek MCP服务测试"""
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, db_session):
        """测试服务初始化"""
        service = DeepSeekMCPService(db_session)
        
        success = await service.initialize()
        
        assert success is True
        assert service.initialized is True
    
    @pytest.mark.asyncio
    async def test_login_without_credentials(self, db_session):
        """测试无凭证登录"""
        service = DeepSeekMCPService(db_session)
        await service.initialize()
        
        result = await service.login("", "")
        
        # 应该失败或返回错误
        assert result.get("success") is False or "error" in result
    
    @pytest.mark.asyncio
    async def test_send_message_without_login(self, db_session):
        """测试未登录发送消息"""
        service = DeepSeekMCPService(db_session)
        await service.initialize()
        
        message = DeepSeekMessage(message="测试消息")
        result = await service.send_message(message)
        
        # 应该失败
        assert result.success is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_start_new_session(self, db_session):
        """测试开始新会话"""
        service = DeepSeekMCPService(db_session)
        await service.initialize()
        
        result = await service.start_new_session()
        
        # 应该返回会话ID
        assert "success" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_get_conversations(self, db_session):
        """测试获取对话历史"""
        service = DeepSeekMCPService(db_session)
        await service.initialize()
        
        result = await service.get_conversation_history()
        
        assert result["success"] is True
        assert "conversations" in result


# ============================================================================
# 数据模型测试
# ============================================================================

class TestDatabaseModels:
    """数据模型测试"""
    
    @pytest.mark.asyncio
    async def test_collaboration_log_model(self, db_session):
        """测试协作日志模型"""
        log = CollaborationLog(
            conversation_id="test_conv_1",
            session_id="test_session_1",
            from_model="GLM4.7",
            to_model="DeepSeek",
            message_type="request",
            message_content="测试消息",
            status="pending"
        )
        
        db_session.add(log)
        await db_session.commit()
        
        assert log.id is not None
        assert log.conversation_id == "test_conv_1"
    
    @pytest.mark.asyncio
    async def test_document_version_model(self, db_session):
        """测试文档版本模型"""
        version = DocumentVersion(
            doc_path="test_doc.md",
            doc_type="daily_progress",
            version="v1.0.0",
            author="GLM4.7",
            signature="[2026-01-14 12:00] @GLM4.7: 创建文档",
            content="# 测试文档\n\n这是测试内容",
            content_hash="test_hash",
            change_description="创建文档"
        )
        
        db_session.add(version)
        await db_session.commit()
        
        assert version.id is not None
        assert version.version == "v1.0.0"
    
    @pytest.mark.asyncio
    async def test_collaboration_session_model(self, db_session):
        """测试协作会话模型"""
        session = CollaborationSession(
            session_id="test_session_1",
            title="测试会话",
            doc_type="daily_progress",
            participants="GLM4.7,DeepSeek",
            status="active"
        )
        
        db_session.add(session)
        await db_session.commit()
        
        assert session.id is not None
        assert session.session_id == "test_session_1"


# ============================================================================
# 集成测试
# ============================================================================

class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_document_workflow(self, collab_service, db_session):
        """测试完整的文档工作流"""
        # 1. 创建文档
        create_result = await collab_service.create_document(
            doc_type="daily_progress",
            title="集成测试日报",
            content="原始内容",
            author="GLM4.7",
            db=db_session
        )
        assert create_result["success"] is True
        
        # 2. 获取文档
        doc_path = Path(create_result["filepath"]).relative_to("test_collaboration_docs")
        get_result = await collab_service.get_document(str(doc_path))
        assert get_result["success"] is True
        
        # 3. 更新文档
        update_result = await collab_service.update_document(
            doc_path=str(doc_path),
            content="更新后的内容",
            signature="[2026-01-14 13:00] @GLM4.7: 更新内容",
            author="GLM4.7",
            db=db_session
        )
        assert update_result["success"] is True
        
        # 4. 列出文档
        list_result = await collab_service.list_documents()
        assert list_result["success"] is True
        assert list_result["count"] >= 1
    
    @pytest.mark.asyncio
    async def test_multiple_documents_workflow(self, collab_service):
        """测试多个文档的工作流"""
        # 创建多个文档
        doc_types = ["daily_progress", "weekly_report", "technical_review", "test_report"]
        
        for doc_type in doc_types:
            result = await collab_service.create_document(
                doc_type=doc_type,
                title=f"{doc_type}测试",
                content=f"{doc_type}的测试内容",
                author="GLM4.7",
                db=None
            )
            assert result["success"] is True
        
        # 列出所有文档
        list_result = await collab_service.list_documents()
        assert list_result["success"] is True
        assert list_result["count"] >= 4


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])