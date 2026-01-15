"""
多模型协作日志数据模型
记录GLM4.7、Gemini、DeepSeek之间的协作历史
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from app.models.base import Base


class CollaborationLog(Base):
    """协作日志表"""
    __tablename__ = "collaboration_logs"

    id = Column(Integer, primary_key=True, index=True, comment="日志ID")
    
    # 协作信息
    conversation_id = Column(String(100), index=True, comment="对话ID")
    session_id = Column(String(100), index=True, comment="会话ID")
    
    # 模型信息
    from_model = Column(String(50), nullable=False, comment="发起模型（GLM4.7/Gemini/DeepSeek）")
    to_model = Column(String(50), nullable=False, comment="目标模型（GLM4.7/Gemini/DeepSeek）")
    
    # 消息内容
    message_type = Column(String(50), nullable=False, comment="消息类型（request/response/error）")
    message_content = Column(Text, comment="消息内容")
    
    # 文档信息
    doc_type = Column(String(50), comment="文档类型（daily_progress/weekly_report/technical_review/test_report）")
    doc_path = Column(String(500), comment="文档路径")
    
    # 状态信息
    status = Column(String(50), default="pending", comment="状态（pending/processing/completed/failed）")
    error_message = Column(Text, comment="错误信息")
    
    # 时间信息
    created_at = Column(DateTime, server_default=func.current_timestamp(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.current_timestamp(), 
                    onupdate=func.current_timestamp(), comment="更新时间")
    
    # 元数据
    metadata = Column(Text, comment="元数据（JSON格式）")
    
    def __repr__(self):
        return f"<CollaborationLog(id={self.id}, from={self.from_model}, to={self.to_model}, status={self.status})>"


class DocumentVersion(Base):
    """文档版本表"""
    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True, index=True, comment="版本ID")
    
    # 文档信息
    doc_path = Column(String(500), nullable=False, index=True, comment="文档路径")
    doc_type = Column(String(50), nullable=False, comment="文档类型")
    version = Column(String(50), nullable=False, comment="版本号（v1.0.0）")
    
    # 作者信息
    author = Column(String(50), nullable=False, comment="作者模型（GLM4.7/Gemini/DeepSeek）")
    signature = Column(String(500), comment="署名信息")
    
    # 内容信息
    content = Column(Text, comment="文档内容")
    content_hash = Column(String(64), comment="内容哈希（MD5）")
    
    # 备份信息
    backup_path = Column(String(500), comment="备份文件路径")
    
    # 变更信息
    change_description = Column(Text, comment="变更描述")
    
    # 时间信息
    created_at = Column(DateTime, server_default=func.current_timestamp(), comment="创建时间")
    
    def __repr__(self):
        return f"<DocumentVersion(id={self.id}, doc={self.doc_path}, version={self.version}, author={self.author})>"


class CollaborationSession(Base):
    """协作会话表"""
    __tablename__ = "collaboration_sessions"

    id = Column(Integer, primary_key=True, index=True, comment="会话ID")
    session_id = Column(String(100), unique=True, nullable=False, index=True, comment="会话ID")
    
    # 会话信息
    title = Column(String(200), comment="会话标题")
    doc_type = Column(String(50), comment="关联的文档类型")
    doc_path = Column(String(500), comment="关联的文档路径")
    
    # 参与模型
    participants = Column(String(200), comment="参与模型（逗号分隔）")
    
    # 状态信息
    status = Column(String(50), default="active", comment="状态（active/completed/archived）")
    
    # 统计信息
    message_count = Column(Integer, default=0, comment="消息数量")
    version_count = Column(Integer, default=0, comment="版本数量")
    
    # 时间信息
    created_at = Column(DateTime, server_default=func.current_timestamp(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.current_timestamp(), 
                    onupdate=func.current_timestamp(), comment="更新时间")
    completed_at = Column(DateTime, comment="完成时间")
    
    # 元数据
    metadata = Column(Text, comment="元数据（JSON格式）")
    
    def __repr__(self):
        return f"<CollaborationSession(id={self.id}, session_id={self.session_id}, status={self.status})>"