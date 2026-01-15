#!/bin/bash
# MCP系统安装脚本
# 用于自动安装DeepSeek + Trae AI模型协作系统

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
echo -e "${GREEN}  MCP系统安装脚本${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 检查Python版本
echo -e "${YELLOW}检查Python版本...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到Python3${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo -e "${GREEN}✓ Python版本: $PYTHON_VERSION${NC}"

# 检查Node.js版本
echo -e "${YELLOW}检查Node.js版本...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}错误: 未找到Node.js${NC}"
    exit 1
fi

NODE_VERSION=$(node --version)
echo -e "${GREEN}✓ Node.js版本: $NODE_VERSION${NC}"

# 进入后端目录
cd "$BACKEND_DIR" || exit 1

# 创建虚拟环境
echo -e "${YELLOW}创建Python虚拟环境...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ 虚拟环境创建成功${NC}"
else
    echo -e "${YELLOW}虚拟环境已存在${NC}"
fi

# 激活虚拟环境
echo -e "${YELLOW}激活虚拟环境...${NC}"
source venv/bin/activate

# 升级pip
echo -e "${YELLOW}升级pip...${NC}"
pip install --upgrade pip

# 安装Python依赖
echo -e "${YELLOW}安装Python依赖...${NC}"
pip install -r requirements.txt

# 安装Playwright浏览器
echo -e "${YELLOW}安装Playwright浏览器...${NC}"
playwright install chromium

# 配置环境变量
echo -e "${YELLOW}配置环境变量...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.mcp.example" ]; then
        cp .env.mcp.example .env
        echo -e "${GREEN}✓ 已创建.env配置文件${NC}"
        echo -e "${YELLOW}请编辑.env文件，填入DeepSeek登录信息${NC}"
    else
        echo -e "${RED}错误: 未找到.env.mcp.example文件${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}.env文件已存在${NC}"
fi

# 创建协作文档目录
echo -e "${YELLOW}创建协作文档目录...${NC}"
mkdir -p collaboration_docs/{daily_progress,weekly_report,technical_review,test_report,archive}
echo -e "${GREEN}✓ 协作文档目录创建成功${NC}"

# 初始化数据库
echo -e "${YELLOW}初始化数据库...${NC}"
python3 -c "
from app.database import engine
from app.models.collaboration_log import Base
import asyncio

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('数据库初始化完成')

asyncio.run(init_db())
"
echo -e "${GREEN}✓ 数据库初始化完成${NC}"

# 安装TypeScript MCP工具
echo -e "${YELLOW}安装TypeScript MCP工具...${NC}"

# 安装DeepSeek MCP工具
if [ -d "$MCP_TOOLS_DIR/deepseek-mcp" ]; then
    cd "$MCP_TOOLS_DIR/deepseek-mcp"
    if [ -f "package.json" ]; then
        npm install
        echo -e "${GREEN}✓ DeepSeek MCP工具安装成功${NC}"
    fi
fi

# 安装协作文档MCP工具
if [ -d "$MCP_TOOLS_DIR/collaboration-tools" ]; then
    cd "$MCP_TOOLS_DIR/collaboration-tools"
    if [ -f "package.json" ]; then
        npm install
        echo -e "${GREEN}✓ 协作文档MCP工具安装成功${NC}"
    fi
fi

# 编译TypeScript代码
echo -e "${YELLOW}编译TypeScript代码...${NC}"
cd "$MCP_TOOLS_DIR/deepseek-mcp"
npm run build
cd "$MCP_TOOLS_DIR/collaboration-tools"
npm run build
echo -e "${GREEN}✓ TypeScript代码编译完成${NC}"

# 返回项目根目录
cd "$PROJECT_ROOT"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  安装完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}下一步操作：${NC}"
echo "1. 编辑配置文件: $BACKEND_DIR/.env"
echo "2. 启动MCP API服务: cd $BACKEND_DIR && python3 main_mcp.py"
echo "3. 启动MCP工具服务器:"
echo "   - DeepSeek: cd $MCP_TOOLS_DIR/deepseek-mcp && npm run start"
echo "   - 协作文档: cd $MCP_TOOLS_DIR/collaboration-tools && npm run start"
echo ""
echo -e "${YELLOW}配置说明文档: $BACKEND_DIR/MCP_CONFIG_GUIDE.md${NC}"
echo -e "${YELLOW}快速开始指南: $BACKEND_DIR/MCP_QUICKSTART.md${NC}"
echo ""