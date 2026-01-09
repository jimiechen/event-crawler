stock-monitor-backend/
├── app/                    # 应用代码（保持不变）
├── scripts/                # 脚本目录（已重组）
│   ├── tests/             # ✅ 测试脚本 (22个文件)
│   ├── checks/            # ✅ 检查脚本 (23个文件)
│   ├── debug/             # ✅ 调试脚本 (7个文件)
│   ├── fixes/             # ✅ 修复脚本 (6个文件)
│   ├── migrations/        # ✅ 数据库迁移脚本 (6个文件)
│   ├── diagnostics/       # ✅ 诊断脚本 (6个文件)
│   ├── utils/             # ✅ 工具脚本 (9个文件)
│   └── legacy/           # ✅ 历史脚本 (17个文件)
├── tests/                  # 单元测试（保持不变）
├── docs/                   # 文档
│   └── reports/          # ✅ 测试报告 (11个文件)
├── static/                 # 静态文件（保持不变）
├── config/                 # 配置文件（保持不变）
├── docker/                 # Docker配置（保持不变）
├── sql/                    # SQL脚本（保持不变）
├── run.py                  # ✅ 主启动脚本（保留）
├── run_new.py              # ✅ 增强启动脚本（保留）
├── run_tests.py            # ✅ 测试运行脚本（保留）
├── pytest.ini              # ✅ pytest配置（保留）
├── requirements.txt        # ✅ 依赖文件（保留）
├── docker-compose.yml      # ✅ Docker配置（保留）
├── .env*                   # ✅ 环境变量（保留）
├── *.sh                    # ✅ Shell脚本（保留）
└── *.md                    # ✅ 核心文档（保留）