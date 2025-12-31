#!/bin/bash

# Docker服务健康检查脚本
# 用于检查股票监控系统所有服务的运行状态

echo "🔍 Docker服务健康检查"
echo "=================================="

# 检查Docker是否运行
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker未运行"
    exit 1
fi

# 进入项目目录
cd "$(dirname "$0")"

echo "📊 容器状态:"
docker-compose ps

echo ""
echo "🔗 服务连接测试:"

# 检查MySQL连接
echo -n "  MySQL (3306): "
if docker exec stock_monitor_mysql mysql -u stock_user -pstock123456 -e "SELECT 1" >/dev/null 2>&1; then
    echo "✅ 正常"
else
    echo "❌ 失败"
fi

# 检查Redis连接
echo -n "  Redis (6379): "
if docker exec stock_monitor_redis redis-cli ping >/dev/null 2>&1; then
    echo "✅ 正常"
else
    echo "❌ 失败"
fi

# 检查phpMyAdmin
echo -n "  phpMyAdmin (8080): "
if curl -s http://localhost:8080 >/dev/null 2>&1; then
    echo "✅ 正常"
else
    echo "❌ 失败"
fi

# 检查Redis Commander
echo -n "  Redis Commander (8081): "
if curl -s http://localhost:8081 >/dev/null 2>&1; then
    echo "✅ 正常"
else
    echo "❌ 失败"
fi

# 检查后端API
echo -n "  后端API (8000): "
if curl -s http://localhost:8000/api/v1/health >/dev/null 2>&1; then
    echo "✅ 正常"
else
    echo "❌ 失败"
fi

echo ""
echo "💾 数据卷状态:"
docker volume ls | grep stock-monitor-backend

echo ""
echo "🌐 网络状态:"
docker network ls | grep stock-monitor-backend

echo ""
echo "📈 资源使用:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep stock_monitor

echo ""
echo "=================================="
echo "✅ 健康检查完成"