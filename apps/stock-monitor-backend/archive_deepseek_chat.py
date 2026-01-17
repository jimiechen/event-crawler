import requests
import json
import sys
import os

# 配置
BASE_URL = "http://localhost:8000/mcp"
CHAT_ID = "a41b487d-dd57-43d9-b41b-914ec6af3b2f"
DOC_TITLE = "主流题材研判技术架构设计"
DOC_TYPE = "technical_review"
AUTHOR = "DeepSeek_Archiver"

def archive_chat():
    print(f"=== 开始归档 DeepSeek 会话: {CHAT_ID} ===")
    
    # 1. 读取 DeepSeek 会话内容
    print(f"\n[步骤 1] 正在通过 MCP 读取 DeepSeek 会话...")
    chat_url = f"{BASE_URL}/deepseek/chats/{CHAT_ID}"
    try:
        response = requests.get(chat_url)
        response.raise_for_status()
        chat_data = response.json()
        
        content = chat_data.get("content", "")
        if not content:
            print("错误: 读取到的会话内容为空")
            return
            
        print(f"成功读取会话内容，长度: {len(content)} 字符")
        # 简单预览前100字符
        print(f"内容预览: {content[:100]}...")
        
    except Exception as e:
        print(f"读取 DeepSeek 会话失败: {e}")
        return

    # 2. 调用协作服务创建文档
    print(f"\n[步骤 2] 正在通过 MCP 协作服务创建本地文档...")
    
    # 构建文档内容，增加一些上下文头部
    formatted_content = f"""# {DOC_TITLE}

> 来源会话: [DeepSeek Chat](https://chat.deepseek.com/a/chat/s/{CHAT_ID})
> 归档时间: {os.popen('date').read().strip()}

{content}
"""

    create_payload = {
        "doc_type": DOC_TYPE,
        "title": DOC_TITLE,
        "content": formatted_content,
        "author": AUTHOR
    }
    
    try:
        create_url = f"{BASE_URL}/collaboration/doc/create"
        response = requests.post(create_url, json=create_payload)
        response.raise_for_status()
        result = response.json()
        
        if result.get("success"):
            print("\n✅ 文档归档成功!")
            print(f"文件路径: {result.get('filepath')}")
            print(f"文件名: {result.get('filename')}")
            print(f"消息: {result.get('message')}")
            
            # 3. 验证文件内容
            print(f"\n[步骤 3] 验证本地文件...")
            file_path = result.get('filepath')
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    saved_content = f.read()
                    print(f"文件大小: {len(saved_content)} 字节")
                    print("文件元数据部分:")
                    # 打印前10行查看元数据
                    for i, line in enumerate(saved_content.split('\n')[:10]):
                        print(f"{i+1}: {line}")
            else:
                print(f"警告: 无法在本地找到文件 {file_path}")
                
        else:
            print(f"文档创建失败: {result}")
            
    except Exception as e:
        print(f"创建文档失败: {e}")

if __name__ == "__main__":
    archive_chat()
