# 同花顺股票监控系统部署指南

## 概述

本文档详细介绍了同花顺股票监控系统的部署流程，包括环境准备、依赖安装、配置设置和服务启动等步骤。

## 系统要求

### 硬件要求

- **CPU**: 2核心以上
- **内存**: 4GB以上
- **存储**: 20GB以上可用空间
- **网络**: 稳定的互联网连接

### 软件要求

- **操作系统**: Linux (Ubuntu 20.04+), macOS (10.15+), Windows 10+
- **Python**: 3.9+
- **数据库**: MySQL 8.0+ 或 PostgreSQL 13+
- **Git**: 用于代码管理

## 环境准备

### 1. 安装Python

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install python3.9 python3.9-pip python3.9-venv
```

#### macOS
```bash
# 使用Homebrew
brew install python@3.9

# 或使用pyenv
brew install pyenv
pyenv install 3.9.18
pyenv global 3.9.18
```

#### Windows
从 [Python官网](https://www.python.org/downloads/) 下载并安装Python 3.9+

### 2. 安装数据库

#### MySQL (推荐)

**Ubuntu/Debian:**
```bash
sudo apt install mysql-server mysql-client
sudo mysql_secure_installation
```

**macOS:**
```bash
brew install mysql
brew services start mysql
```

**Windows:**
从 [MySQL官网](https://dev.mysql.com/downloads/mysql/) 下载并安装

#### PostgreSQL (可选)

**Ubuntu/Debian:**
```bash
sudo apt install postgresql postgresql-contrib
```

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

### 3. 创建数据库

#### MySQL
```sql
-- 登录MySQL
mysql -u root -p

-- 创建数据库
CREATE DATABASE stock_monitor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建用户
CREATE USER 'stock_user'@'localhost' IDENTIFIED BY 'your_password';

-- 授权
GRANT ALL PRIVILEGES ON stock_monitor.* TO 'stock_user'@'localhost';
FLUSH PRIVILEGES;

-- 退出
EXIT;
```

#### PostgreSQL
```sql
-- 登录PostgreSQL
sudo -u postgres psql

-- 创建数据库
CREATE DATABASE stock_monitor;

-- 创建用户
CREATE USER stock_user WITH PASSWORD 'your_password';

-- 授权
GRANT ALL PRIVILEGES ON DATABASE stock_monitor TO stock_user;

-- 退出
\q
```

## 项目部署

### 1. 获取代码

```bash
# 克隆项目
git clone <repository_url>
cd stock-monitor-backend

# 或者直接下载项目文件
```

### 2. 创建虚拟环境

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. 安装依赖

```bash
# 升级pip
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt
```

### 4. 环境配置

#### 创建环境配置文件

```bash
# 复制环境配置模板
cp .env.example .env

# 编辑配置文件
nano .env  # 或使用其他编辑器
```

#### 配置文件说明 (.env)

```bash
# 应用配置
APP_NAME=同花顺股票监控系统
APP_VERSION=1.0.0
APP_ENV=production  # development, testing, production
DEBUG=false

# 服务器配置
HOST=0.0.0.0
PORT=8001
WORKERS=4

# 数据库配置 (MySQL)
DATABASE_URL=mysql+aiomysql://stock_user:your_password@localhost:3306/stock_monitor

# 或者 PostgreSQL
# DATABASE_URL=postgresql+asyncpg://stock_user:your_password@localhost:5432/stock_monitor

# 数据库连接池配置
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
LOG_MAX_SIZE=10MB
LOG_BACKUP_COUNT=5

# CORS配置
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
CORS_ALLOW_HEADERS=["*"]

# 安全配置
SECRET_KEY=your_secret_key_here
TRUSTED_HOSTS=["localhost", "127.0.0.1", "your-domain.com"]

# API文档配置 (生产环境建议关闭)
DOCS_URL=/docs
REDOC_URL=/redoc
OPENAPI_URL=/openapi.json
```

### 5. 数据库初始化

```bash
# 创建数据库表
python -c "
import asyncio
from app.database import DatabaseManager

async def init_db():
    db_manager = DatabaseManager()
    await db_manager.initialize()
    print('数据库初始化完成')

asyncio.run(init_db())
"

# 或者直接执行SQL文件
mysql -u stock_user -p stock_monitor < sql/create_tables.sql
```

### 6. 验证配置

```bash
# 测试数据库连接
python -c "
import asyncio
from app.database import DatabaseManager

async def test_db():
    db_manager = DatabaseManager()
    if await db_manager.health_check():
        print('✅ 数据库连接正常')
    else:
        print('❌ 数据库连接失败')

asyncio.run(test_db())
"

# 测试应用启动
python -c "
from app.main import app
print('✅ 应用配置正常')
"
```

## 服务启动

### 1. 开发环境启动

```bash
# 直接启动 (开发模式)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# 或使用Python模块方式
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# 使用项目提供的启动脚本 (推荐)
python run.py
```

### 2. 生产环境启动

#### 使用Gunicorn (推荐)

```bash
# 安装Gunicorn
pip install gunicorn

# 启动服务
gunicorn app.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8001 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log \
  --log-level info \
  --daemon
```

#### 创建启动脚本

**start.sh:**
```bash
#!/bin/bash

# 激活虚拟环境
source venv/bin/activate

# 创建日志目录
mkdir -p logs

# 启动服务
gunicorn app.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log \
  --log-level info \
  --pid logs/gunicorn.pid \
  --daemon

echo "服务已启动，PID: $(cat logs/gunicorn.pid)"
```

**stop.sh:**
```bash
#!/bin/bash

if [ -f logs/gunicorn.pid ]; then
    kill $(cat logs/gunicorn.pid)
    rm logs/gunicorn.pid
    echo "服务已停止"
else
    echo "服务未运行"
fi
```

**restart.sh:**
```bash
#!/bin/bash

./stop.sh
sleep 2
./start.sh
```

### 3. 使用systemd (Linux)

#### 创建服务文件

**/etc/systemd/system/stock-monitor.service:**
```ini
[Unit]
Description=Stock Monitor API Service
After=network.target mysql.service

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/path/to/stock-monitor-backend
Environment=PATH=/path/to/stock-monitor-backend/venv/bin
ExecStart=/path/to/stock-monitor-backend/venv/bin/gunicorn \
  app.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile /path/to/stock-monitor-backend/logs/access.log \
  --error-logfile /path/to/stock-monitor-backend/logs/error.log \
  --log-level info \
  --pid /path/to/stock-monitor-backend/logs/gunicorn.pid \
  --daemon
ExecReload=/bin/kill -s HUP $MAINPID
ExecStop=/bin/kill -s TERM $MAINPID
PIDFile=/path/to/stock-monitor-backend/logs/gunicorn.pid
Restart=always

[Install]
WantedBy=multi-user.target
```

#### 启用和启动服务

```bash
# 重新加载systemd配置
sudo systemctl daemon-reload

# 启用服务
sudo systemctl enable stock-monitor

# 启动服务
sudo systemctl start stock-monitor

# 查看状态
sudo systemctl status stock-monitor

# 查看日志
sudo journalctl -u stock-monitor -f
```

## 功能验证

### 1. HTML查询页面

服务启动后，可以通过浏览器访问HTML查询页面：

**访问地址**: http://localhost:8001/

**功能特性**:
- **股票搜索**: 支持按股票代码或名称搜索
- **实时数据**: 显示最新的股票信息
- **分页显示**: 支持大量数据的分页浏览
- **响应式设计**: 适配不同屏幕尺寸
- **数据刷新**: 支持手动和自动刷新

**使用方法**:
1. 在搜索框中输入股票代码（如：000001）或股票名称（如：平安银行）
2. 点击"搜索"按钮或按回车键
3. 查看搜索结果，支持分页浏览
4. 点击"刷新数据"获取最新信息

### 2. API接口验证

**股票搜索接口**:
```bash
# 按股票代码搜索
curl "http://localhost:8001/api/v1/stocks/search?q=000001"

# 按股票名称搜索
curl "http://localhost:8001/api/v1/stocks/search?q=平安"

# 分页查询
curl "http://localhost:8001/api/v1/stocks/search?q=000&page=1&size=10"
```

**股票列表接口**:
```bash
# 获取所有股票列表
curl "http://localhost:8001/api/v1/stocks/"

# 分页获取
curl "http://localhost:8001/api/v1/stocks/?page=1&size=20"
```

**数据提交接口**:
```bash
# Chrome插件数据提交
curl -X POST "http://localhost:8001/api/v1/stocks/data/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "data_list": [
      {
        "stock_code": "000001",
        "stock_name": "平安银行",
        "current_price": "12.50",
        "change_percent": "+2.45%",
        "volume": "1000000",
        "market_cap": "2500亿"
      }
    ]
  }'
```

### 3. 端到端测试

运行完整的端到端测试验证所有功能：

```bash
# 运行端到端集成测试
python test_e2e_integration.py

# 预期输出：
# ✅ PASS 健康检查
# ✅ PASS 静态文件访问
# ✅ PASS Chrome插件数据提交
# ✅ PASS 股票信息创建
# ✅ PASS 股票搜索API
# ✅ PASS 股票列表API
# ✅ PASS 数据流完整性
# 成功率: 100.0%
```

## 反向代理配置

### Nginx配置

**/etc/nginx/sites-available/stock-monitor:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL证书配置
    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/key.pem;

    # SSL安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # 日志配置
    access_log /var/log/nginx/stock-monitor.access.log;
    error_log /var/log/nginx/stock-monitor.error.log;

    # 反向代理配置
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时配置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 静态文件缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
}
```

#### 启用Nginx配置

```bash
# 创建软链接
sudo ln -s /etc/nginx/sites-available/stock-monitor /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重新加载配置
sudo systemctl reload nginx
```

## 监控和维护

### 1. 健康检查

```bash
# 检查服务状态
curl http://localhost:8001/health

# 检查HTML查询页面
curl http://localhost:8001/

# 检查API接口
curl http://localhost:8001/api/v1/stocks/search?q=平安

# 检查静态文件服务
curl -I http://localhost:8001/static/

# 数据库健康检查
python -c "
import asyncio
from app.database import DatabaseManager
async def test(): 
    db = DatabaseManager()
    result = await db.health_check()
    print('✅ 数据库连接正常' if result else '❌ 数据库连接失败')
asyncio.run(test())
"
```

### 2. 日志监控

```bash
# 查看应用日志
tail -f logs/app.log

# 查看访问日志
tail -f logs/access.log

# 查看错误日志
tail -f logs/error.log

# 查看系统日志
sudo journalctl -u stock-monitor -f
```

### 3. 性能监控

```bash
# 查看进程状态
ps aux | grep gunicorn

# 查看端口占用
netstat -tlnp | grep :8000

# 查看系统资源
top
htop
```

### 4. 数据库维护

```bash
# 备份数据库
mysqldump -u stock_user -p stock_monitor > backup_$(date +%Y%m%d_%H%M%S).sql

# 恢复数据库
mysql -u stock_user -p stock_monitor < backup_20240115_120000.sql

# 查看数据库状态
mysql -u stock_user -p -e "SHOW PROCESSLIST;"
mysql -u stock_user -p -e "SHOW STATUS LIKE 'Threads%';"
```

## 故障排除

### 常见问题

#### 1. 服务无法启动

**检查步骤:**
```bash
# 检查端口占用
netstat -tlnp | grep :8000

# 检查配置文件
python -c "from app.config.settings import get_settings; print(get_settings())"

# 检查数据库连接
python -c "
import asyncio
from app.database import DatabaseManager
async def test(): 
    db = DatabaseManager()
    print(await db.health_check())
asyncio.run(test())
"
```

#### 2. 数据库连接失败

**检查步骤:**
```bash
# 检查数据库服务状态
sudo systemctl status mysql

# 检查数据库连接
mysql -u stock_user -p -h localhost

# 检查防火墙
sudo ufw status
```

#### 3. 性能问题

**优化建议:**
- 增加worker进程数量
- 调整数据库连接池大小
- 启用数据库查询缓存
- 使用Redis缓存热点数据

### 日志分析

#### 常见错误模式

```bash
# 数据库连接错误
grep "database" logs/error.log

# 内存不足
grep "Memory" logs/error.log

# 超时错误
grep "timeout" logs/error.log

# 权限错误
grep "permission" logs/error.log
```

## 安全建议

### 1. 网络安全

- 使用HTTPS加密传输
- 配置防火墙规则
- 限制数据库访问IP
- 使用VPN或专网

### 2. 应用安全

- 定期更新依赖包
- 使用强密码
- 启用访问日志
- 配置速率限制

### 3. 数据安全

- 定期备份数据
- 加密敏感数据
- 设置数据保留策略
- 监控异常访问

## 扩展部署

### 1. 负载均衡

使用多个应用实例和负载均衡器:

```nginx
upstream stock_monitor_backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    location / {
        proxy_pass http://stock_monitor_backend;
    }
}
```

### 2. 容器化部署

**Dockerfile:**
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=mysql+aiomysql://stock_user:password@db:3306/stock_monitor
    depends_on:
      - db

  db:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=rootpassword
      - MYSQL_DATABASE=stock_monitor
      - MYSQL_USER=stock_user
      - MYSQL_PASSWORD=password
    volumes:
      - mysql_data:/var/lib/mysql

volumes:
  mysql_data:
```

## 联系支持

如果在部署过程中遇到问题，请：

1. 查看本文档的故障排除部分
2. 检查项目的GitHub Issues
3. 联系技术支持团队

---

**注意**: 请根据实际环境调整配置参数，确保系统安全和稳定运行。