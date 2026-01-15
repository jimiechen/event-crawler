"""
协作文档管理服务
管理Markdown文档的创建、更新、版本控制和署名
"""
import os
import json
import time
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from jinja2 import Template
from app.models.collaboration_log import DocumentVersion, CollaborationSession
import logging

logger = logging.getLogger(__name__)


class CollaborationService:
    """协作文档管理服务"""
    
    def __init__(self, base_dir: str = "collaboration_docs"):
        self.base_dir = Path(base_dir)
        self.ensure_directories()
    
    def ensure_directories(self):
        """确保目录结构存在"""
        directories = [
            "daily_progress",
            "weekly_report", 
            "technical_review",
            "test_report",
            "archive"
        ]
        
        for dir_name in directories:
            (self.base_dir / dir_name).mkdir(parents=True, exist_ok=True)
    
    async def create_document(self, doc_type: str, title: str, content: str, 
                          author: str = "GLM4.7", db=None) -> Dict[str, Any]:
        """创建新的协作文档"""
        try:
            # 验证文档类型
            valid_types = ["daily_progress", "weekly_report", "technical_review", "test_report"]
            if doc_type not in valid_types:
                return {
                    "success": False,
                    "error": f"无效的文档类型: {doc_type}，有效类型: {valid_types}"
                }
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{doc_type}_{timestamp}.md"
            
            # 确定保存路径
            filepath = self.base_dir / doc_type / filename
            
            # 构建文档内容
            doc_content = self._build_document_content(title, content, author, doc_type)
            
            # 保存文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(doc_content)
            
            logger.info(f"创建文档: {filepath}")
            
            # 记录文档版本
            if db:
                version = DocumentVersion(
                    doc_path=str(filepath.relative_to(self.base_dir)),
                    doc_type=doc_type,
                    version="v1.0.0",
                    author=author,
                    signature=f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] @{author}: 创建文档",
                    content=doc_content,
                    content_hash=self._calculate_hash(doc_content),
                    change_description="创建文档"
                )
                db.add(version)
                await db.commit()
            
            return {
                "success": True,
                "filepath": str(filepath),
                "filename": filename,
                "message": "文档创建成功"
            }
            
        except Exception as e:
            logger.error(f"创建文档失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_document(self, doc_path: str, content: str, signature: str, 
                          author: str = "GLM4.7", db=None) -> Dict[str, Any]:
        """更新现有文档"""
        try:
            # 确保路径在base_dir内
            full_path = self.base_dir / doc_path
            if not full_path.exists():
                return {
                    "success": False,
                    "error": f"文档不存在: {doc_path}"
                }
            
            # 读取现有内容
            with open(full_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()
            
            # 解析现有内容以更新元数据
            updated_content = self._update_document_content(
                existing_content, content, signature, author
            )
            
            # 备份旧版本
            backup_path = full_path.with_suffix(f".{int(time.time())}.bak")
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(existing_content)
            
            # 写入新内容
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            logger.info(f"更新文档: {full_path}, 作者: {author}")
            
            # 记录文档版本
            if db:
                version = DocumentVersion(
                    doc_path=doc_path,
                    doc_type=self._extract_doc_type(doc_path),
                    version=self._increment_version(existing_content),
                    author=author,
                    signature=signature,
                    content=updated_content,
                    content_hash=self._calculate_hash(updated_content),
                    backup_path=str(backup_path.relative_to(self.base_dir)),
                    change_description=signature
                )
                db.add(version)
                await db.commit()
            
            return {
                "success": True,
                "filepath": str(full_path),
                "backup": str(backup_path),
                "message": "文档更新成功"
            }
            
        except Exception as e:
            logger.error(f"更新文档失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_document(self, doc_path: str) -> Dict[str, Any]:
        """获取文档内容"""
        try:
            full_path = self.base_dir / doc_path
            if not full_path.exists():
                return {
                    "success": False,
                    "error": f"文档不存在: {doc_path}"
                }
            
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "success": True,
                "content": content,
                "metadata": self._extract_metadata(content),
                "filepath": str(full_path)
            }
            
        except Exception as e:
            logger.error(f"获取文档失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_documents(self, doc_type: Optional[str] = None) -> Dict[str, Any]:
        """列出所有文档"""
        try:
            documents = []
            
            if doc_type:
                # 列出特定类型的文档
                type_dir = self.base_dir / doc_type
                if type_dir.exists():
                    for file in type_dir.glob("*.md"):
                        documents.append({
                            "name": file.name,
                            "path": str(file.relative_to(self.base_dir)),
                            "type": doc_type,
                            "modified": file.stat().st_mtime
                        })
            else:
                # 列出所有文档
                for dir_name in ["daily_progress", "weekly_report", "technical_review", "test_report"]:
                    dir_path = self.base_dir / dir_name
                    if dir_path.exists():
                        for file in dir_path.glob("*.md"):
                            documents.append({
                                "name": file.name,
                                "path": str(file.relative_to(self.base_dir)),
                                "type": dir_name,
                                "modified": file.stat().st_mtime
                            })
            
            # 按修改时间排序
            documents.sort(key=lambda x: x["modified"], reverse=True)
            
            return {
                "success": True,
                "documents": documents,
                "count": len(documents)
            }
            
        except Exception as e:
            logger.error(f"列出文档失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _build_document_content(self, title: str, content: str, author: str, doc_type: str) -> str:
        """构建文档内容"""
        now = datetime.now()
        template = Template("""# {{ title }}

## 元数据
- 创建时间: {{ create_time }}
- 最后更新: {{ create_time }}
- 当前模型: {{ author }}
- 文档版本: v1.0.0
- 文档类型: {{ doc_type }}

## 内容
{{ content }}

## 变更记录
- [{{ create_time }}] @{{ author }}: 创建文档

---
*本文档由Trae AI协作系统自动生成*""")
        
        return template.render(
            title=title,
            create_time=now.strftime("%Y-%m-%d %H:%M:%S"),
            author=author,
            content=content,
            doc_type=doc_type
        )
    
    def _update_document_content(self, existing_content: str, new_content: str, 
                              signature: str, author: str) -> str:
        """更新文档内容"""
        lines = existing_content.split('\n')
        updated_lines = []
        in_metadata = False
        in_content = False
        
        for line in lines:
            if line.startswith("## 元数据"):
                in_metadata = True
                updated_lines.append(line)
            elif line.startswith("## 变更记录"):
                # 添加新的变更记录
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                updated_lines.append(line)
                updated_lines.append(f"- [{now}] @{author}: {signature}")
                in_metadata = False
            elif in_metadata and line.startswith("- 最后更新:"):
                # 更新最后更新时间
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                updated_lines.append(f"- 最后更新: {now}")
            elif line.startswith("## 内容"):
                # 替换内容部分
                updated_lines.append(line)
                updated_lines.append(new_content)
                # 跳过旧的内容行
                in_content = True
                continue
            elif in_content and line.startswith("## "):
                # 遇到下一个标题，结束内容部分
                in_content = False
                updated_lines.append(line)
            elif not in_content:
                updated_lines.append(line)
        
        return '\n'.join(updated_lines)
    
    def _extract_metadata(self, content: str) -> Dict[str, str]:
        """提取文档元数据"""
        metadata = {}
        lines = content.split('\n')
        
        for line in lines:
            if line.startswith("- 创建时间:"):
                metadata["create_time"] = line.split(": ", 1)[1]
            elif line.startswith("- 最后更新:"):
                metadata["last_update"] = line.split(": ", 1)[1]
            elif line.startswith("- 当前模型:"):
                metadata["current_model"] = line.split(": ", 1)[1]
            elif line.startswith("- 文档版本:"):
                metadata["version"] = line.split(": ", 1)[1]
            elif line.startswith("- 文档类型:"):
                metadata["doc_type"] = line.split(": ", 1)[1]
        
        return metadata
    
    def _extract_doc_type(self, doc_path: str) -> str:
        """从文档路径提取文档类型"""
        parts = doc_path.split('/')
        if len(parts) >= 2:
            return parts[0]
        return "unknown"
    
    def _increment_version(self, existing_content: str) -> str:
        """递增版本号"""
        metadata = self._extract_metadata(existing_content)
        current_version = metadata.get("version", "v1.0.0")
        
        # 解析版本号
        try:
            version_parts = current_version.replace("v", "").split(".")
            major, minor, patch = int(version_parts[0]), int(version_parts[1]), int(version_parts[2])
            patch += 1
            return f"v{major}.{minor}.{patch}"
        except:
            return "v1.0.1"
    
    def _calculate_hash(self, content: str) -> str:
        """计算内容哈希"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()