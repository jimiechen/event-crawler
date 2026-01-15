#!/bin/bash
# MCP系统测试脚本
# 用于测试DeepSeek + Trae AI模型协作系统的功能

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="/Users/mac/StudioProjects/open-citycloud/projects/event-crawler"
BACKEND_DIR="$PROJECT_ROOT/apps/stock-monitor-backend"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  MCP系统测试脚本${NC}"
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

echo -e "${YELLOW}开始测试...${NC}"
echo ""

# 测试计数器
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 测试函数
run_test() {
    local test_name=$1
    local test_command=$2
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -e "${YELLOW}测试 $TOTAL_TESTS: $test_name${NC}"
    
    if eval "$test_command"; then
        echo -e "${GREEN}✓ 通过${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ 失败${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    echo ""
}

# ============================================================================
# 测试1: 检查Python依赖
# ============================================================================
run_test "检查Python依赖" "pip list | grep -E 'playwright|jinja2|markdown'"

# ============================================================================
# 测试2: 检查数据库模型
# ============================================================================
run_test "检查数据库模型" "python3 -c 'from app.models.collaboration_log import CollaborationLog, DocumentVersion, CollaborationSession; print(\"数据库模型导入成功\")'"

# ============================================================================
# 测试3: 检查MCP配置
# ============================================================================
run_test "检查MCP配置" "python3 -c 'from config.mcp_config import MCPConfig; MCPConfig.validate(); print(\"MCP配置验证通过\")'"

# ============================================================================
# 测试4: 检查协作文档目录
# ============================================================================
run_test "检查协作文档目录" "ls -la $BACKEND_DIR/collaboration_docs/"

# ============================================================================
# 测试5: 检查MCP工具文件
# ============================================================================
run_test "检查DeepSeek MCP工具" "ls -la $PROJECT_ROOT/mcp-tools/deepseek-mcp/"
run_test "检查协作文档MCP工具" "ls -la $PROJECT_ROOT/mcp-tools/collaboration-tools/"

# ============================================================================
# 测试6: 检查TypeScript编译
# ============================================================================
run_test "检查DeepSeek MCP工具编译" "test -f $PROJECT_ROOT/mcp-tools/deepseek-mcp/dist/mcp-server.js"
run_test "检查协作文档MCP工具编译" "test -f $PROJECT_ROOT/mcp-tools/collaboration-tools/dist/mcp-server.js"

# ============================================================================
# 测试7: 测试MCP API健康检查
# ============================================================================
echo -e "${YELLOW}测试MCP API健康检查...${NC}"
if curl -s http://localhost:8000/mcp/health > /dev/null 2>&1; then
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -e "${GREEN}✓ 通过: MCP API健康检查${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -e "${RED}✗ 失败: MCP API健康检查${NC}"
    echo -e "${YELLOW}提示: 请先启动MCP API服务${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo ""

# ============================================================================
# 测试8: 测试DeepSeek登录（需要配置）
# ============================================================================
echo -e "${YELLOW}测试DeepSeek登录...${NC}"
echo -e "${YELLOW}提示: 需要在.env中配置DeepSeek账号${NC}"

# 读取DeepSeek凭证
source "$BACKEND_DIR/.env"
if [ -n "$DEEPSEEK_EMAIL" ] && [ -n "$DEEPSEEK_PASSWORD" ]; then
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    LOGIN_RESULT=$(curl -s -X POST http://localhost:8000/mcp/deepseek/login \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$DEEPSEEK_EMAIL\",\"password\":\"$DEEPSEEK_PASSWORD\"}")
    
    if echo "$LOGIN_RESULT" | grep -q "success.*true"; then
        echo -e "${GREEN}✓ 通过: DeepSeek登录${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ 失败: DeepSeek登录${NC}"
        echo -e "${YELLOW}响应: $LOGIN_RESULT${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
else
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -e "${YELLOW}⚠ 跳过: DeepSeek登录（未配置凭证）${NC}"
fi
echo ""

# ============================================================================
# 测试9: 测试创建协作文档
# ============================================================================
echo -e "${YELLOW}测试创建协作文档...${NC}"
CREATE_DOC_RESULT=$(curl -s -X POST http://localhost:8000/mcp/collaboration/doc/create \
    -H "Content-Type: application/json" \
    -d '{
        "doc_type": "daily_progress",
        "title": "测试文档",
        "content": "这是一个测试文档",
        "author": "GLM4.7"
    }')

if echo "$CREATE_DOC_RESULT" | grep -q "success.*true"; then
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -e "${GREEN}✓ 通过: 创建协作文档${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    
    # 提取文档路径
    DOC_PATH=$(echo "$CREATE_DOC_RESULT" | grep -o '"filepath":"[^"]*"' | cut -d'"' -f4)
    echo -e "${YELLOW}文档路径: $DOC_PATH${NC}"
else
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -e "${RED}✗ 失败: 创建协作文档${NC}"
    echo -e "${YELLOW}响应: $CREATE_DOC_RESULT${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo ""

# ============================================================================
# 测试10: 测试列出协作文档
# ============================================================================
echo -e "${YELLOW}测试列出协作文档...${NC}"
LIST_DOCS_RESULT=$(curl -s http://localhost:8000/mcp/collaboration/docs)

if echo "$LIST_DOCS_RESULT" | grep -q "success.*true"; then
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -e "${GREEN}✓ 通过: 列出协作文档${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    
    # 显示文档数量
    DOC_COUNT=$(echo "$LIST_DOCS_RESULT" | grep -o '"count":[0-9]*' | cut -d':' -f2)
    echo -e "${YELLOW}文档数量: $DOC_COUNT${NC}"
else
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -e "${RED}✗ 失败: 列出协作文档${NC}"
    echo -e "${YELLOW}响应: $LIST_DOCS_RESULT${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo ""

# ============================================================================
# 测试总结
# ============================================================================
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  测试总结${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "总测试数: $TOTAL_TESTS"
echo -e "${GREEN}通过: $PASSED_TESTS${NC}"
echo -e "${RED}失败: $FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}所有测试通过！✓${NC}"
    exit 0
else
    echo -e "${RED}部分测试失败！✗${NC}"
    exit 1
fi