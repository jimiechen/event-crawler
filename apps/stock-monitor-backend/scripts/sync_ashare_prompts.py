import sys
import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

# Add path to import app modules
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_root = os.path.dirname(current_dir)
sys.path.append(backend_root)

from app.models.arena_models import PromptTemplate, Base
from app.config.prompt_templates import STOCK_DEFAULT_PROMPT_TEMPLATE, OUTPUT_FORMAT_JSON

# Connection string for 192.168.1.6
DB_URL = "postgresql+asyncpg://chroma_user:chroma_password@192.168.1.6:5432/chroma_db"

PROMPTS = [
    {
        "key": "ashare_json_decision",
        "name": "A股个股决策(JSON)",
        "description": "针对单只A股股票进行决策，输出JSON格式",
        "is_system": True,
        "template_text": STOCK_DEFAULT_PROMPT_TEMPLATE.replace("{output_format}", OUTPUT_FORMAT_JSON.replace("{", "{{").replace("}", "}}")),
        "system_template_text": "你是一位专业的A股交易AI，严格按照JSON格式输出决策。"
    },
    {
        "key": "ashare_daily_review",
        "name": "A股每日复盘报告",
        "description": "基于A股市场数据进行每日复盘分析，生成市场情绪和策略建议",
        "is_system": True,
        "template_text": """# A股每日复盘报告 ({date})

## 1. 市场概况
- **上证指数**: {sh_index} (涨跌幅: {sh_change}%)
- **市场成交量**: {volume} (较昨日: {volume_change})
- **涨跌分布**: 涨停 {limit_up_count} 家 / 跌停 {limit_down_count} 家
- **北向资金**: {north_money}

## 2. 热门板块与概念
{hot_sectors}

## 3. 异动个股分析
{abnormal_stocks}

## 4. AI 市场情绪判断
请基于以上数据，分析当前市场情绪（贪婪/恐慌/中性），并给出明日的总体仓位建议和操作策略。

## 5. 重点关注
列出3-5只值得关注的标的及其逻辑。""",
        "system_template_text": "你是一位拥有20年经验的A股市场资深分析师，擅长结合技术面、资金面和政策面进行全方位研判。你的输出风格专业、客观且具有实操性。请以Markdown格式输出报告。"
    },
    {
        "key": "ashare_stock_analysis",
        "name": "A股个股深度诊断",
        "description": "针对单只A股股票进行技术面、资金面和基本面的深度诊断",
        "is_system": True,
        "template_text": """# 个股诊断报告: {stock_name} ({stock_code})

## 基础数据
- 现价: {price}
- 市盈率(TTM): {pe_ttm}
- 总市值: {total_mv}

## 技术面分析
- **均线系统**: MA5={ma5}, MA20={ma20}, MA60={ma60}
- **趋势判断**: 当前处于{trend_status}趋势
- **关键支撑/阻力**: 支撑位 {support_price} / 阻力位 {resistance_price}

## 资金面分析
- 主力资金净流入: {main_net_inflow}
- 量比: {vol_ratio}

## AI 综合决策
请综合上述信息，给出明确的操作建议：
1. **评级**: (强烈买入 / 谨慎买入 / 持有 / 减仓 / 卖出)
2. **核心逻辑**: 用简练的语言阐述理由。
3. **操作计划**: 如果买入，建议仓位是多少？止损位设在哪里？""",
        "system_template_text": "你是一位擅长量价分析和基本面挖掘的A股投资顾问。请基于提供的数据，为用户提供专业的个股诊断意见。输出必须包含明确的买卖评级。"
    }
]

async def sync_prompts():
    print(f"Connecting to {DB_URL}...")
    engine = create_async_engine(DB_URL, echo=False)
    
    # Create tables if they don't exist
    print("Creating tables if not exist...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print("Connected. Syncing A-Share prompts...")
        
        for p in PROMPTS:
            stmt = select(PromptTemplate).where(PromptTemplate.key == p["key"])
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                print(f"Updating prompt: {p['name']}")
                existing.name = p["name"]
                existing.description = p["description"]
                existing.template_text = p["template_text"]
                existing.system_template_text = p["system_template_text"]
                # Don't overwrite created_by or other fields
            else:
                print(f"Creating prompt: {p['name']}")
                new_prompt = PromptTemplate(
                    key=p["key"],
                    name=p["name"],
                    description=p["description"],
                    template_text=p["template_text"],
                    system_template_text=p["system_template_text"],
                    is_system=p["is_system"],
                    is_deleted="false",
                    created_by="system"
                )
                session.add(new_prompt)
        
        await session.commit()
        print("✅ Prompts sync complete.")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(sync_prompts())
