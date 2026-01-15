"""
AI Decision Service
Implements the core AI decision logic for A-Share trading.
"""

import json
import re
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Literal
import httpx
import pandas as pd
import numpy as np
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config.prompt_templates import STOCK_DEFAULT_PROMPT_TEMPLATE, OUTPUT_FORMAT_JSON
from app.repositories.stock_repository import StockRepository, StockDataRepository
from app.models.tag_management import StockTagInfo, StockTagRelation
from app.models.stock import StockData
from app.models.ai_decision import AIDecisionResult
from app.adapters.arena_adapter import ArenaAdapter
from app.adapters.ashare_adapter import AShareAdapter

logger = logging.getLogger(__name__)

class SafeDict(dict):
    """
    A dictionary that returns a placeholder for missing keys instead of raising KeyError.
    Used for safe string formatting.
    """
    def __missing__(self, key):
        return f"{{N/A: {key}}}"

class DecisionItem(BaseModel):
    """Individual trading decision item"""
    operation: Literal["buy", "sell", "hold", "close"] = Field(description="Trading operation")
    stock_code: str = Field(description="Stock code (6 digits)")
    stock_name: str = Field(description="Stock name")
    target_portion_of_balance: float = Field(default=0.0, ge=0.0, le=1.0, description="Target position size (0.0-1.0)")
    max_price: Optional[float] = Field(default=None, description="Max buy price limit")
    min_price: Optional[float] = Field(default=None, description="Min sell price limit")
    reason: str = Field(description="Primary reason for decision")
    trading_strategy: str = Field(description="Detailed strategy description")

class DecisionResponse(BaseModel):
    """Full decision response schema"""
    decisions: List[DecisionItem]

class AIDecisionConfig(BaseModel):
    """Configuration for AI Decision Service"""
    api_key: str
    base_url: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 5000

class AIDecisionService:
    """
    Service for generating trading decisions using AI models.
    """

    def __init__(self, config: AIDecisionConfig):
        self.config = config
        self.arena_adapter = ArenaAdapter()
        # AShareAdapter needs session, so we instantiate it per request or pass session to methods
        # Here we don't instantiate it yet.

    async def generate_decision(
        self,
        session: AsyncSession,
        stock_code: str,
        template_text: Optional[str] = None, # If None, tries to fetch default from Arena
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a trading decision for a stock.
        """
        # 1. Resolve Template
        template_name = "ashare_json_decision"
        if not template_text:
            # Try to fetch from Arena
            template_text = await self.arena_adapter.get_prompt_template(template_name)
            
        if not template_text:
            # Fallback to local default
            template_text = STOCK_DEFAULT_PROMPT_TEMPLATE
            template_name = "local_default"

        # 2. Prepare Context
        # Instantiate AShareAdapter with the current session
        ashare_adapter = AShareAdapter(session)
        context = await ashare_adapter.get_stock_context(stock_code)
        
        # 3. Render Prompt
        prompt = template_text.format_map(SafeDict(context))
        
        # 4. Call AI Model
        try:
            response = await self._call_llm_api(prompt, model)
            
            # 5. Parse Response (Expect JSON)
            decision_data = self._parse_llm_response(response)
            
            # Add metadata
            decision_data["stock_code"] = stock_code
            decision_data["timestamp"] = datetime.utcnow().isoformat() + "Z"

            # 6. Save to Database
            # Extract primary decision info
            decisions_list = decision_data.get("decisions", [])
            primary_op = "hold"
            primary_reason = "No decision generated"
            
            if decisions_list:
                # Use the first decision as primary
                first_decision = decisions_list[0]
                primary_op = first_decision.get("operation", "hold")
                primary_reason = first_decision.get("reason", "")

            decision_record = AIDecisionResult(
                stock_code=stock_code,
                trade_date=datetime.utcnow().date(), # Use current date or get from context if possible
                decision_json=decision_data,
                model_name=model or self.config.model,
                template_name=template_name,
                primary_operation=primary_op,
                primary_reason=primary_reason,
                created_at=datetime.utcnow()
            )
            session.add(decision_record)
            await session.commit()
            
            return decision_data
            
        except Exception as e:
            logger.error(f"Error generating decision for {stock_code}: {e}", exc_info=True)
            return {
                "error": str(e),
                "stock_code": stock_code,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "decisions": [] # Ensure consistent structure even on error
            }

    async def prepare_decision_context(self, session: AsyncSession, stock_code: str, template_text: str) -> Dict[str, Any]:
        """
        Deprecated: Use AShareAdapter directly.
        """
        ashare_adapter = AShareAdapter(session)
        return await ashare_adapter.get_stock_context(stock_code)

    async def _call_llm_api(self, prompt: str, model: Optional[str] = None) -> str:
        """Call the LLM API."""
        api_key = self.config.api_key
        base_url = self.config.base_url
        model_name = model or self.config.model
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Enforce JSON schema in system prompt
        system_content = (
            "You are a professional trading assistant for the Chinese A-Share market. "
            "You MUST respond with a valid JSON object strictly following this schema:\n"
            f"{json.dumps(DecisionResponse.model_json_schema(), indent=2)}\n"
            "Do NOT output markdown blocks. Output ONLY the raw JSON string."
        )

        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt}
            ],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "response_format": {"type": "json_object"}
        }
        
        async with httpx.AsyncClient() as client:
            try:
                # Use longer timeout for AI generation
                response = await client.post(
                    f"{base_url}/chat/completions", 
                    json=payload, 
                    headers=headers,
                    timeout=60.0 
                )
                response.raise_for_status()
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                return content
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error calling LLM: {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Error calling LLM: {e}")
                raise

    def _parse_llm_response(self, content: str) -> Dict[str, Any]:
        """Parse the LLM response content as JSON and validate against schema."""
        try:
            # 1. Extract JSON string
            json_str = content
            # Try to clean up markdown if present (even if we asked not to)
            match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
            if match:
                json_str = match.group(1)
            elif re.search(r"```\s*(.*?)\s*```", content, re.DOTALL):
                 match = re.search(r"```\s*(.*?)\s*```", content, re.DOTALL)
                 json_str = match.group(1)

            # 2. Parse JSON
            data = json.loads(json_str)
            
            # 3. Validate with Pydantic
            validated = DecisionResponse(**data)
            return validated.model_dump()
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON Parse Error: {e}. Content: {content}")
            return {"raw_content": content, "parsing_error": "Invalid JSON format", "decisions": []}
        except ValidationError as e:
            logger.error(f"Schema Validation Error: {e}. Data: {data}")
            return {"raw_content": content, "parsing_error": f"Schema validation failed: {str(e)}", "decisions": []}
        except Exception as e:
            logger.error(f"Unknown Parse Error: {e}")
            return {"raw_content": content, "parsing_error": str(e), "decisions": []}

    async def prepare_decision_context(
        self, 
        session: AsyncSession, 
        stock_code: str, 
        template_text: str = STOCK_DEFAULT_PROMPT_TEMPLATE
    ) -> Dict[str, Any]:
        """
        Prepare context data by fetching from database.
        """
        ashare_adapter = AShareAdapter(session)
        data_repo = StockDataRepository(session)
        
        # 1. Get A-Share Context (Basic Info, Price, Tags)
        ashare_context = await ashare_adapter.get_stock_context(stock_code)
        
        # 2. Map to Prompt Variables
        market_prices = {stock_code: ashare_context.get("current_price", 0.0)}
        
        # 3. Get Holdings (Mock for now)
        # TODO: Implement actual holdings fetching from AccountRepository
        holdings = [] 
        
        # 4. Get Account Status (Mock)
        # TODO: Implement actual account status
        account_status = {
            "runtime_minutes": 240, # Mock: Market open for 4 hours
            "total_return_percent": 0.0,
            "available_cash": 1000000.0,
            "total_account_value": 1000000.0
        }
        
        # 5. Get Trigger Context (Signals)
        # Fetch active signals from Arena for "A-Share Basic Strategy"
        active_signals = await self.arena_adapter.get_signal_pool_signals("A-Share Basic Strategy")
        
        # Match stock tags to signals
        stock_tags = ashare_context.get("tags", [])
        trigger_context = self._match_signals(stock_tags, active_signals)

        # 6. Build Context (Initial)
        context = self._build_prompt_context(
            account_status=account_status,
            holdings=holdings,
            market_prices=market_prices,
            news_section="No significant news.",
            template_text=template_text,
            trigger_context=trigger_context
        )
        
        # 7. Fill K-lines and Indicators (Real Data)
        variable_groups = self._parse_kline_indicator_variables(template_text)
        
        # Fetch and calculate K-lines and indicators
        dynamic_context = await self._build_klines_and_indicators_context(variable_groups, data_repo)
        
        # Merge into main context
        context.update(dynamic_context)
            
        return context

    def _match_signals(self, stock_context: Dict[str, Any], active_signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Match stock tags with active Arena signals.
        Returns a dictionary of triggered signals.
        """
        triggered = {}
        
        # Extract tags from context for backward compatibility
        stock_tags = stock_context.get("tags", [])
        tag_lookup = {tag["name"]: tag for tag in stock_tags}
        
        for signal in active_signals:
            condition = signal.get("trigger_condition", {})
            if not isinstance(condition, dict):
                continue
                
            # 1. Source: ashare_quant (Tag based)
            if condition.get("source") == "ashare_quant":
                required_tag = condition.get("tag")
                if required_tag in tag_lookup:
                    # Signal Triggered!
                    triggered[signal["name"]] = {
                        "description": signal["description"],
                        "value": tag_lookup[required_tag].get("score", 1.0)
                    }
                continue

            # 2. Metric Comparison (Rule based)
            metric = condition.get("metric")
            if metric:
                # Handle mapping if necessary
                metric_key = metric
                if metric == "price": metric_key = "current_price"
                
                if metric_key not in stock_context:
                    continue
                    
                actual_value = stock_context[metric_key]
                
                # Determine threshold
                threshold = condition.get("value")
                
                # (Optional) Compare against another metric
                compare_metric = condition.get("compare_metric")
                if compare_metric and compare_metric in stock_context:
                    threshold = stock_context[compare_metric]
                    
                if threshold is None:
                    continue
                    
                # Perform Comparison
                operator = condition.get("operator", "==")
                is_match = False
                
                try:
                    actual_float = float(actual_value)
                    threshold_float = float(threshold)
                    
                    if operator == ">":
                        is_match = actual_float > threshold_float
                    elif operator == ">=":
                        is_match = actual_float >= threshold_float
                    elif operator == "<":
                        is_match = actual_float < threshold_float
                    elif operator == "<=":
                        is_match = actual_float <= threshold_float
                    elif operator == "==":
                        is_match = abs(actual_float - threshold_float) < 0.0001
                    elif operator == "!=":
                        is_match = abs(actual_float - threshold_float) > 0.0001
                except (ValueError, TypeError):
                    pass
                    
                if is_match:
                     triggered[signal["name"]] = {
                        "description": signal["description"],
                        "value": actual_value,
                        "threshold": threshold,
                        "operator": operator
                    }
        
        if not triggered:
            # If no specific signals matched, but we have tags, include them generically
            if stock_tags:
                return {"raw_tags": [t["name"] for t in stock_tags]}
            return {}
            
        return triggered

    async def _get_tags(self, session: AsyncSession, stock_code: str) -> Dict[str, Any]:
        """Fetch tags for a stock."""
        try:
            stmt = select(StockTagInfo.name, StockTagInfo.score, StockTagInfo.tag_type)\
                .join(StockTagRelation, StockTagInfo.id == StockTagRelation.tag_id)\
                .where(
                    StockTagRelation.stock_code == stock_code,
                    StockTagInfo.is_deleted == False
                )
            
            result = await session.execute(stmt)
            tags = []
            for name, score, tag_type in result.all():
                tags.append({
                    "name": name,
                    "score": float(score),
                    "type": tag_type
                })
            return {"tags": tags}
        except Exception as e:
            logger.error(f"Failed to get tags for {stock_code}: {e}")
            return {"tags": []}

    def _format_history_data(self, history: List[StockData]) -> str:
        """Format list of StockData to string representation."""
        if not history:
            return "No historical data."
        
        # Sort by timestamp ascending for display
        history = sorted(history, key=lambda x: x.timestamp)
        
        lines = ["Date, Open, High, Low, Close, Volume"]
        for d in history:
            date_str = d.timestamp.strftime("%Y-%m-%d")
            # Using price as Close. If High/Low/Open are 0, use price.
            close_price = float(d.price)
            high_price = float(d.high) if d.high > 0 else close_price
            low_price = float(d.low) if d.low > 0 else close_price
            open_price = float(d.open_price) if d.open_price > 0 else close_price
            
            lines.append(f"{date_str}, {open_price:.2f}, {high_price:.2f}, {low_price:.2f}, {close_price:.2f}, {d.volume}")
            
        return "\n".join(lines)

    def _build_prompt_context(
        self,
        account_status: Dict[str, Any],
        holdings: List[Dict[str, Any]],
        market_prices: Dict[str, float],
        news_section: str,
        template_text: Optional[str] = None,
        trigger_context: Optional[Dict[str, Any]] = None,
        skip_indicators: bool = False
    ) -> Dict[str, Any]:
        """
        Build the complete prompt context.
        """
        # Basic Variables
        runtime_minutes = account_status.get("runtime_minutes", 0)
        current_time_utc = datetime.utcnow().isoformat() + "Z"
        total_return_percent = account_status.get("total_return_percent", 0.0)
        available_cash = f"{account_status.get('available_cash', 0.0):.2f}"
        total_account_value = f"{account_status.get('total_account_value', 0.0):.2f}"
        
        holdings_detail = self._build_holdings_detail(holdings)
        market_prices_str = self._build_market_prices(market_prices)
        trigger_context_text = self._format_trigger_context(trigger_context)
        
        # K-line and Indicator Variables (Dynamic)
        kline_context = {}
        # if template_text and not skip_indicators:
        #    # This requires async data fetching, which should be done by the caller
        #    pass
        
        return {
            "trading_environment": "Platform: Chinese A-Share Market (Shanghai/Shenzhen)\nRules: T+1 Trading, 10% Price Limit",
            "runtime_minutes": runtime_minutes,
            "current_time_utc": current_time_utc,
            "total_return_percent": total_return_percent,
            "available_cash": available_cash,
            "total_account_value": total_account_value,
            "holdings_detail": holdings_detail,
            "market_prices": market_prices_str,
            "news_section": news_section,
            "trigger_context": trigger_context_text,
            "output_format": OUTPUT_FORMAT_JSON,
            **kline_context,
        }

    def _build_holdings_detail(self, holdings: List[Dict[str, Any]]) -> str:
        """Format holdings into a string."""
        if not holdings:
            return "No current holdings."
        
        lines = []
        for h in holdings:
            lines.append(f"{h.get('code')}: {h.get('volume')} shares @ {h.get('cost_price')} (Value: {h.get('market_value')})")
        return "\n".join(lines)

    def _build_market_prices(self, prices: Dict[str, float]) -> str:
        """Format market prices into a string."""
        if not prices:
            return "No market price data available."
        
        lines = []
        for code, price in prices.items():
            lines.append(f"{code}: {price}")
        return "\n".join(lines)

    def _format_trigger_context(self, trigger_context: Optional[Dict[str, Any]]) -> str:
        """Format trigger context."""
        if not trigger_context:
            return "Regular scheduled check."
        return json.dumps(trigger_context, ensure_ascii=False, indent=2)

    def _parse_kline_indicator_variables(self, template_text: str) -> Dict[str, Dict[str, Any]]:
        """
        Parse K-line and indicator variables from the template.
        """
        # K-line pattern: {600519_klines_1d}(20)
        kline_pattern = r'\{([0-9]{6})_klines_(\w+)\}(?:\((\d+)\))?'
        
        # Indicator pattern: {600519_MA_5}
        indicator_pattern = r'\{([0-9]{6})_(MA\d*|EMA\d*|RSI\d+|MACD|KDJ|BOLL)_(\w+)\}'
        
        grouped = {"klines": [], "indicators": []}
        
        for match in re.finditer(kline_pattern, template_text):
            stock_code, period, count = match.groups()
            grouped["klines"].append({
                "code": stock_code,
                "period": period,
                "count": int(count) if count else 20
            })
            
        for match in re.finditer(indicator_pattern, template_text):
            stock_code, indicator_type, period = match.groups()
            grouped["indicators"].append({
                "code": stock_code,
                "type": indicator_type,
                "period": period
            })
            
        return grouped

    async def _build_klines_and_indicators_context(
        self, 
        variable_groups: Dict[str, List[Any]],
        data_repo: StockDataRepository
    ) -> Dict[str, str]:
        """
        Fetch data and build context for K-lines and indicators.
        """
        context = {}
        
        # 1. Process K-lines
        for item in variable_groups["klines"]:
            code = item['code']
            count = item['count']
            
            # Fetch history
            history = await data_repo.find_by_code(code, limit=count)
            
            # Format history
            kline_str = self._format_history_data(history)
            key = f"{code}_klines_{item['period']}"
            context[key] = kline_str
            
        # 2. Process Indicators
        for item in variable_groups["indicators"]:
            code = item['code']
            indicator_type = item['type']
            period = item['period'] # e.g. '5' for MA5, 'default' for MACD
            
            # Determine needed history length
            # Ideally should fetch more to ensure accurate calculation (e.g. 50-100 days)
            needed_days = 100
            history = await data_repo.find_by_code(code, limit=needed_days)
            
            val = self._calculate_indicator(history, indicator_type, period)
            
            key = f"{code}_{indicator_type}_{period}"
            context[key] = val
            
        return context

    def _calculate_indicator(self, history: List[StockData], indicator_type: str, suffix: str) -> str:
        """
        Calculate technical indicator value.
        """
        if not history:
            return "N/A"
            
        # Convert to DataFrame
        # Sort by timestamp ascending
        data = sorted(history, key=lambda x: x.timestamp)
        df = pd.DataFrame([{
            'close': float(d.price),
            'high': float(d.high_price) if d.high_price is not None and d.high_price > 0 else float(d.price),
            'low': float(d.low_price) if d.low_price is not None and d.low_price > 0 else float(d.price),
            'open': float(d.open_price) if d.open_price is not None and d.open_price > 0 else float(d.price),
            'volume': float(d.volume) if d.volume is not None else 0
        } for d in data])
        
        try:
            val = None
            
            # 0. MACD (Check before MA because MACD starts with MA)
            if indicator_type == "MACD":
                if len(df) < 26: return "N/A"
                # Standard 12, 26, 9
                exp1 = df['close'].ewm(span=12, adjust=False).mean()
                exp2 = df['close'].ewm(span=26, adjust=False).mean()
                macd = exp1 - exp2
                signal = macd.ewm(span=9, adjust=False).mean()
                hist = macd - signal
                
                # Return formatted string: "DIF: x, DEA: y, MACD: z"
                last_macd = macd.iloc[-1]
                last_signal = signal.iloc[-1]
                last_hist = hist.iloc[-1]
                return f"DIF:{last_macd:.3f}, DEA:{last_signal:.3f}, MACD:{last_hist:.3f}"

            # 1. MA (Moving Average)
            elif indicator_type.startswith("MA"):
                period = int(suffix) if suffix.isdigit() else int(indicator_type[2:]) if indicator_type[2:].isdigit() else 5
                if len(df) < period: return "N/A"
                val = df['close'].rolling(window=period).mean().iloc[-1]
                
            # 2. EMA (Exponential Moving Average)
            elif indicator_type.startswith("EMA"):
                period = int(suffix) if suffix.isdigit() else int(indicator_type[3:]) if indicator_type[3:].isdigit() else 12
                if len(df) < period: return "N/A"
                val = df['close'].ewm(span=period, adjust=False).mean().iloc[-1]
                
            # 3. RSI (Relative Strength Index)
            elif indicator_type.startswith("RSI"):
                period = int(suffix) if suffix.isdigit() else 14
                if len(df) < period + 1: return "N/A"
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                rs = gain / loss
                # Avoid division by zero
                rs = rs.replace([np.inf, -np.inf], np.nan).fillna(0)
                val = 100 - (100 / (1 + rs)).iloc[-1]
                
            # 4. MACD
            # Moved to top to avoid conflict with MA check
            # elif indicator_type == "MACD":
            #    ...
                
            # 5. BOLL (Bollinger Bands)
            elif indicator_type == "BOLL":
                period = 20
                multiplier = 2
                if len(df) < period: return "N/A"
                sma = df['close'].rolling(window=period).mean()
                std = df['close'].rolling(window=period).std()
                upper = sma + (std * multiplier)
                lower = sma - (std * multiplier)
                
                last_up = upper.iloc[-1]
                last_mid = sma.iloc[-1]
                last_low = lower.iloc[-1]
                return f"UP:{last_up:.2f}, MID:{last_mid:.2f}, LOW:{last_low:.2f}"
                
            # 6. KDJ
            elif indicator_type == "KDJ":
                # Simple implementation (RSV based)
                if len(df) < 9: return "N/A"
                low_list = df['low'].rolling(window=9, min_periods=9).min()
                high_list = df['high'].rolling(window=9, min_periods=9).max()
                rsv = (df['close'] - low_list) / (high_list - low_list) * 100
                
                # Pandas doesn't have easy recursive calculation for KDJ, approximating with EMA
                # K = 2/3 * PrevK + 1/3 * RSV
                # D = 2/3 * PrevD + 1/3 * K
                # J = 3 * K - 2 * D
                # Use simple ewm for approximation or iterate
                k = 50
                d = 50
                for i in range(len(df)):
                    if pd.isna(rsv.iloc[i]): continue
                    k = (2/3) * k + (1/3) * rsv.iloc[i]
                    d = (2/3) * d + (1/3) * k
                    
                j = 3 * k - 2 * d
                return f"K:{k:.2f}, D:{d:.2f}, J:{j:.2f}"
        
            if val is not None and not pd.isna(val):
                return f"{val:.2f}"
            
            return "N/A"
            
        except Exception as e:
            logger.error(f"Error calculating indicator {indicator_type} for {suffix}: {e}")
            return "Error"

    async def call_ai_for_decision(
        self,
        account_status: Dict[str, Any],
        holdings: List[Dict[str, Any]],
        market_prices: Dict[str, float],
        news_section: str,
        template_text: str = STOCK_DEFAULT_PROMPT_TEMPLATE,
        trigger_context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Call AI model API to get trading decision.
        """
        context = self._build_prompt_context(
            account_status,
            holdings,
            market_prices,
            news_section,
            template_text=template_text,
            trigger_context=trigger_context,
        )
        
        prompt = template_text.format_map(SafeDict(context))
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
        }
        
        payload = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.config.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=120.0
                )
                response.raise_for_status()
                result = response.json()
                
                decision_text = result["choices"][0]["message"]["content"]
                
                # Try to find JSON in the response if it's mixed with text
                json_match = re.search(r'\{.*\}', decision_text, re.DOTALL)
                if json_match:
                    decision_text = json_match.group(0)
                
                decision = json.loads(decision_text)
                return decision
                
        except Exception as e:
            logger.error(f"AI Decision Call Failed: {e}", exc_info=True)
            return None

    def _extract_reasoning_content_safe(self, api_result: dict) -> str:
        """
        Extract reasoning content from API result (supports multiple providers).
        """
        # Logic from reference document
        msg = api_result.get("choices", [{}])[0].get("message", {})
        
        # OpenAI/DeepSeek/Qwen/Grok standard
        reasoning = msg.get("reasoning")
        if reasoning:
            return reasoning
            
        reasoning_content = msg.get("reasoning_content")
        if reasoning_content:
            return reasoning_content
            
        # Add other provider logic here if needed
        return ""
