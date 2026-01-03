# Docker部署指南

## 概述

本指南详细说明如何使用Docker和Docker Compose部署股票监控系统，包括MySQL 8和Redis 7的配置。

## 系统要求

- macOS 10.15+ 或 Linux
- Docker Desktop 4.0+
- Docker Compose 3.3+
- 至少4GB可用内存
- 至少10GB可用磁盘空间

## 快速开始

### 1. 启动所有服务

```bash
# 进入项目目录
cd /Users/mac/ok-mcp/app/stock-monitor-backend

# 启动所有Docker服务
docker-compose up -d

# 查看服务状态
docker-compose ps
```

### 2. 验证服务

```bash
# 检查MySQL连接
docker exec stock_monitor_mysql mysql -u stock_user -pstock123456 -e "SELECT 1"

# 检查Redis连接
docker exec stock_monitor_redis redis-cli ping

# 检查后端API
curl http://localhost:8000/api/v1/health
```

### 3. 访问管理界面

- **API文档**: http://localhost:8000/docs
- **phpMyAdmin**: http://localhost:8080
- **Redis Commander**: http://localhost:8081

## 服务配置详情

### MySQL 8.0.35 配置

```yaml
mysql:
  image: mysql:8.0.35
  container_name: stock_monitor_mysql
  restart: always
  environment:
    MYSQL_ROOT_PASSWORD: root123456
    MYSQL_DATABASE: stock_monitor
    MYSQL_USER: stock_user
    MYSQL_PASSWORD: stock123456
  ports:
    - "3306:3306"
  volumes:
    - mysql_data:/var/lib/mysql
  networks:
    - stock_monitor_network
  healthcheck:
    test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
    timeout: 20s
    retries: 10
    interval: 30s
```

**连接信息：**
- 主机: localhost
- 端口: 3306
- 数据库: stock_monitor
- 用户名: stock_user
- 密码: stock123456
- Root密码: root123456

### Redis 7 配置

```yaml
redis:
  image: redis:7-alpine
  container_name: stock_monitor_redis
  restart: always
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data
  networks:
    - stock_monitor_network
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    timeout: 10s
    retries: 5
    interval: 30s
```

**连接信息：**
- 主机: localhost
- 端口: 6379
- 密码: 无

### phpMyAdmin 配置

```yaml
phpmyadmin:
  image: phpmyadmin/phpmyadmin
  container_name: stock_monitor_phpmyadmin
  restart: always
  environment:
    PMA_HOST: mysql
    PMA_PORT: 3306
    PMA_USER: stock_user
    PMA_PASSWORD: stock123456
  ports:
    - "8080:80"
  depends_on:
    - mysql
  networks:
    - stock_monitor_network
```

### Redis Commander 配置

```yaml
redis-commander:
  image: rediscommander/redis-commander:latest
  container_name: stock_monitor_redis_commander
  restart: always
  environment:
    REDIS_HOSTS: local:redis:6379
  ports:
    - "8081:8081"
  depends_on:
    - redis
  networks:
    - stock_monitor_network
  healthcheck:
    test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:8081"]
    timeout: 10s
    retries: 5
    interval: 30s
```

## 数据持久化

### 数据卷配置

```yaml
volumes:
  mysql_data:
    driver: local
  redis_data:
    driver: local
```

### 数据备份

```bash
# MySQL数据备份
docker exec stock_monitor_mysql mysqldump -u stock_user -pstock123456 stock_monitor > backup_$(date +%Y%m%d_%H%M%S).sql

# Redis数据备份
docker exec stock_monitor_redis redis-cli BGSAVE
docker cp stock_monitor_redis:/data/dump.rdb ./redis_backup_$(date +%Y%m%d_%H%M%S).rdb
```

### 数据恢复

```bash
# MySQL数据恢复
docker exec -i stock_monitor_mysql mysql -u stock_user -pstock123456 stock_monitor < backup_file.sql

# Redis数据恢复
docker cp redis_backup.rdb stock_monitor_redis:/data/dump.rdb
docker restart stock_monitor_redis
```

## 网络配置

### 自定义网络

```yaml
networks:
  stock_monitor_network:
    driver: bridge
```

### 端口映射

| 服务 | 容器端口 | 主机端口 | 说明 |
|------|----------|----------|------|
| MySQL | 3306 | 3306 | 数据库连接 |
| Redis | 6379 | 6379 | 缓存连接 |
| phpMyAdmin | 80 | 8080 | 数据库管理 |
| Redis Commander | 8081 | 8081 | Redis管理 |
| 后端API | 8000 | 8000 | API服务 |

## 环境变量配置

### .env 文件配置

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

# 数据库配置（Docker）
DATABASE_URL=mysql+aiomysql://stock_user:stock123456@localhost:3306/stock_monitor
DB_HOST=localhost
DB_PORT=3306
DB_USER=stock_user
DB_PASSWORD=stock123456
DB_DATABASE=stock_monitor
DB_CHARSET=utf8mb4
DB_ECHO=false

# Redis配置（Docker）
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
REDIS_DECODE_RESPONSES=true

# 其他配置...
```

## 常用命令

### 服务管理

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 重启服务
docker-compose restart

# 查看服务状态
docker-compose ps

# 查看服务日志
docker-compose logs -f [service_name]

# 停止并删除所有数据
docker-compose down -v
```

### 容器操作

```bash
# 进入MySQL容器
docker exec -it stock_monitor_mysql bash

# 进入Redis容器
docker exec -it stock_monitor_redis sh

# 执行MySQL命令
docker exec stock_monitor_mysql mysql -u stock_user -pstock123456 -e "SHOW DATABASES;"

# 执行Redis命令
docker exec stock_monitor_redis redis-cli info
```

### 日志查看

```bash
# 查看所有服务日志
docker-compose logs

# 查看特定服务日志
docker-compose logs mysql
docker-compose logs redis

# 实时跟踪日志
docker-compose logs -f --tail=100
```

## 故障排除

### 常见问题

#### 1. MySQL启动失败

**问题**: MySQL容器一直重启
**解决方案**:
```bash
# 检查日志
docker logs stock_monitor_mysql

# 清理数据卷重新启动
docker-compose down -v
docker-compose up -d
```

#### 2. 端口冲突

**问题**: 端口被占用
**解决方案**:
```bash
# 查看端口占用
lsof -i :3306
lsof -i :6379
lsof -i :8080

# 修改docker-compose.yml中的端口映射
```

#### 3. 数据库连接失败

**问题**: 后端无法连接数据库
**解决方案**:
```bash
# 检查MySQL服务状态
docker-compose ps mysql

# 测试数据库连接
docker exec stock_monitor_mysql mysql -u stock_user -pstock123456 -e "SELECT 1"

# 检查网络连接
docker network ls
docker network inspect stock-monitor-backend_stock_monitor_network
```

#### 4. 权限问题

**问题**: 数据卷权限错误
**解决方案**:
```bash
# 检查数据卷
docker volume ls
docker volume inspect stock-monitor-backend_mysql_data

# 重新创建数据卷
docker-compose down -v
docker volume prune
docker-compose up -d
```

### 健康检查

```bash
# 检查所有服务健康状态
docker-compose ps

# 检查特定服务健康状态
docker inspect --format='{{.State.Health.Status}}' stock_monitor_mysql
docker inspect --format='{{.State.Health.Status}}' stock_monitor_redis
```

## 性能优化

### MySQL优化

```bash
# 在docker-compose.yml中添加MySQL配置
command: >
  --default-authentication-plugin=mysql_native_password
  --character-set-server=utf8mb4
  --collation-server=utf8mb4_unicode_ci
  --innodb_buffer_pool_size=256M
  --max_connections=1000
```

### Redis优化

```bash
# 在docker-compose.yml中添加Redis配置
command: >
  redis-server
  --maxmemory 256mb
  --maxmemory-policy allkeys-lru
  --save 900 1
  --save 300 10
  --save 60 10000
```

## 安全配置

### 生产环境建议

1. **修改默认密码**
```bash
# 修改MySQL密码
MYSQL_ROOT_PASSWORD=your_secure_root_password
MYSQL_PASSWORD=your_secure_user_password
```

2. **限制网络访问**
```yaml
# 只允许本地访问
ports:
  - "127.0.0.1:3306:3306"
  - "127.0.0.1:6379:6379"
```

3. **使用环境变量文件**
```bash
# 创建.env文件存储敏感信息
echo "MYSQL_ROOT_PASSWORD=your_password" > .env
echo "MYSQL_PASSWORD=your_password" >> .env
```

4. **定期备份**
```bash
# 设置定时备份任务
0 2 * * * /path/to/backup_script.sh
```

## 监控和日志

### 日志配置

```yaml
# 在docker-compose.yml中配置日志
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### 监控脚本

```bash
#!/bin/bash
# health_check.sh

echo "=== Docker服务健康检查 ==="

# 检查容器状态
docker-compose ps

# 检查MySQL连接
echo "检查MySQL连接..."
docker exec stock_monitor_mysql mysql -u stock_user -pstock123456 -e "SELECT 1" 2>/dev/null && echo "✅ MySQL连接正常" || echo "❌ MySQL连接失败"

# 检查Redis连接
echo "检查Redis连接..."
docker exec stock_monitor_redis redis-cli ping 2>/dev/null && echo "✅ Redis连接正常" || echo "❌ Redis连接失败"

# 检查后端API
echo "检查后端API..."
curl -s http://localhost:8000/api/v1/health >/dev/null && echo "✅ 后端API正常" || echo "❌ 后端API异常"

echo "=== 检查完成 ==="
```

## 总结

通过本指南，您可以：

1. ✅ 快速部署MySQL 8和Redis 7服务
2. ✅ 配置数据持久化和网络
3. ✅ 管理和监控Docker服务
4. ✅ 处理常见问题和故障
5. ✅ 优化性能和安全配置

如需帮助，请查看日志文件或联系技术支持。