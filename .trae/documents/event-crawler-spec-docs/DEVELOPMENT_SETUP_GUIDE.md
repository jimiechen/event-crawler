# Event-Crawler 环境搭建指南

## 1. 概述

本文档详细描述Event-Crawler项目的开发环境搭建过程，包括环境要求、依赖安装、数据库初始化、本地开发启动流程和常见问题排查。

**项目位置**: `/Users/mac/StudioProjects/open-citycloud/projects/event-crawler`  
**文档版本**: V1.0  
**最后更新**: 2026-01-08

---

## 2. 环境要求

### 2.1 系统要求

| 组件 | 最低版本 | 推荐版本 | 说明 |
|------|----------|----------|------|
| **操作系统** | macOS 12+ / Ubuntu 20.04+ / Windows 10+ | macOS 14 / Ubuntu 22.04 | 支持主流操作系统 |
| **Node.js** | 16.x | 18.x | Chrome Extension开发 |
| **Python** | 3.9+ | 3.11 | Stock Monitor Backend开发 |
| **MySQL** | 8.0+ | 8.0.35 | 数据库 |
| **Redis** | 6.x | 7.x | 缓存和消息队列 |
| **Docker** | 20.x | 24.x | 容器化部署 |
| **Docker Compose** | 2.x | 2.20.x | 容器编排 |

### 2.2 开发工具

| 工具 | 用途 | 推荐版本 |
|------|------|----------|
| **VS Code** | 代码编辑器 | 1.85+ |
| **Git** | 版本控制 | 2.40+ |
| **Chrome** | 浏览器 | 120+ |
| **Postman** | API测试 | 10.x |
| **DBeaver** | 数据库管理 | 7.x |

---

## 3. 依赖安装

### 3.1 Node.js安装

#### 3.1.1 使用nvm安装（推荐）

```bash
# 安装nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# 重新加载shell配置
source ~/.bashrc

# 安装Node.js 18.x
nvm install 18
nvm use 18

# 验证安装
node --version
npm --version
```

#### 3.1.2 使用官方安装包

```bash
# macOS (使用Homebrew)
brew install node@18

# Ubuntu
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Windows
# 下载安装包：https://nodejs.org/
```

### 3.2 Python安装

#### 3.2.1 使用pyenv安装（推荐）

```bash
# 安装pyenv
brew install pyenv

# 配置shell
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc

# 重新加载shell配置
source ~/.bashrc

# 安装Python 3.11
pyenv install 3.11.7
pyenv global 3.11.7

# 验证安装
python --version
pip --version
```

#### 3.2.2 使用官方安装包

```bash
# macOS (使用Homebrew)
brew install python@3.11

# Ubuntu
sudo apt-get update
sudo apt-get install -y python3.11 python3-pip

# Windows
# 下载安装包：https://www.python.org/downloads/
```

### 3.3 MySQL安装

#### 3.3.1 使用Docker安装（推荐）

```bash
# 拉取MySQL镜像
docker pull mysql:8.0.35

# 启动MySQL容器
docker run --name mysql-stock-monitor \
  -e MYSQL_ROOT_PASSWORD=root123456 \
  -e MYSQL_DATABASE=stock_monitor \
  -e MYSQL_USER=stock_user \
  -e MYSQL_PASSWORD=stock123456 \
  -p 3306:3306 \
  -v mysql_data:/var/lib/mysql \
  -d mysql:8.0.35
```

#### 3.3.2 使用本地安装

```bash
# macOS (使用Homebrew)
brew install mysql@8.0
brew services start mysql@8.0

# Ubuntu
sudo apt-get update
sudo apt-get install -y mysql-server

# Windows
# 下载安装包：https://dev.mysql.com/downloads/mysql/
```

### 3.4 Redis安装

#### 3.4.1 使用Docker安装（推荐）

```bash
# 拉取Redis镜像
docker pull redis:7-alpine

# 启动Redis容器
docker run --name redis-stock-monitor \
  -p 6379:6379 \
  -v redis_data:/data \
  -d redis:7-alpine
```

#### 3.4.2 使用本地安装

```bash
# macOS (使用Homebrew)
brew install redis
brew services start redis

# Ubuntu
sudo apt-get update
sudo apt-get install -y redis-server
sudo systemctl start redis

# Windows
# 下载安装包：https://redis.io/download
```

---

## 4. 项目依赖安装

### 4.1 Chrome Extension依赖

```bash
# 进入Chrome Extension目录
cd /Users/mac/StudioProjects/open-citycloud/projects/event-crawler/apps/chrome-extension

# 安装依赖
npm install

# 验证安装
npm list --depth=0
```

### 4.2 Stock Monitor Backend依赖

```bash
# 进入Stock Monitor Backend目录
cd /Users/mac/StudioProjects/open-citycloud/projects/event-crawler/apps/stock-monitor-backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows

# 升级pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt

# 验证安装
pip list
```

---

## 5. 数据库初始化

### 5.1 创建数据库

```sql
-- 连接到MySQL
mysql -u root -p

-- 创建数据库
CREATE DATABASE IF NOT EXISTS stock_monitor 
DEFAULT CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- 创建用户
CREATE USER IF NOT EXISTS 'stock_user'@'%' IDENTIFIED BY 'stock123456';

-- 授权
GRANT ALL PRIVILEGES ON stock_monitor.* TO 'stock_user'@'%';
FLUSH PRIVILEGES;

-- 退出
EXIT;
```

### 5.2 创建表结构

```bash
# 进入Stock Monitor Backend目录
cd /Users/mac/StudioProjects/open-citycloud/projects/event-crawler/apps/stock-monitor-backend

# 使用SQL脚本创建表
mysql -u stock_user -pstock123456 stock_monitor < docs/database_schema.sql

# 验证表创建
mysql -u stock_user -pstock123456 stock_monitor -e "SHOW TABLES;"
```

### 5.3 初始化测试数据

```sql
-- 插入测试股票信息
INSERT INTO stock_info (stock_code, stock_name, market, industry, sector) VALUES
('000001', '平安银行', 'SZ', '银行', '金融'),
('000002', '万科A', 'SZ', '房地产开发', '房地产'),
('600000', '浦发银行', 'SH', '银行', '金融'),
('600036', '招商银行', 'SH', '银行', '金融'),
('000858', '五粮液', 'SZ', '白酒', '食品饮料');

-- 插入监控列表测试数据
INSERT INTO monitor_list (stock_code, monitor_type, monitor_interval) VALUES
('000001', 'realtime', 30),
('000002', 'realtime', 60),
('600000', 'daily', 3600),
('600036', 'realtime', 30),
('000858', 'realtime', 60);
```

---

## 6. 本地开发启动流程

### 6.1 启动数据库服务

#### 6.1.1 使用Docker Compose启动

```bash
# 进入Stock Monitor Backend目录
cd /Users/mac/StudioProjects/open-citycloud/projects/event-crawler/apps/stock-monitor-backend

# 启动MySQL和Redis
docker-compose up -d mysql redis

# 查看日志
docker-compose logs -f mysql redis

# 停止服务
docker-compose down
```

#### 6.1.2 验证数据库连接

```bash
# 测试MySQL连接
mysql -u stock_user -pstock123456 stock_monitor -e "SELECT 1;"

# 测试Redis连接
redis-cli ping
# 应该返回：PONG
```

### 6.2 启动Stock Monitor Backend

#### 6.2.1 开发模式启动

```bash
# 进入Stock Monitor Backend目录
cd /Users/mac/StudioProjects/open-citycloud/projects/event-crawler/apps/stock-monitor-backend

# 激活虚拟环境
source venv/bin/activate

# 设置环境变量
export DATABASE_URL="mysql+aiomysql://stock_user:stock123456@localhost:3306/stock_monitor"
export REDIS_URL="redis://localhost:6379/0"

# 启动开发服务器
python run.py --mode dev

# 或者使用uvicorn直接启动
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 6.2.2 验证API服务

```bash
# 测试健康检查接口
curl http://localhost:8000/api/v1/health

# 应该返回：
# {
#   "success": true,
#   "data": {
#     "status": "healthy",
#     "timestamp": "2024-01-15T10:30:00Z",
#     "version": "1.0.0",
#     "uptime": 3600.5
#   },
#   "message": "系统运行正常"
# }
```

### 6.3 启动Chrome Extension

#### 6.3.1 开发模式启动

```bash
# 进入Chrome Extension目录
cd /Users/mac/StudioProjects/open-citycloud/projects/event-crawler/apps/chrome-extension

# 启动开发服务器
npm run dev

# 或者使用WXT直接启动
npx wxt
```

#### 6.3.2 加载扩展到浏览器

1. 打开Chrome浏览器
2. 访问 `chrome://extensions/`
3. 启用"开发者模式"
4. 点击"加载已解压的扩展程序"
5. 选择 `.output/chrome-mv3` 目录

#### 6.3.3 验证扩展功能

1. 打开目标网站（如：同花顺）
2. 点击扩展图标
3. 检查侧边栏是否正常显示
4. 检查数据采集是否正常工作

---

## 7. 环境变量配置

### 7.1 Stock Monitor Backend环境变量

创建 `.env` 文件：

```bash
# 应用配置
APP_NAME=Stock Monitor Backend
APP_VERSION=1.0.0
ENVIRONMENT=development

# 服务器配置
HOST=0.0.0.0
PORT=8000
WORKERS=5

# 数据库配置
DATABASE_URL=mysql+aiomysql://stock_user:stock123456@localhost:3306/stock_monitor
DB_HOST=localhost
DB_PORT=3306
DB_USER=stock_user
DB_PASSWORD=stock123456
DB_DATABASE=stock_monitor
DB_CHARSET=utf8mb4

# 数据库连接池
DB_MIN_SIZE=2
DB_MAX_SIZE=10
DB_POOL_RECYCLE=3600

# Redis配置
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379

# Tushare配置
TUSHARE_TOKEN=your_token_here

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
LOG_ROTATION=100 MB
LOG_RETENTION=30 days

# CORS配置
CORS_ORIGINS=["*"]
CORS_ALLOW_CREDENTIALS=true

# API配置
API_V1_PREFIX=/api/v1
DOCS_URL=/docs
REDOC_URL=/redoc
```

### 7.2 Chrome Extension环境变量

创建 `.env` 文件：

```bash
# API配置
API_BASE_URL=http://localhost:8000
API_V1_PREFIX=/api/v1

# Supabase配置（如果使用）
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key

# 开发配置
DEV_MODE=true
DEBUG=true
```

---

## 8. 常见问题排查

### 8.1 数据库连接问题

**问题**: 无法连接到MySQL数据库

**解决方案**:
```bash
# 检查MySQL服务状态
docker ps | grep mysql
# 或者
brew services list | grep mysql

# 检查MySQL日志
docker logs mysql-stock-monitor

# 测试数据库连接
mysql -u stock_user -pstock123456 -h localhost -P 3306 stock_monitor

# 检查防火墙设置
sudo ufw status  # Ubuntu
# 或
sudo pfctl -s all  # macOS
```

### 8.2 Redis连接问题

**问题**: 无法连接到Redis

**解决方案**:
```bash
# 检查Redis服务状态
docker ps | grep redis
# 或者
brew services list | grep redis

# 测试Redis连接
redis-cli ping

# 检查Redis日志
docker logs redis-stock-monitor

# 重启Redis服务
docker restart redis-stock-monitor
```

### 8.3 依赖安装问题

**问题**: npm install或pip install失败

**解决方案**:
```bash
# 清理npm缓存
npm cache clean --force

# 删除node_modules和package-lock.json
rm -rf node_modules package-lock.json

# 重新安装依赖
npm install

# Python依赖安装问题
# 升级pip
pip install --upgrade pip

# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 8.4 扩展加载问题

**问题**: Chrome扩展无法加载

**解决方案**:
1. 检查扩展是否正确打包
   ```bash
   npm run build
   # 检查.output/chrome-mv3目录是否存在
   ```

2. 检查manifest.json是否有效
   ```bash
   # 使用Chrome扩展验证工具
   # https://chrome.google.com/webstore/devconsole
   ```

3. 检查浏览器控制台错误
   - 打开扩展页面
   - 按F12打开开发者工具
   - 查看Console标签的错误信息

### 8.5 API请求问题

**问题**: API请求失败

**解决方案**:
```bash
# 检查后端服务是否启动
curl http://localhost:8000/api/v1/health

# 检查后端日志
tail -f logs/app.log

# 检查CORS配置
# 确保API_BASE_URL配置正确

# 使用Postman测试API
# 导入API文档中的示例请求
```

### 8.6 端口占用问题

**问题**: 端口被占用

**解决方案**:
```bash
# 查看端口占用情况
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# 杀死占用端口的进程
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows

# 或者修改端口配置
export PORT=8001
```

---

## 9. 开发工具配置

### 9.1 VS Code配置

#### 9.1.1 推荐插件

- **Python**: Python扩展包（Microsoft）
- **TypeScript**: TypeScript扩展包（Microsoft）
- **Vue**: Vue - Official（Vue）
- **Prettier**: Prettier - Code formatter（Prettier）
- **ESLint**: ESLint（Microsoft）
- **GitLens**: GitLens（GitKraken）

#### 9.1.2 工作区设置

创建 `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "typescript.tsdk": "node_modules/typescript/lib",
  "volar.takeOverMode.enabled": true
}
```

### 9.2 Git配置

```bash
# 配置用户信息
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# 配置编辑器
git config --global core.editor "code --wait"

# 配置换行符
git config --global core.autocrlf input  # macOS/Linux
git config --global core.autocrlf true   # Windows

# 配置分支命名
git config --global init.defaultBranch main
```

---

## 10. 开发流程

### 10.1 日常开发流程

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 创建功能分支
git checkout -b feat/your-feature-name

# 3. 进行开发
# ... 编写代码 ...

# 4. 提交代码
git add .
git commit -m "feat: 添加新功能"

# 5. 推送到远程
git push origin feat/your-feature-name

# 6. 创建Pull Request
# 在GitHub/GitLab上创建PR
```

### 10.2 调试流程

#### 10.2.1 后端调试

```bash
# 启动调试模式
export DEBUG=true
python run.py --mode dev

# 使用VS Code调试
# 在VS Code中按F5启动调试
```

#### 10.2.2 前端调试

```bash
# 启动开发模式
npm run dev

# 在浏览器中打开扩展
# 按F12打开开发者工具
# 在Sources标签中设置断点
```

---

## 11. 总结

本文档详细描述了Event-Crawler项目的开发环境搭建过程，包括：

1. **环境要求**: 系统要求、开发工具
2. **依赖安装**: Node.js、Python、MySQL、Redis
3. **项目依赖**: Chrome Extension、Stock Monitor Backend
4. **数据库初始化**: 创建数据库、表结构、测试数据
5. **本地开发启动**: 数据库服务、后端服务、前端扩展
6. **环境变量配置**: 后端、前端环境变量
7. **常见问题排查**: 数据库、Redis、依赖、扩展、API、端口
8. **开发工具配置**: VS Code、Git
9. **开发流程**: 日常开发、调试流程

按照本文档的步骤，可以快速搭建完整的开发环境，开始项目开发。

---

**文档维护**: 本文档应随着项目依赖和工具的演进而持续更新，确保与实际开发环境保持一致。
