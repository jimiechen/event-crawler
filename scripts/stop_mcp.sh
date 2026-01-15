#!/bin/bash
# MCP系统停止脚本
# 用于停止DeepSeek + Trae AI模型协作系统

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="/Users/mac/StudioProjects/open-citycloud/projects/event-crawler"
BACKEND_DIR="$PROJECT_ROOT/apps/stock-monitor-backend"

echo -e "${YELLOW}停止MCP系统...${NC}"
echo ""

# 停止MCP API服务
if [ -f "$BACKEND_DIR/.mcp_api.pid" ]; then
    API_PID=$(cat "$BACKEND_DIR/.mcp_api.pid")
    if kill -0 $API_PID 2>/dev/null; then
        echo -e "${GREEN}停止MCP API服务 (PID: $API_PID)${NC}"
        kill $API_PID
        rm "$BACKEND_DIR/.mcp_api.pid"
    else
        echo -e "${YELLOW}MCP API服务未运行${NC}"
        rm "$BACKEND_DIR/.mcp_api.pid"
    fi
else
    echo -e "${YELLOW}未找到MCP API服务PID文件${NC}"
fi

# 停止DeepSeek MCP工具
if [ -f "$BACKEND_DIR/.mcp_deepseek.pid" ]; then
    DEEPSEEK_PID=$(cat "$BACKEND_DIR/.mcp_deepseek.pid")
    if kill -0 $DEEPSEEK_PID 2>/dev/null; then
        echo -e "${GREEN}停止DeepSeek MCP工具 (PID: $DEEPSEEK_PID)${NC}"
        kill $DEEPSEEK_PID
        rm "$BACKEND_DIR/.mcp_deepseek.pid"
    else
        echo -e "${YELLOW}DeepSeek MCP工具未运行${NC}"
        rm "$BACKEND_DIR/.mcp_deepseek.pid"
    fi
else
    echo -e "${YELLOW}未找到DeepSeek MCP工具PID文件${NC}"
fi

# 停止协作文档MCP工具
if [ -f "$BACKEND_DIR/.mcp_collaboration.pid" ]; then
    COLLABORATION_PID=$(cat "$BACKEND_DIR/.mcp_collaboration.pid")
    if kill -0 $COLLABORATION_PID 2>/dev/null; then
        echo -e "${GREEN}停止协作文档MCP工具 (PID: $COLLABORATION_PID)${NC}"
        kill $COLLABORATION_PID
        rm "$BACKEND_DIR/.mcp_collaboration.pid"
    else
        echo -e "${YELLOW}协作文档MCP工具未运行${NC}"
        rm "$BACKEND_DIR/.mcp_collaboration.pid"
    fi
else
    echo -e "${YELLOW}未找到协作文档MCP工具PID文件${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  所有服务已停止！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""