"""
Mock数据管理 - 完全独立，不依赖任何原有代码

所有Mock数据存储在内存中，重启后重置。
从API文档提取的Mock响应数据。
"""
from typing import Dict, List, Any, Optional
from .utils import generate_timestamp, generate_id, parse_bool


class MockDataManager:
    """Mock数据管理器"""

    def __init__(self):
        self._init_data()

    def _init_data(self):
        """初始化所有Mock数据"""
        self._init_config_data()
        self._init_crypto_data()
        self._init_ai_decision_data()
        self._init_user_data()
        self._init_account_data()
        self._init_strategy_data()
        self._init_prompt_data()
        self._init_arena_data()
        self._init_hyperliquid_data()
        self._init_membership_data()
        self._init_builder_data()
        self._init_trader_data()
        self._init_backtest_data()

    def _init_config_data(self):
        """初始化配置数据"""
        self.config_check_required = {
            "required_configs": [
                "OPENAI_API_KEY",
                "HYPERLIQUID_API_KEY",
                "HYPERLIQUID_API_SECRET"
            ],
            "missing_configs": [],
            "all_configured": True
        }

    def _init_crypto_data(self):
        """初始化加密货币数据"""
        self.crypto_symbols = {
            "symbols": [
                "BTC", "ETH", "SOL", "DOGE", "XRP",
                "ADA", "AVAX", "MATIC", "LINK", "DOT"
            ],
            "count": 10
        }

        self.crypto_prices = {
            "BTC": {
                "symbol": "BTC",
                "price": 67542.50,
                "price_change_24h": 1234.50,
                "price_change_percent_24h": 1.86,
                "timestamp": generate_timestamp()
            },
            "ETH": {
                "symbol": "ETH",
                "price": 3456.78,
                "price_change_24h": 72.50,
                "price_change_percent_24h": 2.15,
                "timestamp": generate_timestamp()
            },
            "SOL": {
                "symbol": "SOL",
                "price": 142.35,
                "price_change_24h": 5.20,
                "price_change_percent_24h": 3.80,
                "timestamp": generate_timestamp()
            }
        }

        self.crypto_status = {
            "BTC": {
                "symbol": "BTC",
                "market_status": "open",
                "trading_hours": "24/7",
                "last_update": generate_timestamp()
            },
            "ETH": {
                "symbol": "ETH",
                "market_status": "open",
                "trading_hours": "24/7",
                "last_update": generate_timestamp()
            }
        }

        self.crypto_popular = {
            "popular": [
                {
                    "symbol": "BTC",
                    "name": "Bitcoin",
                    "price": 67542.50,
                    "volume_24h": 28500000000
                },
                {
                    "symbol": "ETH",
                    "name": "Ethereum",
                    "price": 3456.78,
                    "volume_24h": 15200000000
                },
                {
                    "symbol": "SOL",
                    "name": "Solana",
                    "price": 142.35,
                    "volume_24h": 3200000000
                }
            ]
        }

    def _init_ai_decision_data(self):
        """初始化AI决策数据"""
        self.ai_decisions = {
            1: {
                "id": 1,
                "account_id": 1,
                "decision_time": "2026-01-13T10:15:00Z",
                "reason": "BTC突破阻力位，趋势强劲",
                "operation": "buy",
                "symbol": "BTC",
                "prev_portion": 0.3,
                "target_portion": 0.5,
                "total_balance": 100000,
                "executed": "true",
                "order_id": 12345
            },
            2: {
                "id": 2,
                "account_id": 1,
                "decision_time": "2026-01-13T09:30:00Z",
                "reason": "市场波动加大，保持观望",
                "operation": "hold",
                "symbol": "ETH",
                "prev_portion": 0.4,
                "target_portion": 0.4,
                "total_balance": 100000,
                "executed": "true"
            }
        }

        self.ai_decision_stats = {
            "total_decisions": 45,
            "executed_decisions": 42,
            "execution_rate": 0.9333,
            "operations": {
                "buy": 18,
                "sell": 15,
                "hold": 12
            },
            "avg_target_portion": 0.45,
            "period_start": "2026-01-06T00:00:00Z",
            "period_end": "2026-01-13T00:00:00Z"
        }

    def _init_user_data(self):
        """初始化用户数据"""
        self.users = {
            1: {
                "id": 1,
                "username": "trader001",
                "email": "trader001@example.com",
                "is_active": True,
                "created_at": "2025-06-15T08:00:00Z",
                "last_login": "2026-01-13T10:25:00Z"
            }
        }

        self.user_sessions = {
            "trader001": {
                "user": {
                    "id": 1,
                    "username": "trader001",
                    "email": "trader001@example.com",
                    "is_active": True
                },
                "session_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "expires_at": "2026-01-20T10:30:00Z"
            }
        }

    def _init_account_data(self):
        """初始化账户数据"""
        self.accounts = {
            1: {
                "id": 1,
                "user_id": 1,
                "name": "GPT Trader",
                "model": "gpt-4-turbo",
                "base_url": "https://api.openai.com/v1",
                "api_key": "sk-****",
                "initial_capital": 100000,
                "current_cash": 125000,
                "frozen_cash": 0,
                "account_type": "AI",
                "is_active": True,
                "auto_trading_enabled": True,
                "wallet_address": None,
                "has_mainnet_wallet": False,
                "show_on_dashboard": True
            },
            2: {
                "id": 2,
                "user_id": 1,
                "name": "Claude Analyst",
                "model": "claude-3-opus",
                "base_url": "https://api.anthropic.com/v1",
                "api_key": "sk-ant-****",
                "initial_capital": 50000,
                "current_cash": 48500,
                "frozen_cash": 0,
                "account_type": "AI",
                "is_active": True,
                "auto_trading_enabled": False,
                "wallet_address": None,
                "has_mainnet_wallet": False,
                "show_on_dashboard": True
            },
            3: {
                "id": 3,
                "user_id": 1,
                "name": "Hidden Account",
                "model": "gpt-3.5-turbo",
                "base_url": "https://api.openai.com/v1",
                "api_key": "sk-****",
                "initial_capital": 20000,
                "current_cash": 19500,
                "frozen_cash": 0,
                "account_type": "AI",
                "is_active": True,
                "auto_trading_enabled": False,
                "wallet_address": None,
                "has_mainnet_wallet": False,
                "show_on_dashboard": False
            }
        }

        self.account_overview = {
            "total_accounts": 3,
            "active_accounts": 3,
            "total_assets": 193000,
            "total_pnl": 23000,
            "total_return_percent": 13.52,
            "accounts": [
                {
                    "id": 1,
                    "name": "GPT Trader",
                    "initial_capital": 100000,
                    "current_assets": 125000,
                    "pnl": 25000,
                    "return_percent": 25.0
                },
                {
                    "id": 2,
                    "name": "Claude Analyst",
                    "initial_capital": 50000,
                    "current_assets": 48500,
                    "pnl": -1500,
                    "return_percent": -3.0
                },
                {
                    "id": 3,
                    "name": "Hidden Account",
                    "initial_capital": 20000,
                    "current_assets": 19500,
                    "pnl": -500,
                    "return_percent": -2.5
                }
            ]
        }

        self.llm_test_result = {
            "success": True,
            "message": "LLM连接测试成功",
            "response": {
                "model": "gpt-4-turbo",
                "latency_ms": 234,
                "status": "ok"
            }
        }

    def _init_strategy_data(self):
        """初始化策略数据"""
        self.strategies = {
            1: {
                "trigger_mode": "interval",
                "interval_seconds": 300,
                "tick_batch_size": None,
                "enabled": True,
                "last_trigger_at": "2026-01-13T10:30:00Z"
            },
            2: {
                "trigger_mode": "realtime",
                "interval_seconds": None,
                "tick_batch_size": None,
                "enabled": True,
                "last_trigger_at": "2026-01-13T09:45:00Z"
            }
        }

    def _init_prompt_data(self):
        """初始化提示词数据"""
        self.prompt_templates = {
            1: {
                "id": 1,
                "key": "default_trading",
                "name": "默认交易提示词",
                "description": "适用于大多数交易场景的通用提示词",
                "templateText": "当前市场状况：{{market_data}}\n账户余额：{{balance}}\n持仓情况：{{positions}}\n请分析并给出交易建议。",
                "systemTemplateText": "你是一个专业的交易分析师，基于市场数据和账户状况提供交易建议。",
                "isSystem": "true",
                "isDeleted": "false",
                "createdBy": "system",
                "updatedBy": None,
                "createdAt": "2025-06-01T00:00:00Z",
                "updatedAt": None
            },
            2: {
                "id": 2,
                "key": "aggressive_trading",
                "name": "激进交易提示词",
                "description": "适用于追求高收益的激进交易策略",
                "templateText": "当前市场状况：{{market_data}}\n账户余额：{{balance}}\n持仓情况：{{positions}}\n请基于激进策略分析并给出交易建议，关注短期波动机会。",
                "systemTemplateText": "你是一个激进交易专家，善于捕捉短期市场波动机会。",
                "isSystem": "false",
                "isDeleted": "false",
                "createdBy": "admin",
                "updatedBy": "trader001",
                "createdAt": "2025-07-15T10:00:00Z",
                "updatedAt": "2025-12-01T15:30:00Z"
            },
            3: {
                "id": 3,
                "key": "conservative_trading",
                "name": "保守交易提示词",
                "description": "适用于追求稳健收益的保守交易策略",
                "templateText": "当前市场状况：{{market_data}}\n账户余额：{{balance}}\n持仓情况：{{positions}}\n请基于保守策略分析并给出交易建议，注重风险控制。",
                "systemTemplateText": "你是一个保守交易专家，注重风险控制和稳健收益。",
                "isSystem": "false",
                "isDeleted": "false",
                "createdBy": "trader001",
                "updatedBy": None,
                "createdAt": "2026-01-13T11:05:00Z",
                "updatedAt": None
            }
        }

        self.prompt_bindings = {
            1: {
                "id": 1,
                "accountId": 1,
                "accountName": "GPT Trader",
                "accountModel": "gpt-4-turbo",
                "promptTemplateId": 1,
                "promptKey": "default_trading",
                "promptName": "默认交易提示词",
                "updatedBy": "trader001",
                "updatedAt": "2026-01-10T10:00:00Z"
            },
            2: {
                "id": 2,
                "accountId": 2,
                "accountName": "Claude Analyst",
                "accountModel": "claude-3-opus",
                "promptTemplateId": 2,
                "promptKey": "aggressive_trading",
                "promptName": "激进交易提示词",
                "updatedBy": "trader001",
                "updatedAt": "2026-01-12T14:20:00Z"
            }
        }

        self.variables_reference = {
            "content": "# 提示词变量参考\n\n## 市场数据变量\n- `{{market_data}}`: 当前市场状况\n- `{{symbol_prices}}`: 各交易对价格\n\n## 账户变量\n- `{{balance}}`: 账户余额\n- `{{positions}}`: 持仓情况\n- `{{pnl}}`: 盈亏情况\n\n## 技术指标变量\n- `{{rsi}}`: RSI指标\n- `{{macd}}`: MACD指标\n- `{{ma}}`: 移动平均线"
        }

    def _init_arena_data(self):
        """初始化Arena数据"""
        self.arena_accounts = [
            {
                "account_id": 1,
                "name": "GPT Trader",
                "model": "gpt-4-turbo"
            },
            {
                "account_id": 2,
                "name": "Claude Analyst",
                "model": "claude-3-opus"
            }
        ]

        self.arena_trades = [
            {
                "trade_id": 1001,
                "order_id": 12345,
                "order_no": "ORD-20260113-001",
                "account_id": 1,
                "account_name": "GPT Trader",
                "model": "gpt-4-turbo",
                "side": "buy",
                "direction": "long",
                "symbol": "BTC",
                "market": "hyperliquid",
                "price": 67500.00,
                "quantity": 0.5,
                "notional": 33750.00,
                "commission": 33.75,
                "trade_time": "2026-01-13T10:15:00Z",
                "wallet_address": "0x1234...5678",
                "signal_trigger_id": 501,
                "prompt_template_id": 1,
                "prompt_template_name": "默认交易提示词",
                "related_orders": [
                    {
                        "type": "tp",
                        "price": 69000.00,
                        "quantity": 0.5,
                        "notional": 34500.00,
                        "commission": 34.50,
                        "trade_time": "2026-01-13T11:30:00Z"
                    }
                ]
            },
            {
                "trade_id": 1002,
                "order_id": 12346,
                "order_no": "ORD-20260113-002",
                "account_id": 2,
                "account_name": "Claude Analyst",
                "model": "claude-3-opus",
                "side": "sell",
                "direction": "short",
                "symbol": "ETH",
                "market": "hyperliquid",
                "price": 3450.00,
                "quantity": 10.0,
                "notional": 34500.00,
                "commission": 34.50,
                "trade_time": "2026-01-13T09:45:00Z",
                "wallet_address": "0xabcd...efgh",
                "signal_trigger_id": 502,
                "prompt_template_id": 2,
                "prompt_template_name": "激进交易提示词",
                "related_orders": [
                    {
                        "type": "sl",
                        "price": 3500.00,
                        "quantity": 10.0,
                        "notional": 35000.00,
                        "commission": 35.00,
                        "trade_time": "2026-01-13T10:00:00Z"
                    }
                ]
            }
        ]

        self.pnl_sync_status = {
            "needs_sync": True,
            "unsync_count": 25
        }

        self.pnl_update_result = {
            "success": True,
            "message": "盈亏数据更新成功",
            "environments": {
                "paper": {
                    "fills_count": 150,
                    "unique_orders": 120,
                    "trades_updated": 150,
                    "decisions_updated": 145,
                    "skipped": 5
                },
                "mainnet": {
                    "fills_count": 75,
                    "unique_orders": 60,
                    "trades_updated": 75,
                    "decisions_updated": 70,
                    "skipped": 5
                }
            },
            "errors": []
        }

        self.model_chat_entries = [
            {
                "id": 1,
                "account_id": 1,
                "account_name": "GPT Trader",
                "model": "gpt-4-turbo",
                "operation": "buy",
                "symbol": "BTC",
                "reason": "BTC突破67000阻力位，RSI指标显示超买信号缓解，建议加仓",
                "executed": True,
                "prev_portion": 0.3,
                "target_portion": 0.5,
                "total_balance": 125000,
                "order_id": 12345,
                "decision_time": "2026-01-13T10:15:00Z",
                "trigger_mode": "interval",
                "strategy_enabled": True,
                "last_trigger_at": "2026-01-13T10:15:00Z",
                "trigger_latency_seconds": 2.5,
                "prompt_snapshot": "当前市场状况：BTC $67,542.50 (+1.86%), ETH $3,456.78 (+2.15%)\n账户余额：$125,000\n持仓情况：BTC 0.3, ETH 10.0",
                "reasoning_snapshot": "基于技术分析：\n1. BTC成功突破67000阻力位\n2. RSI从75降至68，超买信号缓解\n3. 成交量放大，显示买盘强劲\n4. MACD金叉形成",
                "decision_snapshot": "{\"operation\":\"buy\",\"symbol\":\"BTC\",\"portion\":0.5,\"reason\":\"BTC突破67000阻力位，RSI指标显示超买信号缓解，建议加仓\"}",
                "wallet_address": "0x1234...5678",
                "signal_trigger_id": 501,
                "prompt_template_id": 1,
                "prompt_template_name": "默认交易提示词"
            },
            {
                "id": 2,
                "account_id": 2,
                "account_name": "Claude Analyst",
                "model": "claude-3-opus",
                "operation": "sell",
                "symbol": "ETH",
                "reason": "ETH在3500附近遇到强阻力，短期回调风险加大，建议减仓",
                "executed": True,
                "prev_portion": 0.6,
                "target_portion": 0.3,
                "total_balance": 48500,
                "order_id": 12346,
                "decision_time": "2026-01-13T09:45:00Z",
                "trigger_mode": "realtime",
                "strategy_enabled": True,
                "last_trigger_at": "2026-01-13T09:45:00Z",
                "trigger_latency_seconds": 1.8,
                "prompt_snapshot": "当前市场状况：BTC $67,542.50 (+1.86%), ETH $3,456.78 (+2.15%)\n账户余额：$48,500\n持仓情况：BTC 0.2, ETH 5.0",
                "reasoning_snapshot": "基于技术分析：\n1. ETH在3500附近多次受阻\n2. RSI达到72，超买信号明显\n3. 成交量萎缩，买盘不足\n4. MACD顶背离形成",
                "decision_snapshot": "{\"operation\":\"sell\",\"symbol\":\"ETH\",\"portion\":0.3,\"reason\":\"ETH在3500附近遇到强阻力，短期回调风险加大，建议减仓\"}",
                "wallet_address": "0xabcd...efgh",
                "signal_trigger_id": 502,
                "prompt_template_id": 2,
                "prompt_template_name": "激进交易提示词"
            }
        ]

        self.model_chat_snapshots = {
            1: {
                "id": 1,
                "prompt_snapshot": "当前市场状况：BTC $67,542.50 (+1.86%), ETH $3,456.78 (+2.15%)\n账户余额：$125,000\n持仓情况：BTC 0.3, ETH 10.0\n技术指标：\n- BTC RSI: 68\n- BTC MACD: 金叉\n- ETH RSI: 72\n- ETH MACD: 顶背离",
                "reasoning_snapshot": "基于技术分析：\n1. BTC成功突破67000阻力位，显示强势\n2. RSI从75降至68，超买信号缓解，仍有上涨空间\n3. 成交量放大至日均1.5倍，显示买盘强劲\n4. MACD金叉形成，动能增强\n5. 建议将BTC仓位从30%提升至50%\n\n风险评估：\n- 止损位：66000\n- 目标位：69000\n- 风险收益比：1:2",
                "decision_snapshot": "{\"operation\":\"buy\",\"symbol\":\"BTC\",\"portion\":0.5,\"reason\":\"BTC突破67000阻力位，RSI指标显示超买信号缓解，建议加仓\",\"stop_loss\":66000,\"target_price\":69000,\"risk_reward_ratio\":2}",
                "error": None
            }
        }

        self.arena_positions = {
            "generated_at": "2026-01-13T12:10:00Z",
            "accounts": [
                {
                    "account_id": 1,
                    "account_name": "GPT Trader",
                    "model": "gpt-4-turbo",
                    "environment": "paper",
                    "wallet_address": None,
                    "total_unrealized_pnl": 2500.00,
                    "available_cash": 75000.00,
                    "used_margin": 50000.00,
                    "positions": [
                        {
                            "id": 1,
                            "symbol": "BTC",
                            "name": "Bitcoin",
                            "market": "hyperliquid",
                            "side": "long",
                            "quantity": 0.5,
                            "avg_cost": 66000.00,
                            "current_price": 67500.00,
                            "notional": 33750.00,
                            "current_value": 33750.00,
                            "unrealized_pnl": 750.00,
                            "leverage": 2.0,
                            "margin_used": 16875.00,
                            "return_on_equity": 4.44,
                            "percentage": 27.0,
                            "margin_mode": "cross",
                            "liquidation_px": 63000.00,
                            "max_leverage": 20.0,
                            "leverage_type": "isolated"
                        },
                        {
                            "id": 2,
                            "symbol": "ETH",
                            "name": "Ethereum",
                            "market": "hyperliquid",
                            "side": "long",
                            "quantity": 10.0,
                            "avg_cost": 3300.00,
                            "current_price": 3456.78,
                            "notional": 34567.80,
                            "current_value": 34567.80,
                            "unrealized_pnl": 1567.80,
                            "leverage": 3.0,
                            "margin_used": 11522.60,
                            "return_on_equity": 13.61,
                            "percentage": 46.1,
                            "margin_mode": "cross",
                            "liquidation_px": 3000.00,
                            "max_leverage": 20.0,
                            "leverage_type": "isolated"
                        }
                    ],
                    "total_assets": 125000.00,
                    "initial_capital": 100000.00,
                    "total_return": 25.0,
                    "margin_usage_percent": 40.0,
                    "margin_mode": "cross"
                },
                {
                    "account_id": 2,
                    "account_name": "Claude Analyst",
                    "model": "claude-3-opus",
                    "environment": "paper",
                    "wallet_address": None,
                    "total_unrealized_pnl": -1500.00,
                    "available_cash": 35000.00,
                    "used_margin": 13500.00,
                    "positions": [
                        {
                            "id": 3,
                            "symbol": "SOL",
                            "name": "Solana",
                            "market": "hyperliquid",
                            "side": "long",
                            "quantity": 100.0,
                            "avg_cost": 150.00,
                            "current_price": 142.35,
                            "notional": 14235.00,
                            "current_value": 14235.00,
                            "unrealized_pnl": -765.00,
                            "leverage": 5.0,
                            "margin_used": 2847.00,
                            "return_on_equity": -26.87,
                            "percentage": 27.8,
                            "margin_mode": "cross",
                            "liquidation_px": 120.00,
                            "max_leverage": 20.0,
                            "leverage_type": "isolated"
                        }
                    ],
                    "total_assets": 48500.00,
                    "initial_capital": 50000.00,
                    "total_return": -3.0,
                    "margin_usage_percent": 27.8,
                    "margin_mode": "cross"
                }
            ]
        }

        self.arena_analytics = {
            "generated_at": "2026-01-13T12:15:00Z",
            "accounts": [
                {
                    "account_id": 1,
                    "account_name": "GPT Trader",
                    "model": "gpt-4-turbo",
                    "initial_capital": 100000,
                    "current_cash": 75000,
                    "positions_value": 50000,
                    "total_assets": 125000,
                    "total_pnl": 25000,
                    "total_return_pct": 25.0,
                    "total_fees": 1250.00,
                    "trade_count": 156,
                    "total_volume": 2850000.00,
                    "first_trade_time": "2025-06-15T10:00:00Z",
                    "last_trade_time": "2026-01-13T10:15:00Z",
                    "biggest_gain": 5250.00,
                    "biggest_loss": -2100.00,
                    "win_rate": 0.65,
                    "loss_rate": 0.35,
                    "sharpe_ratio": 2.35,
                    "balance_volatility": 0.15,
                    "decision_count": 180,
                    "executed_decisions": 165,
                    "decision_execution_rate": 0.917,
                    "avg_target_portion": 0.45,
                    "avg_decision_interval_minutes": 45.5
                },
                {
                    "account_id": 2,
                    "account_name": "Claude Analyst",
                    "model": "claude-3-opus",
                    "initial_capital": 50000,
                    "current_cash": 35000,
                    "positions_value": 13500,
                    "total_assets": 48500,
                    "total_pnl": -1500,
                    "total_return_pct": -3.0,
                    "total_fees": 675.00,
                    "trade_count": 89,
                    "total_volume": 1250000.00,
                    "first_trade_time": "2025-07-01T14:00:00Z",
                    "last_trade_time": "2026-01-13T09:45:00Z",
                    "biggest_gain": 1850.00,
                    "biggest_loss": -3200.00,
                    "win_rate": 0.52,
                    "loss_rate": 0.48,
                    "sharpe_ratio": 0.85,
                    "balance_volatility": 0.22,
                    "decision_count": 95,
                    "executed_decisions": 88,
                    "decision_execution_rate": 0.926,
                    "avg_target_portion": 0.52,
                    "avg_decision_interval_minutes": 38.2
                }
            ],
            "summary": {
                "total_assets": 173500,
                "total_pnl": 23500,
                "total_return_pct": 13.52,
                "total_fees": 1925.00,
                "total_volume": 4100000.00,
                "average_sharpe_ratio": 1.60
            }
        }

    def _init_hyperliquid_data(self):
        """初始化Hyperliquid数据"""
        self.hyperliquid_symbols = {
            "symbols": [
                {
                    "symbol": "BTC",
                    "name": "Bitcoin",
                    "type": "perp"
                },
                {
                    "symbol": "ETH",
                    "name": "Ethereum",
                    "type": "perp"
                },
                {
                    "symbol": "SOL",
                    "name": "Solana",
                    "type": "perp"
                },
                {
                    "symbol": "DOGE",
                    "name": "Dogecoin",
                    "type": "perp"
                },
                {
                    "symbol": "XRP",
                    "name": "Ripple",
                    "type": "perp"
                },
                {
                    "symbol": "ADA",
                    "name": "Cardano",
                    "type": "perp"
                },
                {
                    "symbol": "AVAX",
                    "name": "Avalanche",
                    "type": "perp"
                },
                {
                    "symbol": "MATIC",
                    "name": "Polygon",
                    "type": "perp"
                },
                {
                    "symbol": "LINK",
                    "name": "Chainlink",
                    "type": "perp"
                },
                {
                    "symbol": "DOT",
                    "name": "Polkadot",
                    "type": "perp"
                }
            ],
            "updated_at": "2026-01-13T12:00:00Z",
            "max_symbols": 100
        }

        self.hyperliquid_watchlist = {
            "symbols": ["BTC", "ETH", "SOL", "DOGE", "XRP"],
            "max_symbols": 20
        }

    def _init_membership_data(self):
        """初始化会员数据"""
        self.membership_info = {
            "membership": {
                "status": "active",
                "planKey": "premium",
                "planId": "plan_premium_monthly",
                "subscriptionId": "sub_1234567890",
                "environment": "production",
                "currentPeriodStart": "2026-01-01T00:00:00Z",
                "currentPeriodEnd": "2026-02-01T00:00:00Z",
                "nextBillingTime": "2026-02-01T00:00:00Z",
                "lastPaymentTime": "2026-01-01T00:00:00Z",
                "updatedAt": "2026-01-01T00:00:00Z"
            },
            "events": [
                {
                    "id": 1,
                    "eventType": "subscription_created",
                    "status": "completed",
                    "createdAt": "2025-12-01T00:00:00Z",
                    "environment": "production"
                },
                {
                    "id": 2,
                    "eventType": "payment_success",
                    "status": "completed",
                    "createdAt": "2026-01-01T00:00:00Z",
                    "environment": "production"
                }
            ]
        }

    def _init_builder_data(self):
        """初始化Builder授权数据"""
        self.builder_authorization = {
            "authorized": True,
            "max_fee": 0.001,
            "required_fee": 0.0005,
            "builder_address": "0xBuilderAddress123"
        }

        self.unauthorized_accounts = {
            "unauthorized_accounts": [
                {
                    "account_id": 1,
                    "account_name": "GPT Trader",
                    "wallet_address": "0x1234...5678",
                    "max_fee": 0.0005,
                    "required_fee": 0.001,
                    "error_message": "Builder授权费用不足"
                }
            ]
        }

        self.builder_approve_result = {
            "success": True,
            "message": "Builder授权已成功批准",
            "builder_address": "0xBuilderAddress123",
            "approved_fee": "0.001",
            "result": {
                "transaction_hash": "0xabcdef1234567890",
                "status": "confirmed"
            }
        }

        self.disable_trading_result = {
            "success": True,
            "message": "账户交易功能已禁用",
            "account_id": 1,
            "account_name": "GPT Trader"
        }

    def _init_trader_data(self):
        """初始化交易员数据"""
        self.trader_export_data = {
            "account_id": 1,
            "account_name": "GPT Trader",
            "exported_at": "2026-01-13T12:30:00Z",
            "decision_logs": [
                {
                    "symbol": "BTC",
                    "decision_time": "2026-01-13T10:15:00Z",
                    "operation": "buy",
                    "reason": "BTC突破67000阻力位，RSI指标显示超买信号缓解，建议加仓",
                    "prev_portion": 0.3,
                    "target_portion": 0.5,
                    "total_balance": 125000,
                    "executed": "true",
                    "prompt_snapshot": "当前市场状况：BTC $67,542.50 (+1.86%), ETH $3,456.78 (+2.15%)\n账户余额：$125,000\n持仓情况：BTC 0.3, ETH 10.0",
                    "reasoning_snapshot": "基于技术分析：\n1. BTC成功突破67000阻力位\n2. RSI从75降至68，超买信号缓解\n3. 成交量放大，显示买盘强劲\n4. MACD金叉形成",
                    "decision_snapshot": "{\"operation\":\"buy\",\"symbol\":\"BTC\",\"portion\":0.5,\"reason\":\"BTC突破67000阻力位，RSI指标显示超买信号缓解，建议加仓\"}",
                    "hyperliquid_environment": "paper",
                    "wallet_address": None,
                    "hyperliquid_order_id": "ORD-20260113-001",
                    "tp_order_id": "TP-20260113-001",
                    "sl_order_id": "SL-20260113-001",
                    "realized_pnl": 750.00,
                    "pnl_updated_at": "2026-01-13T11:30:00Z"
                }
            ],
            "trades": [
                {
                    "environment": "paper",
                    "wallet_address": None,
                    "symbol": "BTC",
                    "side": "buy",
                    "quantity": 0.5,
                    "price": 67500.00,
                    "leverage": 2.0,
                    "order_id": "ORD-20260113-001",
                    "trade_value": 33750.00,
                    "fee": 33.75,
                    "trade_time": "2026-01-13T10:15:00Z"
                },
                {
                    "environment": "paper",
                    "wallet_address": None,
                    "symbol": "BTC",
                    "side": "sell",
                    "quantity": 0.5,
                    "price": 69000.00,
                    "leverage": 2.0,
                    "order_id": "TP-20260113-001",
                    "trade_value": 34500.00,
                    "fee": 34.50,
                    "trade_time": "2026-01-13T11:30:00Z"
                }
            ]
        }

        self.import_preview_result = {
            "will_import": {
                "decision_logs": 45,
                "trades": 89
            },
            "will_skip": {
                "decision_logs": 5,
                "trades": 3
            },
            "details": {
                "new_decision_times": [
                    "2026-01-13T10:15:00Z",
                    "2026-01-13T09:45:00Z"
                ],
                "duplicate_decision_times": [
                    "2026-01-12T14:30:00Z"
                ],
                "new_trade_ids": [
                    "ORD-20260113-001",
                    "ORD-20260113-002"
                ],
                "duplicate_trade_ids": [
                    "ORD-20260112-001"
                ]
            }
        }

        self.import_execute_result = {
            "success": True,
            "imported": {
                "decision_logs": 45,
                "trades": 89
            },
            "skipped": {
                "decision_logs": 5,
                "trades": 3
            },
            "errors": []
        }

    def _init_backtest_data(self):
        """初始化回测数据"""
        self.backtest_tasks = {
            1: {
                "id": 1,
                "account_id": 1,
                "name": "BTC策略回测",
                "status": "completed",
                "total_count": 50,
                "completed_count": 48,
                "failed_count": 2,
                "created_at": "2026-01-13T13:00:00Z",
                "started_at": "2026-01-13T13:01:00Z",
                "finished_at": "2026-01-13T13:15:00Z"
            },
            2: {
                "id": 2,
                "account_id": 2,
                "name": "ETH策略回测",
                "status": "running",
                "total_count": 30,
                "completed_count": 20,
                "failed_count": 0,
                "created_at": "2026-01-13T13:10:00Z",
                "started_at": "2026-01-13T13:11:00Z",
                "finished_at": None
            }
        }

        self.backtest_results = {
            "task": {
                "id": 1,
                "account_id": 1,
                "name": "BTC策略回测",
                "status": "completed",
                "total_count": 50,
                "completed_count": 48,
                "failed_count": 2,
                "created_at": "2026-01-13T13:00:00Z",
                "started_at": "2026-01-13T13:01:00Z",
                "finished_at": "2026-01-13T13:15:00Z"
            },
            "items": [
                {
                    "id": 1,
                    "original_decision_time": "2026-01-13T10:15:00Z",
                    "original_operation": "buy",
                    "original_symbol": "BTC",
                    "original_target_portion": 0.5,
                    "original_realized_pnl": 750.00,
                    "new_operation": "hold",
                    "new_symbol": "BTC",
                    "new_target_portion": 0.5,
                    "decision_changed": True,
                    "change_type": "avoided_loss",
                    "status": "completed"
                },
                {
                    "id": 2,
                    "original_decision_time": "2026-01-13T09:45:00Z",
                    "original_operation": "sell",
                    "original_symbol": "ETH",
                    "original_target_portion": 0.3,
                    "original_realized_pnl": -500.00,
                    "new_operation": "sell",
                    "new_symbol": "ETH",
                    "new_target_portion": 0.3,
                    "decision_changed": False,
                    "change_type": None,
                    "status": "completed"
                }
            ],
            "summary": {
                "total": 50,
                "completed": 48,
                "failed": 2,
                "changed": 15,
                "unchanged": 33,
                "avoided_loss_count": 8,
                "avoided_loss_amount": 3200.00,
                "missed_profit_count": 7,
                "missed_profit_amount": 1850.00
            }
        }

        self.backtest_item_detail = {
            "id": 1,
            "original_operation": "buy",
            "original_symbol": "BTC",
            "original_reasoning": "基于技术分析：\n1. BTC成功突破67000阻力位\n2. RSI从75降至68，超买信号缓解\n3. 成交量放大，显示买盘强劲\n4. MACD金叉形成",
            "original_decision_json": "{\"operation\":\"buy\",\"symbol\":\"BTC\",\"portion\":0.5,\"reason\":\"BTC突破67000阻力位，RSI指标显示超买信号缓解，建议加仓\"}",
            "original_prompt_template_name": "默认交易提示词",
            "modified_prompt": "更新后的提示词内容：{{market_data}}\n账户余额：{{balance}}\n持仓情况：{{positions}}\n请基于激进策略分析并给出交易建议，关注短期波动机会。",
            "new_operation": "hold",
            "new_symbol": "BTC",
            "new_reasoning": "基于激进策略分析：\n1. BTC在67000-68000区间震荡\n2. 短期指标显示超买风险\n3. 建议等待更明确的突破信号\n4. 当前持仓保持不变",
            "new_decision_json": "{\"operation\":\"hold\",\"symbol\":\"BTC\",\"portion\":0.5,\"reason\":\"BTC在67000-68000区间震荡，短期指标显示超买风险，建议等待更明确的突破信号\"}",
            "decision_changed": True,
            "change_type": "avoided_loss",
            "error_message": None
        }

        self.backtest_task_items = {
            "task_id": 1,
            "task_name": "BTC策略回测",
            "items": [
                {
                    "id": 1,
                    "modified_prompt": "更新后的提示词内容：{{market_data}}\n账户余额：{{balance}}\n持仓情况：{{positions}}\n请基于激进策略分析并给出交易建议，关注短期波动机会。",
                    "operation": "hold",
                    "symbol": "BTC",
                    "reason": "BTC在67000-68000区间震荡，短期指标显示超买风险，建议等待更明确的突破信号",
                    "decision_time": "2026-01-13T10:15:00Z",
                    "realized_pnl": 750.00
                },
                {
                    "id": 2,
                    "modified_prompt": "更新后的提示词内容：{{market_data}}\n账户余额：{{balance}}\n持仓情况：{{positions}}\n请基于激进策略分析并给出交易建议，关注短期波动机会。",
                    "operation": "sell",
                    "symbol": "ETH",
                    "reason": "ETH在3500附近遇到强阻力，短期回调风险加大，建议减仓",
                    "decision_time": "2026-01-13T09:45:00Z",
                    "realized_pnl": -500.00
                }
            ]
        }


data_manager = MockDataManager()
