#!/bin/bash
# MCP系统启动脚本
# 用于启动DeepSeek + Trae AI模型协作系统

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="/Users/mac/StudioProjects/open-citycloud/projects/event-crawler"
BACKEND_DIR="$PROJECT_ROOT/apps/stock-monitor-backend"
MCP_TOOLS_DIR="$PROJECT_ROOT/mcp-tools"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  MCP系统启动脚本${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 检查虚拟环境
if [ ! -d "$BACKEND_DIR/venv" ]; then
    echo -e "${RED}错误: 虚拟环境不存在，请先运行安装脚本${NC}"
    exit 1
fi

# 激活虚拟环境
echo -e "${YELLOW}激活虚拟环境...${NC}"
source "$BACKEND_DIR/venv/bin/activate"

# 检查配置文件
if [ ! -f "$BACKEND_DIR/.env" ]; then
    echo -e "${RED}错误: .env配置文件不存在${NC}"
    exit 1
fi

# 检查MCP配置文件
if [ ! -f "$PROJECT_ROOT/.trae/mcp-config.json" ]; then
    echo -e "${RED}错误: MCP配置文件不存在${NC}"
    exit 1
fi

# 启动MCP API服务
echo -e "${YELLOW}启动MCP API服务...${NC}"
cd "$BACKEND_DIR"
python3 main_mcp.py &
API_PID=$!
echo -e "${GREEN}✓ MCP API服务已启动 (PID: $API_PID)${NC}"

# 等待API服务启动
sleep 5

# 检查API服务是否启动成功
if ! kill -0 $API_PID 2>/dev/null; then
    echo -e "${RED}错误: MCP API服务启动失败${NC}"
    exit 1
fi

# 启动DeepSeek MCP工具
echo -e "${YELLOW}启动DeepSeek MCP工具...${NC}"
cd "$MCP_TOOLS_DIR/deepseek-mcp"
if [ -f "dist/mcp-server.js" ]; then
    node dist/mcp-server.js &
    DEEPSEEK_PID=$!
    echo -e "${GREEN}✓ DeepSeek MCP工具已启动 (PID: $DEEPSEEK_PID)${NC}"
else
    echo -e "${RED}错误: DeepSeek MCP工具未编译${NC}"
    exit 1
fi

# 启动协作文档MCP工具
echo -e "${YELLOW}启动协作文档MCP工具...${NC}"
cd "$MCP_TOOLS_DIR/collaboration-tools"
if [ -f "dist/mcp-server.js" ]; then
    node dist/mcp-server.js &
    COLLABORATION_PID=$!
    echo -e "${GREEN}✓ 协作文档MCP工具已启动 (PID: $COLLABORATION_PID)${NC}"
else
    echo -e "${RED}错误: 协作文档MCP工具未编译${NC}"
    exit 1
fi

# 保存PID
echo "$API_PID" > "$BACKEND_DIR/.mcp_api.pid"
echo "$DEEPSEEK_PID" > "$BACKEND_DIR/.mcp_deepseek.pid"
echo "$COLLABORATION_PID" > "$BACKEND_DIR/.mcp_collaboration.pid"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  所有服务已启动！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}服务信息：${NC}"
echo "MCP API服务: http://localhost:8000"
echo "DeepSeek MCP工具: stdio://deepseek-mcp"
echo "协作文档MCP工具: stdio://collaboration-tools"
echo ""
echo -e "${YELLOW}PID文件：${NC}"
echo "API服务: $BACKEND_DIR/.mcp_api.pid"
echo "DeepSeek: $BACKEND_DIR/.mcp_deepseek.pid"
echo "协作文档: $BACKEND_DIR/.mcp_collaboration.pid"
echo ""
echo -e "${YELLOW}停止服务：${NC}"
echo "bash $PROJECT_ROOT/scripts/stop_mcp.sh"
echo ""
echo -e "${YELLOW}查看日志：${NC}"
echo "API服务: tail -f $BACKEND_DIR/mcp_collaboration.log"
echo ""

# 等待用户输入
echo -e "${YELLOW}按Ctrl+C停止所有服务${NC}"
wait