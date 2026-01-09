# Event-Crawler 部署指南

## 1. 概述

本文档详细描述Event-Crawler项目的部署流程，包括Docker镜像构建、Docker Compose配置说明、生产环境部署步骤、数据库迁移流程、环境变量配置、回滚策略和监控日志。

**项目位置**: `/Users/mac/StudioProjects/open-citycloud/projects/event-crawler`  
**文档版本**: V1.0  
**最后更新**: 2026-01-08

---

## 2. Docker镜像构建

### 2.1 Stock Monitor Backend Dockerfile

**apps/stock-monitor-backend/Dockerfile**:
```dockerfile
# 使用官方Python镜像作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建非root用户
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 8000

# 启动应用
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2.2 Chrome Extension构建

**apps/chrome-extension/package.json**:
```json
{
  "scripts": {
    "build": "wxt build",
    "zip": "wxt zip"
  }
}
```

```bash
# 构建Chrome Extension
cd apps/chrome-extension
npm run build

# 打包Chrome Extension
npm run zip
```

### 2.3 构建Docker镜像

```bash
# 构建Stock Monitor Backend镜像
cd apps/stock-monitor-backend
docker build -t stock-monitor-backend:latest .

# 构建带版本标签的镜像
docker build -t stock-monitor-backend:v1.0.0 .

# 推送到Docker Hub
docker tag stock-monitor-backend:latest your-username/stock-monitor-backend:latest
docker push your-username/stock-monitor-backend:latest
```

---

## 3. Docker Compose配置

### 3.1 docker-compose.yml

**apps/stock-monitor-backend/docker-compose.yml**:
```yaml
version: '3.8'

services:
  app:
    build: .
    container_name: stock-monitor-backend
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    environment:
      - DATABASE_URL=mysql+aiomysql://stock_user:stock123456@db:3306/stock_monitor
      - REDIS_URL=redis://redis:6379/0
      - LOG_LEVEL=INFO
    volumes:
      - ./logs:/app/logs
    restart: always
    networks:
      - stock-monitor-network

  db:
    image: mysql:8.0.35
    container_name: stock-monitor-mysql
    environment:
      MYSQL_DATABASE: stock_monitor
      MYSQL_USER: stock_user
      MYSQL_PASSWORD: stock123456
      MYSQL_ROOT_PASSWORD: root123456
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./docker/mysql/conf:/etc/mysql/conf.d
      - ./docker/mysql/init:/docker-entrypoint-initdb.d
    restart: always
    networks:
      - stock-monitor-network

  redis:
    image: redis:7-alpine
    container_name: stock-monitor-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: always
    networks:
      - stock-monitor-network

  phpmyadmin:
    image: phpmyadmin/phpmyadmin:latest
    container_name: stock-monitor-phpmyadmin
    ports:
      - "8080:80"
    environment:
      PMA_HOST: db
      PMA_PORT: 3306
      PMA_USER: stock_user
      PMA_PASSWORD: stock123456
    depends_on:
      - db
    restart: always
    networks:
      - stock-monitor-network

  redis-commander:
    image: rediscommander/redis-commander:latest
    container_name: stock-monitor-redis-commander
    ports:
      - "8081:8081"
    environment:
      REDIS_HOSTS: redis:redis:6379
    depends_on:
      - redis
    restart: always
    networks:
      - stock-monitor-network

volumes:
  mysql_data:
  redis_data:

networks:
  stock-monitor-network:
    driver: bridge
```

### 3.2 docker-compose.prod.yml

**apps/stock-monitor-backend/docker-compose.prod.yml**:
```yaml
version: '3.8'

services:
  app:
    image: your-username/stock-monitor-backend:latest
    container_name: stock-monitor-backend
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    environment:
      - DATABASE_URL=mysql+aiomysql://stock_user:stock123456@db:3306/stock_monitor
      - REDIS_URL=redis://redis:6379/0
      - LOG_LEVEL=WARNING
      - ENVIRONMENT=production
    volumes:
      - ./logs:/app/logs
    restart: always
    networks:
      - stock-monitor-network
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
        window: 120s

  db:
    image: mysql:8.0.35
    container_name: stock-monitor-mysql
    environment:
      MYSQL_DATABASE: stock_monitor
      MYSQL_USER: stock_user
      MYSQL_PASSWORD: stock123456
      MYSQL_ROOT_PASSWORD: root123456
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./docker/mysql/conf:/etc/mysql/conf.d
      - ./docker/mysql/init:/docker-entrypoint-initdb.d
    restart: always
    networks:
      - stock-monitor-network
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G

  redis:
    image: redis:7-alpine
    container_name: stock-monitor-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: always
    networks:
      - stock-monitor-network
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru

volumes:
  mysql_data:
  redis_data:

networks:
  stock-monitor-network:
    driver: bridge
```

---

## 4. 生产环境部署步骤

### 4.1 服务器准备

#### 4.1.1 系统要求

| 组件 | 最低配置 | 推荐配置 |
|------|----------|----------|
| **CPU** | 2核 | 4核 |
| **内存** | 4GB | 8GB |
| **磁盘** | 50GB | 100GB |
| **操作系统** | Ubuntu 20.04+ | Ubuntu 22.04+ |

#### 4.1.2 安装Docker

```bash
# 更新系统包
sudo apt-get update
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common

# 添加Docker官方GPG密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 添加Docker仓库
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker --version
docker-compose --version
```

### 4.2 部署应用

#### 4.2.1 克隆代码

```bash
# 克隆代码仓库
git clone https://github.com/your-username/event-crawler.git
cd event-crawler

# 切换到生产分支
git checkout main
```

#### 4.2.2 配置环境变量

```bash
# 复制环境变量模板
cp apps/stock-monitor-backend/.env.example apps/stock-monitor-backend/.env

# 编辑环境变量
vim apps/stock-monitor-backend/.env
```

**生产环境变量示例**:
```bash
# 应用配置
APP_NAME=Stock Monitor Backend
APP_VERSION=1.0.0
ENVIRONMENT=production

# 服务器配置
HOST=0.0.0.0
PORT=8000
WORKERS=5

# 数据库配置
DATABASE_URL=mysql+aiomysql://stock_user:strong_password@db:3306/stock_monitor
DB_HOST=db
DB_PORT=3306
DB_USER=stock_user
DB_PASSWORD=strong_password
DB_DATABASE=stock_monitor
DB_CHARSET=utf8mb4

# 数据库连接池
DB_MIN_SIZE=5
DB_MAX_SIZE=20
DB_POOL_RECYCLE=3600

# Redis配置
REDIS_URL=redis://redis:6379/0
REDIS_HOST=redis
REDIS_PORT=6379

# Tushare配置
TUSHARE_TOKEN=your_tushare_token

# 日志配置
LOG_LEVEL=WARNING
LOG_FILE=logs/app.log
LOG_ROTATION=500 MB
LOG_RETENTION=90 days

# CORS配置
CORS_ORIGINS=["https://yourdomain.com"]
CORS_ALLOW_CREDENTIALS=true

# API配置
API_V1_PREFIX=/api/v1
DOCS_URL=/docs
REDOC_URL=/redoc
```

#### 4.2.3 启动服务

```bash
# 进入项目目录
cd apps/stock-monitor-backend

# 启动生产环境
docker-compose -f docker-compose.prod.yml up -d

# 查看服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f app
```

### 4.3 配置Nginx反向代理

#### 4.3.1 Nginx配置文件

**/etc/nginx/sites-available/stock-monitor**:
```nginx
upstream stock_monitor_backend {
    least_conn;
    server app:8000 max_fails=3 fail_timeout=30s;
}

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
    ssl_certificate /etc/ssl/certs/your-domain.com.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.com.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # 日志配置
    access_log /var/log/nginx/stock-monitor-access.log;
    error_log /var/log/nginx/stock-monitor-error.log;
    
    # 代理配置
    location /api/ {
        proxy_pass http://stock_monitor_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时配置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 静态文件缓存
    location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

#### 4.3.2 启用配置

```bash
# 创建符号链接
sudo ln -s /etc/nginx/sites-available/stock-monitor /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启Nginx
sudo systemctl restart nginx
```

---

## 5. 数据库迁移流程

### 5.1 Alembic配置

**apps/stock-monitor-backend/alembic.ini**:
```ini
[alembic]
script_location = alembic
prepend_sys_path = .

# 数据库URL（从环境变量读取）
sqlalchemy.url = driver://user:pass@localhost/dbname

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic
```

### 5.2 创建迁移脚本

```bash
# 创建新的迁移
alembic revision --autogenerate -m "添加新字段"

# 手动创建迁移
alembic revision -m "添加新字段"
```

### 5.3 执行迁移

```bash
# 升级到最新版本
alembic upgrade head

# 升级到指定版本
alembic upgrade 001_add_new_field

# 降级到指定版本
alembic downgrade 001_add_new_field

# 查看当前版本
alembic current

# 查看历史版本
alembic history
```

---

## 6. 环境变量配置

### 6.1 环境变量文件

**apps/stock-monitor-backend/.env**:
```bash
# 应用配置
APP_NAME=Stock Monitor Backend
APP_VERSION=1.0.0
ENVIRONMENT=production

# 服务器配置
HOST=0.0.0.0
PORT=8000
WORKERS=5

# 数据库配置
DATABASE_URL=mysql+aiomysql://stock_user:strong_password@db:3306/stock_monitor
DB_HOST=db
DB_PORT=3306
DB_USER=stock_user
DB_PASSWORD=strong_password
DB_DATABASE=stock_monitor
DB_CHARSET=utf8mb4

# 数据库连接池
DB_MIN_SIZE=5
DB_MAX_SIZE=20
DB_POOL_RECYCLE=3600

# Redis配置
REDIS_URL=redis://redis:6379/0
REDIS_HOST=redis
REDIS_PORT=6379

# Tushare配置
TUSHARE_TOKEN=your_tushare_token

# 日志配置
LOG_LEVEL=WARNING
LOG_FILE=logs/app.log
LOG_ROTATION=500 MB
LOG_RETENTION=90 days

# CORS配置
CORS_ORIGINS=["https://yourdomain.com"]
CORS_ALLOW_CREDENTIALS=true

# API配置
API_V1_PREFIX=/api/v1
DOCS_URL=/docs
REDOC_URL=/redoc
```

### 6.2 敏感信息管理

#### 6.2.1 使用Docker Secrets

```bash
# 创建Docker Secret
echo "strong_password" | docker secret create db_password -

# 在docker-compose.yml中使用
version: '3.8'
services:
  app:
    environment:
      - DB_PASSWORD_FILE=/run/secrets/db_password
    secrets:
      - db_password

secrets:
  db_password:
    external: true
```

#### 6.2.2 使用环境变量管理工具

```bash
# 使用direnv管理环境变量
brew install direnv

# 在项目根目录创建.env文件
echo "export DATABASE_URL=..." > .env

# 加载环境变量
direnv allow .env
```

---

## 7. 回滚策略

### 7.1 Docker镜像回滚

```bash
# 查看镜像历史
docker images | grep stock-monitor-backend

# 回滚到上一个版本
docker stop stock-monitor-backend
docker rm stock-monitor-backend
docker run -d --name stock-monitor-backend stock-monitor-backend:v1.0.0

# 或者使用docker-compose
docker-compose down
docker-compose up -d --scale app=1
```

### 7.2 数据库回滚

```bash
# 备份当前数据库
mysqldump -u stock_user -p stock_monitor > backup_$(date +%Y%m%d_%H%M%S).sql

# 恢复数据库
mysql -u stock_user -p stock_monitor < backup_20240115_103045.sql
```

### 7.3 代码回滚

```bash
# 查看提交历史
git log --oneline

# 回滚到指定提交
git checkout <commit-hash>

# 或者使用git revert
git revert <commit-hash>

# 推送到远程
git push origin main
```

---

## 8. 监控和日志

### 8.1 应用日志

#### 8.1.1 日志配置

```python
# apps/stock-monitor-backend/app/config/logging.py
from loguru import logger
import sys

# 配置日志
logger.remove()  # 移除默认处理器

# 添加控制台输出
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
    colorize=True
)

# 添加文件输出
logger.add(
    "logs/app.log",
    rotation="100 MB",
    retention="30 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="INFO"
)

# 添加错误日志
logger.add(
    "logs/error.log",
    rotation="50 MB",
    retention="90 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="ERROR"
)
```

#### 8.1.2 查看日志

```bash
# 查看应用日志
docker-compose logs -f app

# 查看错误日志
docker-compose exec app tail -f logs/error.log

# 查看最近100行日志
docker-compose logs --tail=100 app
```

### 8.2 系统监控

#### 8.2.1 使用Prometheus监控

**prometheus.yml**:
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'stock-monitor'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

#### 8.2.2 使用Grafana可视化

```bash
# 启动Grafana
docker run -d \
  --name=grafana \
  -p 3000:3000 \
  grafana/grafana

# 访问Grafana
# http://your-server:3000
# 默认用户名/密码：admin/admin
```

---

## 9. 总结

本文档详细描述了Event-Crawler项目的部署流程，包括：

1. **Docker镜像构建**: Stock Monitor Backend Dockerfile、Chrome Extension构建、构建Docker镜像
2. **Docker Compose配置**: docker-compose.yml、docker-compose.prod.yml
3. **生产环境部署步骤**: 服务器准备、部署应用、配置Nginx反向代理
4. **数据库迁移流程**: Alembic配置、创建迁移脚本、执行迁移
5. **环境变量配置**: 环境变量文件、敏感信息管理
6. **回滚策略**: Docker镜像回滚、数据库回滚、代码回滚
7. **监控和日志**: 应用日志、系统监控

遵循这些部署流程可以确保应用稳定、安全地部署到生产环境。

---

**文档维护**: 本文档应随着部署流程的演进而持续更新，确保与实际部署实践保持一致。
