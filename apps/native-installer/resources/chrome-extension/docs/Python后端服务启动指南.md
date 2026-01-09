# Python后端服务启动指南

## 概述

本指南详细说明如何启动和配置Python后端服务，包括股票监控后端服务和相关的调试工具。

## 服务架构

项目包含以下Python服务：

1. **股票监控后端服务** (`/Users/mac/ok-mcp/app/stock-monitor-backend/`)
2. **Python控制台工具** (`/Users/mac/ok-mcp/app/python-console/`)
3. **浏览器管理脚本** (用于Chrome浏览器管理)

## 1. 股票监控后端服务

### 1.1 环境准备

#### 系统要求
- Python 3.9+
- MySQL 8.0+
- Redis (可选)

#### 依赖安装
```bash
cd /Users/mac/ok-mcp/app/stock-monitor-backend

# 安装Python依赖
pip install -r requirements.txt
```

#### 核心依赖包
```
# FastAPI和相关依赖
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# 数据库相关
sqlalchemy==2.0.23
asyncpg==0.29.0
alembic==1.13.1

# Redis（可选）
redis==5.0.1
aioredis==2.0.1

# 日志
loguru==0.7.2

# 工具库
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0
```

### 1.2 数据库配置

#### 创建数据库
```sql
CREATE DATABASE stock_monitor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'stock_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON stock_monitor.* TO 'stock_user'@'localhost';
FLUSH PRIVILEGES;
```

#### 环境变量配置
创建 `.env` 文件：
```bash
# 应用配置
APP_NAME=Stock Monitor Backend
APP_VERSION=1.0.0
APP_DEBUG=true
ENVIRONMENT=development

# 服务器配置
HOST=0.0.0.0
PORT=8000
WORKERS=1

# 数据库配置
DATABASE_URL=mysql+aiomysql://stock_user:your_password@localhost:3306/stock_monitor
DB_HOST=localhost
DB_PORT=3306
DB_USER=stock_user
DB_PASSWORD=your_password
DB_DATABASE=stock_monitor
DB_CHARSET=utf8mb4
DB_ECHO=false

# 数据库连接池配置
DB_MIN_SIZE=2
DB_MAX_SIZE=10

# 日志配置
LOG_LEVEL=INFO
LOG_FORMAT=json

# CORS配置
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000", "chrome-extension://*"]
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
CORS_ALLOW_HEADERS=["*"]

# API配置
API_V1_PREFIX=/api/v1
DOCS_URL=/docs
REDOC_URL=/redoc
OPENAPI_URL=/openapi.json

# 监控配置
ALERT_THRESHOLD_PERCENTAGE=5.0
ALERT_CHECK_INTERVAL_MINUTES=5

# 去重配置
DEDUP_ENABLED=true
DEDUP_WINDOW_MINUTES=1

# 性能配置
BATCH_SIZE=1000
QUERY_TIMEOUT_SECONDS=30
```

### 1.3 启动服务

#### 开发环境启动
```bash
cd /Users/mac/ok-mcp/app/stock-monitor-backend

# 方式1：使用启动脚本
python run.py --mode dev

# 方式2：直接使用uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level info

# 方式3：使用Python模块启动
python -m app.main
```

#### 生产环境启动
```bash
# 使用Gunicorn启动
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# 或使用启动脚本
python run.py --mode prod --workers 4
```

### 1.4 服务验证

#### 健康检查
```bash
# 检查服务状态
curl http://localhost:8000/health

# 检查API文档
curl http://localhost:8000/docs

# 检查API版本
curl http://localhost:8000/api/v1/
```

#### 预期响应
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0",
  "database": "connected",
  "uptime": "00:05:30"
}
```

### 1.5 日志配置

#### 日志级别
- `DEBUG`: 详细调试信息
- `INFO`: 一般信息（推荐）
- `WARNING`: 警告信息
- `ERROR`: 错误信息
- `CRITICAL`: 严重错误

#### 日志输出
```bash
# 实时查看日志
tail -f logs/app.log

# 查看错误日志
tail -f logs/error.log

# 查看访问日志
tail -f logs/access.log
```

## 2. Python控制台工具

### 2.1 浏览器管理脚本

#### 启动浏览器管理器
```bash
cd /Users/mac/ok-mcp/app/python-console

# 启动浏览器管理器
python start_browser.py
```

#### 检查浏览器状态
```bash
# 检查状态
python check_browser_status.py

# 实时监控
watch -n 2 'python check_browser_status.py'
```

#### 停止浏览器管理器
```bash
# 优雅停止
python stop_browser.py
```

### 2.2 MCP客户端工具

#### 使用改进版MCP客户端
```bash
# 启动MCP客户端
python improved_mcp_client.py

# 使用最终修复版本
python final_mcp_client.py
```

## 3. 服务集成测试

### 3.1 完整启动流程

```bash
# 1. 启动数据库服务
sudo systemctl start mysql

# 2. 启动Redis（可选）
sudo systemctl start redis

# 3. 启动股票监控后端
cd /Users/mac/ok-mcp/app/stock-monitor-backend
python run.py --mode dev

# 4. 启动浏览器管理器
cd /Users/mac/ok-mcp/app/python-console
python start_browser.py

# 5. 验证所有服务
python check_browser_status.py
curl http://localhost:8000/health
```

### 3.2 服务状态检查

#### 端口占用检查
```bash
# 检查关键端口
netstat -tlnp | grep -E ':(8000|3306|6379|9222)'

# 或使用lsof
lsof -i :8000  # 后端服务
lsof -i :3306  # MySQL
lsof -i :6379  # Redis
lsof -i :9222  # Chrome调试端口
```

#### 进程状态检查
```bash
# 检查Python进程
ps aux | grep python

# 检查Chrome进程
ps aux | grep chrome

# 检查数据库进程
ps aux | grep mysql
```

## 4. 故障排除

### 4.1 常见问题

#### 数据库连接失败
```bash
# 检查MySQL服务状态
sudo systemctl status mysql

# 检查数据库连接
mysql -u stock_user -p -h localhost stock_monitor

# 检查防火墙设置
sudo ufw status
```

#### 端口被占用
```bash
# 查找占用端口的进程
lsof -i :8000

# 杀死占用进程
kill -9 <PID>

# 或使用fuser
fuser -k 8000/tcp
```

#### Chrome调试端口问题
```bash
# 检查Chrome调试端口
curl http://localhost:9222/json

# 重启Chrome调试模式
pkill -f "chrome.*remote-debugging-port"
google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug
```

### 4.2 日志分析

#### 后端服务日志
```bash
# 查看启动日志
tail -f /Users/mac/ok-mcp/app/stock-monitor-backend/logs/app.log

# 查看错误日志
grep ERROR /Users/mac/ok-mcp/app/stock-monitor-backend/logs/app.log

# 查看数据库连接日志
grep "database" /Users/mac/ok-mcp/app/stock-monitor-backend/logs/app.log
```

#### 浏览器管理器日志
```bash
# 查看浏览器管理器日志
tail -f /tmp/browser_manager.log

# 查看Chrome进程日志
tail -f /tmp/chrome_debug.log
```

## 5. 性能优化

### 5.1 数据库优化

#### 连接池配置
```python
# 在.env文件中调整
DB_MIN_SIZE=5
DB_MAX_SIZE=20
```

#### 索引优化
```sql
-- 为常用查询添加索引
CREATE INDEX idx_stock_code ON stock_info(stock_code);
CREATE INDEX idx_timestamp ON stock_data(timestamp);
CREATE INDEX idx_stock_data_code_time ON stock_data(stock_code, timestamp);
```

### 5.2 应用优化

#### 缓存配置
```python
# 启用Redis缓存
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=300  # 5分钟
```

#### 批处理优化
```python
# 调整批处理大小
BATCH_SIZE=2000
QUERY_TIMEOUT_SECONDS=60
```

## 6. 监控和维护

### 6.1 健康检查脚本

创建 `health_check.sh`：
```bash
#!/bin/bash

echo "=== 服务健康检查 ==="

# 检查后端服务
echo "检查后端服务..."
curl -s http://localhost:8000/health | jq .

# 检查数据库
echo "检查数据库连接..."
mysql -u stock_user -p -e "SELECT 1" stock_monitor

# 检查Chrome调试端口
echo "检查Chrome调试端口..."
curl -s http://localhost:9222/json | jq length

echo "=== 检查完成 ==="
```

### 6.2 自动重启脚本

创建 `auto_restart.sh`：
```bash
#!/bin/bash

# 检查服务是否运行
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "后端服务异常，正在重启..."
    cd /Users/mac/ok-mcp/app/stock-monitor-backend
    python run.py --mode dev &
fi

# 检查浏览器管理器
if ! pgrep -f "start_browser.py" > /dev/null; then
    echo "浏览器管理器异常，正在重启..."
    cd /Users/mac/ok-mcp/app/python-console
    python start_browser.py &
fi
```

## 7. 安全配置

### 7.1 生产环境安全

#### 环境变量安全
```bash
# 设置文件权限
chmod 600 .env

# 使用系统环境变量
export DATABASE_URL="mysql+aiomysql://..."
export SECRET_KEY="your-secret-key"
```

#### 网络安全
```bash
# 配置防火墙
sudo ufw allow 8000/tcp
sudo ufw allow from 127.0.0.1 to any port 3306
```

### 7.2 数据备份

#### 数据库备份
```bash
# 创建备份脚本
mysqldump -u stock_user -p stock_monitor > backup_$(date +%Y%m%d_%H%M%S).sql

# 定时备份（添加到crontab）
0 2 * * * /path/to/backup_script.sh
```

## 8. 总结

通过本指南，您应该能够：

1. ✅ 成功启动股票监控后端服务
2. ✅ 配置和管理浏览器调试环境
3. ✅ 使用Python控制台工具进行调试
4. ✅ 监控服务状态和性能
5. ✅ 处理常见问题和故障

如果遇到问题，请参考故障排除部分或查看相关日志文件。