# 环境变量配置文档

本项目使用 `.env` 文件进行环境变量配置。以下是所有支持的配置项及其说明。

## 基础配置

| 变量名 | 说明 | 默认值 | 示例 |
| :--- | :--- | :--- | :--- |
| `ENVIRONMENT` | 运行环境 | `development` | `development`, `production` |
| `HOST` | 服务器绑定地址 | `0.0.0.0` | `0.0.0.0` |
| `PORT` | 服务器端口 | `8000` | `8000` |
| `LOG_LEVEL` | 日志级别 | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

## 数据库配置 (Database)

支持 MySQL 和 SQLite。

| 变量名 | 说明 | 默认值 | 示例 |
| :--- | :--- | :--- | :--- |
| `DB_TYPE` | 数据库类型 | `mysql` | `mysql`, `sqlite` |
| `DB_HOST` | 数据库主机 | `localhost` | `192.168.1.6` |
| `DB_PORT` | 数据库端口 | `3306` | `3306` |
| `DB_USER` | 数据库用户名 | `root` | `root` |
| `DB_PASSWORD` | 数据库密码 | `""` | `12345678` |
| `DB_DATABASE` | 数据库名称 | `stock_monitor` | `stock_monitor_new` |
| `DB_CHARSET` | 字符集 | `utf8mb4` | `utf8mb4` |
| `DB_ECHO` | 是否打印 SQL | `False` | `True` |

### 连接池配置

| 变量名 | 说明 | 默认值 | 示例 |
| :--- | :--- | :--- | :--- |
| `DB_MIN_SIZE` | 最小连接数 | `5` | `5` |
| `DB_MAX_SIZE` | 最大连接数 | `20` | `20` |
| `DB_POOL_RECYCLE` | 连接回收时间(秒) | `3600` | `3600` |
| `DB_POOL_TIMEOUT` | 连接超时时间(秒) | `30` | `30` |

## Tushare 数据源配置

| 变量名 | 说明 | 默认值 | 示例 |
| :--- | :--- | :--- | :--- |
| `TUSHARE_TOKEN` | Tushare API Token | `None` | `your_token_here` |
| `TUSHARE_INCREMENTAL_START_DATE` | 增量同步起始日期 | `2025-12-22` | `2025-01-01` |

## 文件存储配置

| 变量名 | 说明 | 默认值 | 示例 |
| :--- | :--- | :--- | :--- |
| `CSV_DATA_PATH` | CSV数据存储路径 | `/Users/mac/ok-mcp/history/daily` | `/data/stock/daily` |

## 监控与告警配置

| 变量名 | 说明 | 默认值 | 示例 |
| :--- | :--- | :--- | :--- |
| `ALERT_THRESHOLD_PERCENTAGE` | 价格波动告警阈值(%) | `5.0` | `5.0` |
| `ALERT_CHECK_INTERVAL_MINUTES` | 告警检查间隔(分) | `5` | `5` |

## 数据保留策略

| 变量名 | 说明 | 默认值 | 示例 |
| :--- | :--- | :--- | :--- |
| `DATA_RETENTION_DAYS` | 数据库数据保留天数 | `90` | `90` |
| `LOG_RETENTION_DAYS` | 日志保留天数 | `30` | `30` |
