"""
Mock路由定义 - 完全独立，不依赖任何原有代码

提供所有API接口的Mock实现，用于开发和测试。
所有数据从mock_data.py获取，不依赖database、services等模块。
"""
from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict, Any
from .mock_data import data_manager
from .utils import generate_timestamp, generate_id, parse_bool, error_response, success_response

router = APIRouter(prefix="/api/mock", tags=["mock"])


# ============================================================================
# 1. 配置管理
# ============================================================================

@router.get("/config/check-required")
async def mock_check_required_configs():
    """检查必需配置"""
    return data_manager.config_check_required


# ============================================================================
# 2. 加密货币
# ============================================================================

@router.get("/crypto/symbols")
async def mock_get_crypto_symbols():
    """获取加密货币符号列表"""
    return data_manager.crypto_symbols


@router.get("/crypto/price/{symbol}")
async def mock_get_crypto_price(symbol: str):
    """获取加密货币价格"""
    prices = data_manager.crypto_prices
    if symbol.upper() not in prices:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
    return prices[symbol.upper()]


@router.get("/crypto/status/{symbol}")
async def mock_get_crypto_status(symbol: str):
    """获取加密货币市场状态"""
    statuses = data_manager.crypto_status
    if symbol.upper() not in statuses:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
    return statuses[symbol.upper()]


@router.get("/crypto/popular")
async def mock_get_popular_cryptos():
    """获取热门加密货币"""
    return data_manager.crypto_popular


# ============================================================================
# 3. AI决策日志
# ============================================================================

@router.get("/accounts/{account_id}/ai-decisions")
async def mock_get_ai_decisions(
    account_id: int,
    operation: Optional[str] = None,
    symbol: Optional[str] = None,
    executed: Optional[bool] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: Optional[int] = None
):
    """获取AI决策列表"""
    decisions = list(data_manager.ai_decisions.values())
    
    # 过滤
    if operation:
        decisions = [d for d in decisions if d["operation"] == operation]
    if symbol:
        decisions = [d for d in decisions if d["symbol"] == symbol]
    if executed is not None:
        executed_str = str(executed).lower()
        decisions = [d for d in decisions if d["executed"] == executed_str]
    
    # 限制数量
    if limit:
        decisions = decisions[:limit]
    
    return {
        "decisions": decisions,
        "total": len(decisions)
    }


@router.get("/accounts/{account_id}/ai-decisions/{decision_id}")
async def mock_get_ai_decision_by_id(account_id: int, decision_id: int):
    """获取单个AI决策详情"""
    if decision_id not in data_manager.ai_decisions:
        raise HTTPException(status_code=404, detail=f"Decision {decision_id} not found")
    return data_manager.ai_decisions[decision_id]


@router.get("/accounts/{account_id}/ai-decisions/stats")
async def mock_get_ai_decision_stats(account_id: int, days: Optional[int] = None):
    """获取AI决策统计"""
    return data_manager.ai_decision_stats


# ============================================================================
# 4. 用户认证
# ============================================================================

@router.post("/users/login")
async def mock_login_user(payload: Dict[str, str]):
    """用户登录"""
    username = payload.get("username")
    password = payload.get("password")
    
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password are required")
    
    # 简单验证
    for user in data_manager.users.values():
        if user["username"] == username:
            return {
                "user": user,
                "session_token": f"mock_token_{generate_id()}",
                "expires_at": "2026-01-20T10:30:00Z"
            }
    
    raise HTTPException(status_code=401, detail="Invalid username or password")


@router.get("/users/profile")
async def mock_get_user_profile(session_token: str):
    """获取用户资料"""
    if not session_token:
        raise HTTPException(status_code=401, detail="Session token is required")
    
    # 简单验证
    for user in data_manager.users.values():
        return user
    
    raise HTTPException(status_code=401, detail="Invalid session token")


# ============================================================================
# 5. 交易账户管理
# ============================================================================

@router.get("/accounts/")
async def mock_list_trading_accounts(session_token: str):
    """列出交易账户（带会话令牌）"""
    if not session_token:
        raise HTTPException(status_code=401, detail="Session token is required")
    
    return {
        "accounts": list(data_manager.accounts.values())
    }


@router.post("/accounts/")
async def mock_create_trading_account(payload: Dict[str, Any], session_token: str):
    """创建交易账户（带会话令牌）"""
    if not session_token:
        raise HTTPException(status_code=401, detail="Session token is required")
    
    account_id = generate_id()
    account = {
        "id": account_id,
        "user_id": 1,
        "name": payload.get("name", "New Account"),
        "model": payload.get("model"),
        "base_url": payload.get("base_url"),
        "api_key": payload.get("api_key"),
        "initial_capital": payload.get("initial_capital", 10000),
        "current_cash": payload.get("initial_capital", 10000),
        "frozen_cash": 0,
        "account_type": payload.get("account_type", "AI"),
        "is_active": True,
        "auto_trading_enabled": payload.get("auto_trading_enabled", True),
        "wallet_address": None,
        "has_mainnet_wallet": False,
        "show_on_dashboard": True,
        "created_at": generate_timestamp()
    }
    
    data_manager.accounts[account_id] = account
    return account


@router.put("/accounts/{account_id}")
async def mock_update_trading_account(
    account_id: int,
    payload: Dict[str, Any],
    session_token: str
):
    """更新交易账户（带会话令牌）"""
    if not session_token:
        raise HTTPException(status_code=401, detail="Session token is required")
    
    if account_id not in data_manager.accounts:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    
    account = data_manager.accounts[account_id]
    
    # 更新字段
    if "name" in payload:
        account["name"] = payload["name"]
    if "model" in payload:
        account["model"] = payload["model"]
    if "base_url" in payload:
        account["base_url"] = payload["base_url"]
    if "api_key" in payload:
        account["api_key"] = payload["api_key"]
    if "auto_trading_enabled" in payload:
        account["auto_trading_enabled"] = payload["auto_trading_enabled"]
    
    account["updated_at"] = generate_timestamp()
    return account


@router.delete("/accounts/{account_id}")
async def mock_delete_trading_account(account_id: int, session_token: str):
    """删除交易账户（带会话令牌）"""
    if not session_token:
        raise HTTPException(status_code=401, detail="Session token is required")
    
    if account_id not in data_manager.accounts:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    
    del data_manager.accounts[account_id]
    return {
        "success": True,
        "message": "账户已成功删除"
    }


@router.get("/account/list")
async def mock_get_accounts(include_hidden: bool = False):
    """获取账户列表（模拟交易）"""
    accounts = list(data_manager.accounts.values())
    
    if not include_hidden:
        accounts = [a for a in accounts if a.get("show_on_dashboard", True)]
    
    return {
        "accounts": accounts
    }


@router.patch("/account/dashboard-visibility")
async def mock_update_dashboard_visibility(updates: List[Dict[str, Any]]):
    """更新仪表板可见性"""
    updated_count = 0
    
    for update in updates:
        account_id = update.get("account_id")
        if account_id in data_manager.accounts:
            data_manager.accounts[account_id]["show_on_dashboard"] = update.get("show_on_dashboard", True)
            updated_count += 1
    
    return {
        "success": True,
        "updated_count": updated_count,
        "updates": updates
    }


@router.get("/account/overview")
async def mock_get_overview():
    """获取账户概览"""
    return data_manager.account_overview


@router.post("/account/")
async def mock_create_account(payload: Dict[str, Any]):
    """创建账户（模拟交易）"""
    account_id = generate_id()
    account = {
        "id": account_id,
        "user_id": 1,
        "name": payload.get("name", "New Account"),
        "model": payload.get("model"),
        "base_url": payload.get("base_url"),
        "api_key": payload.get("api_key"),
        "initial_capital": payload.get("initial_capital", 10000),
        "current_cash": payload.get("initial_capital", 10000),
        "frozen_cash": 0,
        "account_type": payload.get("account_type", "AI"),
        "is_active": True,
        "auto_trading_enabled": payload.get("auto_trading_enabled", True),
        "wallet_address": None,
        "has_mainnet_wallet": False,
        "show_on_dashboard": True,
        "created_at": generate_timestamp()
    }
    
    data_manager.accounts[account_id] = account
    return account


@router.put("/account/{account_id}")
async def mock_update_account(account_id: int, payload: Dict[str, Any]):
    """更新账户（模拟交易）"""
    if account_id not in data_manager.accounts:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    
    account = data_manager.accounts[account_id]
    
    # 更新字段
    if "name" in payload:
        account["name"] = payload["name"]
    if "model" in payload:
        account["model"] = payload["model"]
    if "base_url" in payload:
        account["base_url"] = payload["base_url"]
    if "api_key" in payload:
        account["api_key"] = payload["api_key"]
    if "auto_trading_enabled" in payload:
        account["auto_trading_enabled"] = payload["auto_trading_enabled"]
    
    account["updated_at"] = generate_timestamp()
    return account


@router.post("/account/test-llm")
async def mock_test_llm_connection(payload: Dict[str, Any]):
    """测试LLM连接"""
    return data_manager.llm_test_result


# ============================================================================
# 6. 策略配置
# ============================================================================

@router.get("/account/{account_id}/strategy")
async def mock_get_account_strategy(account_id: int):
    """获取账户策略配置"""
    if account_id not in data_manager.strategies:
        raise HTTPException(status_code=404, detail=f"Strategy for account {account_id} not found")
    return data_manager.strategies[account_id]


@router.put("/account/{account_id}/strategy")
async def mock_update_account_strategy(account_id: int, payload: Dict[str, Any]):
    """更新账户策略配置"""
    if account_id not in data_manager.strategies:
        raise HTTPException(status_code=404, detail=f"Strategy for account {account_id} not found")
    
    strategy = data_manager.strategies[account_id]
    
    # 更新字段
    if "trigger_mode" in payload:
        strategy["trigger_mode"] = payload["trigger_mode"]
    if "interval_seconds" in payload:
        strategy["interval_seconds"] = payload["interval_seconds"]
    if "tick_batch_size" in payload:
        strategy["tick_batch_size"] = payload["tick_batch_size"]
    if "enabled" in payload:
        strategy["enabled"] = payload["enabled"]
    
    strategy["last_trigger_at"] = generate_timestamp()
    return strategy


# ============================================================================
# 7. 提示词模板管理
# ============================================================================

@router.get("/prompts")
async def mock_get_prompt_templates():
    """获取提示词模板列表"""
    return {
        "templates": list(data_manager.prompt_templates.values()),
        "bindings": list(data_manager.prompt_bindings.values())
    }


@router.put("/prompts/{key}")
async def mock_update_prompt_template(key: str, payload: Dict[str, Any]):
    """更新提示词模板"""
    # 查找模板
    template = None
    for t in data_manager.prompt_templates.values():
        if t["key"] == key:
            template = t
            break
    
    if not template:
        raise HTTPException(status_code=404, detail=f"Prompt template {key} not found")
    
    # 更新字段
    if "templateText" in payload:
        template["templateText"] = payload["templateText"]
    if "description" in payload:
        template["description"] = payload["description"]
    if "updatedBy" in payload:
        template["updatedBy"] = payload["updatedBy"]
    
    template["updatedAt"] = generate_timestamp()
    return template


@router.post("/prompts")
async def mock_create_prompt_template(payload: Dict[str, Any]):
    """创建提示词模板"""
    template_id = generate_id()
    template = {
        "id": template_id,
        "key": f"custom_{template_id}",
        "name": payload.get("name", "New Template"),
        "description": payload.get("description"),
        "templateText": payload.get("templateText", ""),
        "systemTemplateText": "你是一个专业的交易分析师，基于市场数据和账户状况提供交易建议。",
        "isSystem": "false",
        "isDeleted": "false",
        "createdBy": payload.get("createdBy", "user"),
        "updatedBy": None,
        "createdAt": generate_timestamp(),
        "updatedAt": None
    }
    
    data_manager.prompt_templates[template_id] = template
    return template


@router.post("/prompts/{template_id}/copy")
async def mock_copy_prompt_template(template_id: int, payload: Dict[str, Any]):
    """复制提示词模板"""
    if template_id not in data_manager.prompt_templates:
        raise HTTPException(status_code=404, detail=f"Prompt template {template_id} not found")
    
    original = data_manager.prompt_templates[template_id]
    new_id = generate_id()
    new_template = {
        "id": new_id,
        "key": f"{original['key']}_copy_{new_id}",
        "name": payload.get("newName", f"{original['name']} 副本"),
        "description": original["description"],
        "templateText": original["templateText"],
        "systemTemplateText": original["systemTemplateText"],
        "isSystem": "false",
        "isDeleted": "false",
        "createdBy": payload.get("createdBy", "user"),
        "updatedBy": None,
        "createdAt": generate_timestamp(),
        "updatedAt": None
    }
    
    data_manager.prompt_templates[new_id] = new_template
    return new_template


@router.delete("/prompts/{template_id}")
async def mock_delete_prompt_template(template_id: int):
    """删除提示词模板"""
    if template_id not in data_manager.prompt_templates:
        raise HTTPException(status_code=404, detail=f"Prompt template {template_id} not found")
    
    del data_manager.prompt_templates[template_id]
    return {
        "success": True,
        "message": "提示词模板已成功删除"
    }


@router.patch("/prompts/{template_id}/name")
async def mock_update_prompt_template_name(template_id: int, payload: Dict[str, Any]):
    """更新提示词模板名称"""
    if template_id not in data_manager.prompt_templates:
        raise HTTPException(status_code=404, detail=f"Prompt template {template_id} not found")
    
    template = data_manager.prompt_templates[template_id]
    
    # 更新字段
    if "name" in payload:
        template["name"] = payload["name"]
    if "description" in payload:
        template["description"] = payload["description"]
    if "updatedBy" in payload:
        template["updatedBy"] = payload["updatedBy"]
    
    template["updatedAt"] = generate_timestamp()
    return template


@router.post("/prompts/bindings")
async def mock_upsert_prompt_binding(payload: Dict[str, Any]):
    """创建或更新提示词绑定"""
    binding_id = payload.get("id")
    account_id = payload.get("account_id")
    prompt_template_id = payload.get("prompt_template_id")
    
    if not account_id or not prompt_template_id:
        raise HTTPException(status_code=400, detail="account_id and prompt_template_id are required")
    
    # 查找模板
    template = None
    for t in data_manager.prompt_templates.values():
        if t["id"] == prompt_template_id:
            template = t
            break
    
    if not template:
        raise HTTPException(status_code=404, detail=f"Prompt template {prompt_template_id} not found")
    
    # 查找账户
    account = None
    for a in data_manager.accounts.values():
        if a["id"] == account_id:
            account = a
            break
    
    if not account:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    
    # 创建或更新绑定
    if binding_id:
        # 更新现有绑定
        for i, binding in enumerate(data_manager.prompt_bindings.values()):
            if binding["id"] == binding_id:
                data_manager.prompt_bindings[i + 1] = {
                    "id": binding_id,
                    "accountId": account_id,
                    "accountName": account["name"],
                    "accountModel": account.get("model"),
                    "promptTemplateId": prompt_template_id,
                    "promptKey": template["key"],
                    "promptName": template["name"],
                    "updatedBy": payload.get("updatedBy"),
                    "updatedAt": generate_timestamp()
                }
                break
    else:
        # 创建新绑定
        new_id = generate_id()
        data_manager.prompt_bindings[new_id] = {
            "id": new_id,
            "accountId": account_id,
            "accountName": account["name"],
            "accountModel": account.get("model"),
            "promptTemplateId": prompt_template_id,
            "promptKey": template["key"],
            "promptName": template["name"],
            "updatedBy": payload.get("updatedBy"),
            "updatedAt": generate_timestamp()
        }
        return data_manager.prompt_bindings[new_id]
    
    return data_manager.prompt_bindings[list(data_manager.prompt_bindings.keys())[-1]]


@router.delete("/prompts/bindings/{binding_id}")
async def mock_delete_prompt_binding(binding_id: int):
    """删除提示词绑定"""
    if binding_id not in data_manager.prompt_bindings:
        raise HTTPException(status_code=404, detail=f"Prompt binding {binding_id} not found")
    
    del data_manager.prompt_bindings[binding_id]
    return {
        "success": True,
        "message": "提示词绑定已成功删除"
    }


@router.get("/prompts/variables-reference")
async def mock_get_variables_reference(lang: str = "en"):
    """获取变量参考文档"""
    return data_manager.variables_reference


@router.post("/prompts/preview")
async def mock_preview_prompt(payload: Dict[str, Any]):
    """预览提示词"""
    account_ids = payload.get("accountIds", [])
    symbols = payload.get("symbols", [])
    
    previews = []
    for account_id in account_ids:
        account = None
        for a in data_manager.accounts.values():
            if a["id"] == account_id:
                account = a
                break
        
        if account:
            previews.append({
                "accountId": account_id,
                "accountName": account["name"],
                "symbols": symbols,
                "filledPrompt": f"当前市场状况：BTC $67,542.50 (+1.86%), ETH $3,456.78 (+2.15%)\n账户余额：${account.get('current_cash', 0)}\n持仓情况：BTC 0.3, ETH 10.0"
            })
    
    return {
        "previews": previews
    }


# ============================================================================
# 8. Alpha Arena 聚合数据
# ============================================================================

@router.get("/arena/trades")
async def mock_get_arena_trades(
    limit: Optional[int] = None,
    account_id: Optional[int] = None,
    trading_mode: Optional[str] = None,
    wallet_address: Optional[str] = None,
    symbol: Optional[str] = None
):
    """获取Arena交易记录"""
    trades = data_manager.arena_trades
    
    # 过滤
    if account_id:
        trades = [t for t in trades if t["account_id"] == account_id]
    if trading_mode:
        trades = [t for t in trades if t.get("trading_mode") == trading_mode]
    if wallet_address:
        trades = [t for t in trades if t.get("wallet_address") == wallet_address]
    if symbol:
        trades = [t for t in trades if t["symbol"] == symbol]
    
    # 限制数量
    if limit:
        trades = trades[:limit]
    
    return {
        "generated_at": generate_timestamp(),
        "accounts": data_manager.arena_accounts,
        "trades": trades
    }


@router.post("/arena/update-pnl")
async def mock_update_arena_pnl():
    """更新Arena盈亏"""
    return data_manager.pnl_update_result


@router.get("/arena/check-pnl-status")
async def mock_check_pnl_sync_status(trading_mode: Optional[str] = None):
    """检查盈亏同步状态"""
    return data_manager.pnl_sync_status


@router.get("/arena/model-chat")
async def mock_get_arena_model_chat(
    limit: Optional[int] = None,
    account_id: Optional[int] = None,
    trading_mode: Optional[str] = None,
    wallet_address: Optional[str] = None,
    before_time: Optional[str] = None,
    symbol: Optional[str] = None
):
    """获取Arena模型聊天记录"""
    entries = data_manager.model_chat_entries
    
    # 过滤
    if account_id:
        entries = [e for e in entries if e["account_id"] == account_id]
    if trading_mode:
        entries = [e for e in entries if e.get("trading_mode") == trading_mode]
    if wallet_address:
        entries = [e for e in entries if e.get("wallet_address") == wallet_address]
    if symbol:
        entries = [e for e in entries if e.get("symbol") == symbol]
    if before_time:
        entries = [e for e in entries if e.get("decision_time", "") < before_time]
    
    # 限制数量
    if limit:
        entries = entries[:limit]
    
    return {
        "generated_at": generate_timestamp(),
        "entries": entries
    }


@router.get("/arena/model-chat/{decision_id}/snapshots")
async def mock_get_model_chat_snapshots(decision_id: int):
    """获取模型聊天快照"""
    if decision_id not in data_manager.model_chat_snapshots:
        raise HTTPException(status_code=404, detail=f"Decision {decision_id} not found")
    return data_manager.model_chat_snapshots[decision_id]


@router.get("/arena/positions")
async def mock_get_arena_positions(
    account_id: Optional[int] = None,
    trading_mode: Optional[str] = None
):
    """获取Arena持仓信息"""
    positions_data = data_manager.arena_positions
    
    # 过滤
    if account_id:
        positions_data["accounts"] = [
            a for a in positions_data["accounts"]
            if a["account_id"] == account_id
        ]
    
    return positions_data


@router.get("/arena/analytics")
async def mock_get_arena_analytics(account_id: Optional[int] = None):
    """获取Arena分析数据"""
    analytics_data = data_manager.arena_analytics
    
    # 过滤
    if account_id:
        analytics_data["accounts"] = [
            a for a in analytics_data["accounts"]
            if a["account_id"] == account_id
        ]
    
    return analytics_data


# ============================================================================
# 9. Hyperliquid 相关
# ============================================================================

@router.get("/hyperliquid/symbols/available")
async def mock_get_hyperliquid_available_symbols():
    """获取Hyperliquid可用符号"""
    return data_manager.hyperliquid_symbols


@router.get("/hyperliquid/symbols/watchlist")
async def mock_get_hyperliquid_watchlist():
    """获取Hyperliquid观察列表"""
    return data_manager.hyperliquid_watchlist


@router.put("/hyperliquid/symbols/watchlist")
async def mock_update_hyperliquid_watchlist(payload: Dict[str, Any]):
    """更新Hyperliquid观察列表"""
    symbols = payload.get("symbols", [])
    
    data_manager.hyperliquid_watchlist = {
        "symbols": symbols,
        "max_symbols": 20
    }
    
    return data_manager.hyperliquid_watchlist


# ============================================================================
# 10. 会员服务
# ============================================================================

@router.get("/membership/me")
async def mock_get_membership_info():
    """获取会员信息"""
    return data_manager.membership_info


# ============================================================================
# 11. Hyperliquid Builder Fee 授权
# ============================================================================

@router.get("/account/hyperliquid/check-builder-authorization")
async def mock_check_builder_authorization(wallet_address: str):
    """检查Builder授权状态"""
    return data_manager.builder_authorization


@router.get("/account/hyperliquid/check-mainnet-accounts")
async def mock_check_mainnet_accounts():
    """检查主网账户授权"""
    return data_manager.unauthorized_accounts


@router.post("/account/hyperliquid/approve-builder")
async def mock_approve_builder(account_id: int):
    """批准Builder授权"""
    return data_manager.builder_approve_result


@router.post("/account/{account_id}/disable-trading")
async def mock_disable_trading(account_id: int):
    """禁用交易"""
    return data_manager.disable_trading_result


# ============================================================================
# 12. 交易员数据导入导出
# ============================================================================

@router.get("/trader/{account_id}/export")
async def mock_export_trader_data(account_id: int):
    """导出交易员数据"""
    return data_manager.trader_export_data


@router.post("/trader/{account_id}/import/preview")
async def mock_preview_trader_import(account_id: int, payload: Dict[str, Any]):
    """预览交易员导入"""
    return data_manager.import_preview_result


@router.post("/trader/{account_id}/import/execute")
async def mock_execute_trader_import(account_id: int, payload: Dict[str, Any]):
    """执行交易员导入"""
    return data_manager.import_execute_result


# ============================================================================
# 13. Prompt 回测
# ============================================================================

@router.post("/prompt-backtest/tasks")
async def mock_create_backtest_task(payload: Dict[str, Any]):
    """创建回测任务"""
    task_id = generate_id()
    task = {
        "id": task_id,
        "account_id": payload.get("account_id"),
        "name": payload.get("name"),
        "status": "pending",
        "total_count": len(payload.get("items", [])),
        "completed_count": 0,
        "failed_count": 0,
        "created_at": generate_timestamp(),
        "started_at": None,
        "finished_at": None
    }
    
    data_manager.backtest_tasks[task_id] = task
    return task


@router.get("/prompt-backtest/tasks")
async def mock_list_backtest_tasks(account_id: Optional[int] = None, limit: int = 20):
    """列出回测任务"""
    tasks = list(data_manager.backtest_tasks.values())
    
    # 过滤
    if account_id:
        tasks = [t for t in tasks if t.get("account_id") == account_id]
    
    # 限制数量
    if limit:
        tasks = tasks[:limit]
    
    return {
        "tasks": tasks
    }


@router.get("/prompt-backtest/tasks/{task_id}")
async def mock_get_backtest_task_status(task_id: int):
    """获取回测任务状态"""
    if task_id not in data_manager.backtest_tasks:
        raise HTTPException(status_code=404, detail=f"Backtest task {task_id} not found")
    return data_manager.backtest_tasks[task_id]


@router.get("/prompt-backtest/tasks/{task_id}/results")
async def mock_get_backtest_task_results(task_id: int):
    """获取回测任务结果"""
    if task_id not in data_manager.backtest_tasks:
        raise HTTPException(status_code=404, detail=f"Backtest task {task_id} not found")
    return data_manager.backtest_results


@router.get("/prompt-backtest/items/{item_id}")
async def mock_get_backtest_item_detail(item_id: int):
    """获取回测项目详情"""
    if item_id not in data_manager.backtest_item_detail:
        raise HTTPException(status_code=404, detail=f"Backtest item {item_id} not found")
    return data_manager.backtest_item_detail


@router.delete("/prompt-backtest/tasks/{task_id}")
async def mock_delete_backtest_task(task_id: int):
    """删除回测任务"""
    if task_id not in data_manager.backtest_tasks:
        raise HTTPException(status_code=404, detail=f"Backtest task {task_id} not found")
    
    del data_manager.backtest_tasks[task_id]
    return {
        "success": True,
        "message": "回测任务已成功删除"
    }


@router.post("/prompt-backtest/tasks/{task_id}/retry")
async def mock_retry_backtest_task(task_id: int):
    """重试回测任务"""
    if task_id not in data_manager.backtest_tasks:
        raise HTTPException(status_code=404, detail=f"Backtest task {task_id} not found")
    
    task = data_manager.backtest_tasks[task_id]
    task["status"] = "pending"
    task["started_at"] = None
    task["finished_at"] = None
    
    return {
        "success": True,
        "message": "回测任务重试已启动",
        "retry_count": 1
    }


@router.get("/prompt-backtest/tasks/{task_id}/items")
async def mock_get_backtest_task_items(task_id: int):
    """获取回测任务项目列表"""
    if task_id not in data_manager.backtest_task_items:
        raise HTTPException(status_code=404, detail=f"Backtest task {task_id} not found")
    
    return data_manager.backtest_task_items
