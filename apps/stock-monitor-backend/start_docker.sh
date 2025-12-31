#!/bin/bash

# Docker服务启动脚本
# 用于一键启动股票监控系统的所有Docker服务

set -e

echo "🚀 启动股票监控系统Docker服务..."
echo "=================================="

# 检查Docker是否运行
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker Desktop"
    exit 1
fi

# 检查docker-compose是否可用
if ! command -v docker-compose >/dev/null 2>&1; then
    echo "❌ docker-compose未安装"
    exit 1
fi

# 进入项目目录
cd "$(dirname "$0")"

echo "📁 当前目录: $(pwd)"

# 停止现有服务（如果有）
echo "🛑 停止现有服务..."
docker-compose down 2>/dev/null || true

# 启动所有服务
echo "🔄 启动Docker服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 30

# 检查服务状态
echo "📊 检查服务状态..."
docker-compose ps

echo ""
echo "🔍 验证服务连接..."

# 检查MySQL
echo -n "MySQL: "
if docker exec stock_monitor_mysql mysql -u stock_user -pstock123456 -e "SELECT 1" >/dev/null 2>&1; then
    echo "✅ 连接正常"
else
    echo "❌ 连接失败"
fi

# 检查Redis
echo -n "Redis: "
if docker exec stock_monitor_redis redis-cli ping >/dev/null 2>&1; then
    echo "✅ 连接正常"
else
    echo "❌ 连接失败"
fi

echo ""
echo "🌐 服务访问地址:"
echo "  - API文档:        http://localhost:8000/docs"
echo "  - phpMyAdmin:     http://localhost:8080"
echo "  - Redis Commander: http://localhost:8081"
echo "  - 健康检查:       http://localhost:8000/api/v1/health"

echo ""
echo "📝 数据库连接信息:"
echo "  - 主机: localhost"
echo "  - 端口: 3306"
echo "  - 数据库: stock_monitor"
echo "  - 用户名: stock_user"
echo "  - 密码: stock123456"

echo ""
echo "🎉 Docker服务启动完成！"
echo "=================================="