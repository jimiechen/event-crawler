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
api_router = APIRouter(prefix="/api", tags=["api"])


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
    
    for user in data_manager.users.values():
        return user
    
    raise HTTPException(status_code=401, detail="Invalid session token")


@router.post("/users/change-config")
async def mock_change_user_config(payload: Dict[str, Any]):
    """修改用户配置"""
    return {
        "success": True,
        "message": "配置已成功更新"
    }


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
    
    return accounts


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


@router.get("/account/asset-curve")
async def mock_get_asset_curve(
    timeframe: str = "5m",
    trading_mode: str = "testnet",
    environment: str = "testnet",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """获取账户资产曲线"""
    from datetime import datetime, timedelta
    import random
    
    now = datetime.now()
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except:
            end_dt = now
    else:
        end_dt = now
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except:
            start_dt = end_dt - timedelta(days=7)
    else:
        start_dt = end_dt - timedelta(days=7)
    
    points = []
    current_time = start_dt
    base_value = 10000.0
    current_value = base_value
    
    while current_time <= end_dt:
        change = random.uniform(-50, 50)
        current_value = max(current_value + change, 9000)
        points.append({
            "timestamp": current_time.isoformat(),
            "total_assets": round(current_value, 2),
            "pnl": round(current_value - base_value, 2),
            "pnl_percentage": round(((current_value - base_value) / base_value) * 100, 2)
        })
        current_time += timedelta(minutes=5)
    
    return points


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


# ============================================================================
# Hyperliquid账户相关接口（补充）
# ============================================================================

@router.get("/hyperliquid/accounts/{account_id}/balance")
async def mock_get_hyperliquid_account_balance(account_id: int):
    """获取Hyperliquid账户余额"""
    if account_id not in data_manager.accounts:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    
    return {
        "account_value": 10000.0,
        "margin_balance": 9500.0,
        "wallet_balance": 500.0,
        "available_margin": 9000.0,
        "position_margin": 500.0,
        "unrealized_pnl": 0.0,
        "leverage": 1.0,
        "margin_ratio": 0.95,
        "liquidation_price": None
    }


@router.get("/hyperliquid/accounts/{account_id}/wallet")
async def mock_get_hyperliquid_wallet(account_id: int):
    """获取Hyperliquid钱包信息"""
    if account_id not in data_manager.accounts:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    
    return {
        "address": "0x1234567890abcdef1234567890abcdef1234567890",
        "environment": "testnet",
        "balance": 500.0,
        "margin_used": 500.0,
        "margin_available": 9000.0,
        "total_equity": 10000.0,
        "leverage": 1.0
    }


@router.get("/hyperliquid/accounts/{account_id}/rate-limit")
async def mock_get_hyperliquid_rate_limit(account_id: int, environment: str = "testnet"):
    """获取Hyperliquid速率限制"""
    if account_id not in data_manager.accounts:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    
    return {
        "limit": 100,
        "remaining": 95,
        "reset": 1736774400,
        "environment": environment
    }


@router.get("/account/{account_id}/strategy")
async def mock_get_account_strategy(account_id: int):
    """获取账户策略"""
    if account_id not in data_manager.accounts:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    
    return data_manager.strategies.get(str(account_id), {
        "id": account_id,
        "account_id": account_id,
        "enabled": True,
        "trading_mode": "testnet",
        "risk_per_trade": 0.02,
        "max_positions": 3,
        "use_stop_loss": True,
        "stop_loss_percentage": 0.05,
        "use_take_profit": True,
        "take_profit_percentage": 0.10,
        "created_at": generate_timestamp(),
        "updated_at": generate_timestamp()
    })


@router.get("/wallets")
async def mock_get_wallets():
    """获取钱包列表"""
    return [
        {
            "id": 1,
            "address": "0x1234567890abcdef1234567890abcdef1234567890",
            "environment": "testnet",
            "balance": 500.0,
            "is_active": True
        },
        {
            "id": 2,
            "address": "0xabcdef1234567890abcdef1234567890abcdef123456",
            "environment": "testnet",
            "balance": 1000.0,
            "is_active": False
        }
    ]


@router.get("/traders")
async def mock_get_traders():
    """获取交易员列表"""
    return [
        {
            "id": 1,
            "name": "Trader 1",
            "wallet_address": "0x1234567890abcdef1234567890abcdef1234567890",
            "total_trades": 150,
            "win_rate": 0.6,
            "total_pnl": 2500.0
        },
        {
            "id": 2,
            "name": "Trader 2",
            "wallet_address": "0xabcdef1234567890abcdef1234567890abcdef123456",
            "total_trades": 200,
            "win_rate": 0.55,
            "total_pnl": 1800.0
        }
    ]


@router.get("/klines")
async def mock_get_klines():
    """获取K线数据"""
    return []


@router.get("/tasks")
async def mock_get_tasks():
    """获取任务列表"""
    return []


@router.get("/logs")
async def mock_get_logs():
    """获取日志"""
    return []


@router.get("/stats")
async def mock_get_stats():
    """获取统计信息"""
    return {
        "total_trades": 150,
        "winning_trades": 90,
        "losing_trades": 60,
        "win_rate": 0.6,
        "total_pnl": 2500.0
    }


@router.get("/global-config")
async def mock_get_global_config():
    """获取全局配置"""
    return {
        "sampling_depth": 100,
        "enabled": True
    }


@router.get("/signals")
async def mock_get_signals():
    """获取信号列表"""
    return {
        "signals": list(data_manager.signals.values()),
        "pools": list(data_manager.pools.values())
    }


@router.post("/signals/definitions")
async def mock_create_signal(payload: Dict[str, Any]):
    """创建信号"""
    signal_id = generate_id()
    signal = {
        "id": signal_id,
        "signal_name": payload.get("signal_name", "New Signal"),
        "description": payload.get("description", ""),
        "trigger_condition": payload.get("trigger_condition", {}),
        "enabled": payload.get("enabled", True),
        "created_at": generate_timestamp(),
        "updated_at": generate_timestamp()
    }
    data_manager.signals[signal_id] = signal
    return signal


@router.put("/signals/definitions/{signal_id}")
async def mock_update_signal(signal_id: int, payload: Dict[str, Any]):
    """更新信号"""
    if signal_id not in data_manager.signals:
        raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")
    
    signal = data_manager.signals[signal_id]
    
    if "signal_name" in payload:
        signal["signal_name"] = payload["signal_name"]
    if "description" in payload:
        signal["description"] = payload["description"]
    if "trigger_condition" in payload:
        signal["trigger_condition"] = payload["trigger_condition"]
    if "enabled" in payload:
        signal["enabled"] = payload["enabled"]
    
    signal["updated_at"] = generate_timestamp()
    return signal


@router.delete("/signals/definitions/{signal_id}")
async def mock_delete_signal(signal_id: int):
    """删除信号"""
    if signal_id not in data_manager.signals:
        raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")
    
    del data_manager.signals[signal_id]
    return {
        "success": True,
        "message": "信号已成功删除"
    }


@router.post("/signals/pools")
async def mock_create_pool(payload: Dict[str, Any]):
    """创建信号池"""
    pool_id = generate_id()
    pool = {
        "id": pool_id,
        "pool_name": payload.get("pool_name", "New Pool"),
        "signal_ids": payload.get("signal_ids", []),
        "symbols": payload.get("symbols", []),
        "enabled": payload.get("enabled", True),
        "logic": payload.get("logic", "OR"),
        "created_at": generate_timestamp()
    }
    data_manager.pools[pool_id] = pool
    return pool


@router.put("/signals/pools/{pool_id}")
async def mock_update_pool(pool_id: int, payload: Dict[str, Any]):
    """更新信号池"""
    if pool_id not in data_manager.pools:
        raise HTTPException(status_code=404, detail=f"Pool {pool_id} not found")
    
    pool = data_manager.pools[pool_id]
    
    if "pool_name" in payload:
        pool["pool_name"] = payload["pool_name"]
    if "signal_ids" in payload:
        pool["signal_ids"] = payload["signal_ids"]
    if "symbols" in payload:
        pool["symbols"] = payload["symbols"]
    if "enabled" in payload:
        pool["enabled"] = payload["enabled"]
    if "logic" in payload:
        pool["logic"] = payload["logic"]
    
    pool["updated_at"] = generate_timestamp()
    return pool


@router.delete("/signals/pools/{pool_id}")
async def mock_delete_pool(pool_id: int):
    """删除信号池"""
    if pool_id not in data_manager.pools:
        raise HTTPException(status_code=404, detail=f"Pool {pool_id} not found")
    
    del data_manager.pools[pool_id]
    return {
        "success": True,
        "message": "信号池已成功删除"
    }


@router.post("/signals/create-pool-from-config")
async def mock_create_pool_from_config(payload: Dict[str, Any]):
    """从配置创建信号池"""
    pool_id = generate_id()
    signal_ids = []
    
    for i, signal_config in enumerate(payload.get("signals", [])):
        signal_id = generate_id()
        signal = {
            "id": signal_id,
            "signal_name": f"{payload.get('name', 'Pool')} Signal {i + 1}",
            "description": signal_config.get("description", ""),
            "trigger_condition": {
                "metric": signal_config.get("metric"),
                "operator": signal_config.get("operator"),
                "threshold": signal_config.get("threshold"),
                "time_window": signal_config.get("time_window", "5m")
            },
            "enabled": True,
            "created_at": generate_timestamp(),
            "updated_at": generate_timestamp()
        }
        data_manager.signals[signal_id] = signal
        signal_ids.append(signal_id)
    
    pool = {
        "id": pool_id,
        "pool_name": payload.get("name", "New Pool"),
        "signal_ids": signal_ids,
        "symbols": [payload.get("symbol", "BTC")],
        "enabled": True,
        "logic": payload.get("logic", "AND"),
        "created_at": generate_timestamp()
    }
    data_manager.pools[pool_id] = pool
    
    return {
        "success": True,
        "pool": pool,
        "signals": [data_manager.signals[sid] for sid in signal_ids]
    }


@router.get("/signals/backtest/{signal_id}")
async def mock_get_signal_backtest(signal_id: int, symbol: str, kline_min_ts: Optional[int] = None, kline_max_ts: Optional[int] = None):
    """获取信号回测结果"""
    if signal_id not in data_manager.signals:
        raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")
    
    signal = data_manager.signals[signal_id]
    
    return {
        "symbol": symbol,
        "time_window": signal["trigger_condition"].get("time_window", "5m"),
        "condition": signal["trigger_condition"],
        "kline_count": 500,
        "trigger_count": 15,
        "triggers": data_manager.signal_backtest_data["triggers"],
        "signal_names": {
            str(signal_id): signal["signal_name"]
        }
    }


@router.get("/signals/pool-backtest/{pool_id}")
async def mock_get_pool_backtest(pool_id: int, symbol: str, kline_min_ts: Optional[int] = None, kline_max_ts: Optional[int] = None):
    """获取信号池回测结果"""
    if pool_id not in data_manager.pools:
        raise HTTPException(status_code=404, detail=f"Pool {pool_id} not found")
    
    pool = data_manager.pools[pool_id]
    signal_names = {}
    for sid in pool["signal_ids"]:
        if sid in data_manager.signals:
            signal_names[str(sid)] = data_manager.signals[sid]["signal_name"]
    
    return {
        "symbol": symbol,
        "time_window": "5m",
        "logic": pool["logic"],
        "signal_names": signal_names,
        "kline_count": 500,
        "trigger_count": 20,
        "triggers": data_manager.signal_backtest_data["triggers"],
        "isPoolPreview": True
    }


@router.post("/signals/backtest-preview")
async def mock_preview_backtest(payload: Dict[str, Any]):
    """预览回测结果"""
    return {
        "symbol": payload.get("symbol", "BTC"),
        "time_window": payload.get("triggerCondition", {}).get("time_window", "5m"),
        "condition": payload.get("triggerCondition", {}),
        "kline_count": 500,
        "trigger_count": 15,
        "triggers": data_manager.signal_backtest_data["triggers"]
    }


@router.get("/signals/analyze")
async def mock_analyze_metric(symbol: str, metric: str, period: str):
    """分析指标"""
    return data_manager.metric_analysis


@router.post("/market-regime/batch")
async def mock_batch_market_regime(payload: Dict[str, Any]):
    """批量获取市场状态"""
    symbols = payload.get("symbols", [])
    timestamps = payload.get("timestamp_ms", [])
    
    results = []
    for ts in timestamps:
        results.append({
            "symbol": symbols[0] if symbols else "BTC",
            "regime": "breakout",
            "direction": "bullish",
            "confidence": 0.85,
            "reason": "Price broke above resistance with high volume"
        })
    
    return {
        "results": results
    }


@router.get("/market-regime/configs/list")
async def mock_get_market_regime_configs():
    """获取市场状态配置列表"""
    return {
        "configs": [
            {
                "id": 1,
                "symbol": "BTC",
                "enabled": True,
                "regime": "breakout",
                "threshold": 0.8,
                "time_window": "1h",
                "created_at": "2026-01-10T10:00:00Z",
                "updated_at": "2026-01-13T12:00:00Z"
            },
            {
                "id": 2,
                "symbol": "ETH",
                "enabled": True,
                "regime": "continuation",
                "threshold": 0.75,
                "time_window": "1h",
                "created_at": "2026-01-11T08:00:00Z",
                "updated_at": "2026-01-13T12:00:00Z"
            },
            {
                "id": 3,
                "symbol": "SOL",
                "enabled": False,
                "regime": "absorption",
                "threshold": 0.7,
                "time_window": "30m",
                "created_at": "2026-01-12T14:00:00Z",
                "updated_at": "2026-01-12T14:00:00Z"
            }
        ]
    }


@router.get("/signals/logs")
async def mock_get_signals_logs(pool_id: Optional[int] = None, limit: int = 50):
    """获取信号日志"""
    logs = data_manager.signal_logs
    
    if pool_id:
        logs = [log for log in logs if log.get("pool_id") == pool_id]
    
    return {
        "logs": logs[:limit]
    }


@router.get("/hyperliquid/wallets/all")
async def mock_get_all_wallets():
    """获取所有钱包"""
    return [
        {
            "id": 1,
            "address": "0x1234567890abcdef1234567890abcdef1234567890",
            "environment": "testnet",
            "balance": 500.0,
            "is_active": True
        },
        {
            "id": 2,
            "address": "0xabcdef1234567890abcdef1234567890abcdef123456",
            "environment": "testnet",
            "balance": 1000.0,
            "is_active": False
        }
    ]


@router.get("/market/kline-with-indicators/{symbol}")
async def mock_get_kline_with_indicators(symbol: str, market: str = "hyperliquid", period: str = "1m", count: int = 500):
    """获取K线数据（带指标）"""
    from datetime import datetime, timedelta
    import random
    
    now = datetime.now()
    points = []
    for i in range(count):
        timestamp = now - timedelta(minutes=count-i)
        points.append({
            "timestamp": timestamp.isoformat(),
            "open": random.uniform(95000, 96000),
            "high": random.uniform(96000, 97000),
            "low": random.uniform(94000, 95000),
            "close": random.uniform(95000, 96000),
            "volume": random.uniform(100, 1000),
            "sma_20": random.uniform(95000, 96000),
            "ema_12": random.uniform(95000, 96000),
            "rsi": random.uniform(30, 70)
        })
    
    return points


@router.get("/klines/backfill-tasks")
async def mock_get_backfill_tasks():
    """获取回填任务列表"""
    return []


@router.get("/market/prices")
async def mock_get_prices(symbols: str = "BTC,ETH,SOL,DOGE,XRP"):
    """获取价格数据"""
    import random
    symbols_list = symbols.split(",")
    prices = {}
    for symbol in symbols_list:
        prices[symbol] = {
            "symbol": symbol,
            "price": random.uniform(95000, 96000),
            "change_24h": random.uniform(-5, 5),
            "change_7d": random.uniform(-10, 10),
            "volume_24h": random.uniform(1000000, 10000000)
        }
    return prices


@router.get("/config/global-sampling")
async def mock_get_global_sampling():
    """获取全局采样配置"""
    return {
        "sampling_depth": 100,
        "enabled": True,
        "update_interval": 60
    }


@router.get("/system-logs/stats")
async def mock_get_system_logs_stats():
    """获取系统日志统计"""
    return {
        "total_logs": 1000,
        "error_logs": 10,
        "warning_logs": 50,
        "info_logs": 940
    }


@router.get("/system-logs/")
async def mock_get_system_logs(limit: int = 100):
    """获取系统日志"""
    from datetime import datetime, timedelta
    import random
    
    logs = []
    for i in range(min(limit, 50)):
        timestamp = datetime.now() - timedelta(minutes=i)
        log_type = random.choice(["INFO", "WARNING", "ERROR"])
        logs.append({
            "id": i + 1,
            "timestamp": timestamp.isoformat(),
            "level": log_type,
            "message": f"Sample log message {i + 1}",
            "source": random.choice(["API", "Database", "Scheduler", "WebSocket"])
        })
    
    return logs


@router.get("/analytics/trades")
async def mock_get_analytics_trades(environment: str = "mainnet"):
    """获取分析交易数据"""
    from datetime import datetime, timedelta
    import random
    
    trades = []
    for i in range(20):
        timestamp = datetime.now() - timedelta(hours=i)
        trades.append({
            "id": i + 1,
            "timestamp": timestamp.isoformat(),
            "symbol": random.choice(["BTC", "ETH", "SOL", "DOGE"]),
            "side": random.choice(["BUY", "SELL"]),
            "price": random.uniform(95000, 96000),
            "quantity": random.uniform(0.1, 1.0),
            "pnl": random.uniform(-500, 500),
            "environment": environment
        })
    
    return trades


@router.get("/analytics/by-operation")
async def mock_get_analytics_by_operation(environment: str = "mainnet"):
    """按操作类型获取分析数据"""
    return data_manager.analytics_by_operation


@router.get("/analytics/summary")
async def mock_get_analytics_summary(
    environment: Optional[str] = "mainnet",
    account_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """获取分析汇总数据"""
    return data_manager.analytics_summary


@router.get("/analytics/by-symbol")
async def mock_get_analytics_by_symbol(
    environment: Optional[str] = "mainnet",
    account_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """按交易对获取分析数据"""
    return data_manager.analytics_by_symbol


@router.get("/analytics/by-strategy")
async def mock_get_analytics_by_strategy(
    environment: Optional[str] = "mainnet",
    account_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """按策略获取分析数据"""
    return data_manager.analytics_by_strategy


@router.get("/analytics/by-trigger-type")
async def mock_get_analytics_by_trigger_type(
    environment: Optional[str] = "mainnet",
    account_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """按触发类型获取分析数据"""
    return data_manager.analytics_by_trigger_type


@router.get("/analytics/trades")
async def mock_get_analytics_trades(
    environment: Optional[str] = "mainnet",
    account_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    tag_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """获取交易详情数据"""
    trades_data = data_manager.analytics_trades
    
    # 应用标签过滤
    if tag_filter:
        filtered_trades = [
            t for t in trades_data["trades"]
            if tag_filter in t.get("tags", [])
        ]
        trades_data = {
            "trades": filtered_trades,
            "total": len(filtered_trades),
            "limit": limit,
            "offset": offset,
            "account_equity": trades_data["account_equity"],
            "loss_threshold": trades_data["loss_threshold"]
        }
    
    # 应用分页
    trades_data["trades"] = trades_data["trades"][offset:offset + limit]
    
    return trades_data


@router.get("/hyperliquid/accounts/{account_id}/trading-stats")
async def mock_get_hyperliquid_trading_stats(account_id: int, environment: str = "testnet"):
    """获取Hyperliquid交易统计"""
    if account_id not in data_manager.accounts:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    
    return {
        "total_trades": 150,
        "winning_trades": 90,
        "losing_trades": 60,
        "win_rate": 0.6,
        "total_pnl": 2500.0,
        "realized_pnl": 2000.0,
        "unrealized_pnl": 500.0,
        "total_fees": 150.0,
        "avg_trade_pnl": 16.67,
        "max_profit": 500.0,
        "max_loss": -300.0,
        "sharpe_ratio": 1.5,
        "environment": environment
    }


@router.get("/hyperliquid/trading-mode")
async def mock_get_hyperliquid_trading_mode():
    """获取Hyperliquid交易模式"""
    return {
        "mode": "testnet",
        "available_modes": ["testnet", "mainnet"],
        "current_mode": "testnet",
        "can_switch": True
    }
