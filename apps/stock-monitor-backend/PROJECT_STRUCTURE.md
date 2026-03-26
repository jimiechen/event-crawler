# Stock Monitor Backend 项目文件存放规范

## 📁 目录结构规范

```
stock-monitor-backend/
├── app/                          # 主应用代码
│   ├── api/                      # API控制器
│   ├── config/                   # 配置文件
│   ├── models/                   # 数据模型
│   ├── repositories/             # 数据仓库
│   ├── services/                 # 业务服务
│   ├── utils/                    # 工具函数
│   └── websocket/                # WebSocket服务
│
├── tests/                        # 测试代码 (TDD)
│   ├── unit/                     # 单元测试
│   ├── integration/              # 集成测试
│   ├── e2e/                      # 端到端测试
│   └── fixtures/                 # 测试数据
│
├── scripts/                      # 脚本工具
│   ├── db/                       # 数据库脚本
│   └── deploy/                   # 部署脚本
│
├── docs/                         # 项目文档
│   ├── api/                      # API文档
│   ├── design/                   # 设计文档
│   └── guides/                   # 使用指南
│
├── config/                       # 配置文件
├── docker/                       # Docker配置
├── migrations/                   # 数据库迁移
└── temp/                         # 临时文件 (不提交Git)
```

## 📄 文件命名规范

### 代码文件
- 服务类: `{name}_service.py` (如: `tdx_service.py`)
- 控制器: `{name}_controller.py` (如: `stock_controller.py`)
- 模型: `{name}_model.py` 或 `{name}.py` (如: `stock.py`)
- 测试文件: `test_{name}.py` (如: `test_tdx_service.py`)

### 脚本文件
- 数据库脚本: `{action}_{table}.sql` (如: `create_stock_table.sql`)
- 部署脚本: `deploy_{env}.sh` (如: `deploy_prod.sh`)

### 文档文件
- 设计文档: `DESIGN_{feature}.md`
- API文档: `API_{module}.md`
- 使用指南: `GUIDE_{topic}.md`

## 🚫 禁止存放的文件

| 文件类型 | 说明 | 处理方式 |
|---------|------|---------|
| `check_*.py` | 一次性检查脚本 | 移动到 `temp/` |
| `debug_*.py` | 调试脚本 | 移动到 `temp/` |
| `verify_*.py` | 验证脚本 | 移动到 `temp/` |
| `test_*.py` (根目录) | 测试文件 | 移动到 `tests/` |
| `*.bak` | 备份文件 | 删除 |
| `*.log` | 日志文件 | 添加到 `.gitignore` |
| 旧报告文件 | 历史报告 | 移动到 `temp/` 或删除 |

## 📋 清理清单

### 需要删除/移动的目录

1. **scripts/checks/** → 移动到 `temp/`
   - 27个一次性检查脚本

2. **scripts/diagnostics/** → 移动到 `temp/`
   - 6个诊断脚本

3. **scripts/fixes/** → 移动到 `temp/`
   - 6个修复脚本

4. **scripts/legacy/** → 移动到 `temp/`
   - 15个遗留脚本

5. **scripts/tests/** → 移动到 `tests/`
   - 22个测试脚本

6. **scripts/utils/** → 保留或合并到 `app/utils/`
   - 8个工具脚本

7. **acceptance_reports/** → 移动到 `temp/`
   - 16个历史验收报告

8. **collaboration_docs/technical_review/** → 移动到 `temp/`
   - 7个技术评审文件

9. **docs/reports/** → 移动到 `temp/`
   - 11个历史报告

10. **docs/INVESTIGATE_*/** → 移动到 `temp/`
    - 调查文档

11. **docs/WENCAI_BATCH_SYNC/** → 移动到 `temp/`
    - 历史同步文档

12. **docs/同花顺股票监控系统启动和HTML查询页面/** → 移动到 `temp/`
    - 历史项目文档

13. **docs/首页股票列表升级/** → 移动到 `temp/`
    - 历史升级文档

### 需要删除的文件

1. 根目录下的 `.bak` 文件
2. 根目录下的 `debug_*.html`
3. 根目录下的 `debug_*.png`
4. 根目录下的临时 `.md` 文件
5. 根目录下的临时 `.py` 文件

## ✅ 清理后保留的核心文件

```
stock-monitor-backend/
├── app/                          # 完整保留
├── tests/                        # 整合后的测试
├── scripts/
│   ├── db/                       # 数据库脚本
│   ├── deploy/                   # 部署脚本
│   └── migrations/               # 迁移脚本
├── docs/
│   ├── api/                      # API文档
│   ├── design/                   # 设计文档
│   └── guides/                   # 使用指南
│   ├── database_schema.sql       # 数据库结构
│   └── README.md                 # 项目文档
├── config/                       # 配置文件
├── docker/                       # Docker配置
├── migrations/                   # 数据库迁移
├── .env.example                  # 环境变量示例
├── .gitignore                    # Git忽略规则
├── docker-compose.yml            # Docker编排
├── pytest.ini                   # Pytest配置
├── requirements.txt             # 依赖列表
└── run.py                       # 启动脚本
```

## 🔄 清理步骤

1. 创建 `temp/` 目录
2. 移动所有一次性脚本到 `temp/`
3. 移动所有历史报告到 `temp/`
4. 整合测试文件到 `tests/`
5. 删除 `.bak` 文件和临时文件
6. 更新 `.gitignore` 忽略 `temp/`
7. 提交清理后的代码
