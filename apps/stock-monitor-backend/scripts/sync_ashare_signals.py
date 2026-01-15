import sys
import os
import asyncio
import json
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

# Add path to import app modules
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_root = os.path.dirname(current_dir)
sys.path.append(backend_root)

from app.models.arena_models import SignalDefinition, SignalPool, Base

# Connection string for 192.168.1.6
DB_URL = "postgresql+asyncpg://chroma_user:chroma_password@192.168.1.6:5432/chroma_db"

SIGNALS = [
    {
        "signal_name": "MA5_CROSS_MA20_UP",
        "description": "MA5上穿MA20形成金叉，短期趋势走强",
        "signal_type": "technical",
        "trigger_condition": {
            "indicator": "MA_CROSS",
            "fast": 5,
            "slow": 20,
            "operator": "CROSS_UP"
        },
        "parameters": {"window_fast": 5, "window_slow": 20},
        "enabled": True
    },
    {
        "signal_name": "VOL_SPIKE_2X",
        "description": "成交量突破5日均量的2倍，资金流入迹象明显",
        "signal_type": "technical",
        "trigger_condition": {
            "indicator": "VOL_SPIKE",
            "ma_window": 5,
            "multiplier": 2.0
        },
        "parameters": {"ma_window": 5, "multiplier": 2.0},
        "enabled": True
    },
    {
        "signal_name": "RSI_OVERSOLD_30",
        "description": "RSI(14)低于30，进入超卖区，存在反弹需求",
        "signal_type": "technical",
        "trigger_condition": {
            "indicator": "RSI",
            "window": 14,
            "operator": "<",
            "value": 30
        },
        "parameters": {"window": 14, "threshold": 30},
        "enabled": True
    },
    {
        "signal_name": "MACD_GOLDEN_CROSS",
        "description": "MACD DIF线上穿DEA线，形成金叉",
        "signal_type": "technical",
        "trigger_condition": {
            "indicator": "MACD_CROSS",
            "fast": 12,
            "slow": 26,
            "signal": 9,
            "operator": "CROSS_UP"
        },
        "parameters": {"fast": 12, "slow": 26, "signal": 9},
        "enabled": True
    }
]

POOLS = [
    {
        "pool_name": "ashare_strong_bull_v1",
        "description": "A股强势股筛选池V1：结合均线金叉、量能爆发和MACD信号",
        "signal_names": ["MA5_CROSS_MA20_UP", "VOL_SPIKE_2X", "MACD_GOLDEN_CROSS"],
        "symbols": [],
        "logic": "OR",
        "enabled": True
    }
]

async def sync_signals():
    print(f"Connecting to {DB_URL}...")
    engine = create_async_engine(DB_URL, echo=False)
    
    # Create tables if they don't exist
    print("Creating tables if not exist...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print("Connected. Syncing A-Share signals...")
        
        signal_id_map = {}

        # 1. Sync Signals
        for s in SIGNALS:
            stmt = select(SignalDefinition).where(SignalDefinition.signal_name == s["signal_name"])
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                print(f"Updating signal: {s['signal_name']}")
                existing.description = s["description"]
                # existing.signal_type = s["signal_type"]
                existing.trigger_condition = s["trigger_condition"]
                # existing.parameters = s["parameters"]
                existing.enabled = s["enabled"]
                signal_id_map[s["signal_name"]] = existing.id
            else:
                print(f"Creating signal: {s['signal_name']}")
                new_signal = SignalDefinition(
                    signal_name=s["signal_name"],
                    description=s["description"],
                    # signal_type=s["signal_type"],
                    trigger_condition=s["trigger_condition"],
                    # parameters=s["parameters"],
                    enabled=s["enabled"]
                )
                session.add(new_signal)
                await session.flush() # Flush to get ID
                signal_id_map[s["signal_name"]] = new_signal.id
        
        # 2. Sync Pools
        for p in POOLS:
            stmt = select(SignalPool).where(SignalPool.pool_name == p["pool_name"])
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            # Resolve signal names to IDs
            signal_ids = []
            for name in p["signal_names"]:
                if name in signal_id_map:
                    signal_ids.append(signal_id_map[name])
                else:
                    # Try to find in DB if not in current batch
                    stmt_sig = select(SignalDefinition).where(SignalDefinition.signal_name == name)
                    res_sig = await session.execute(stmt_sig)
                    sig_obj = res_sig.scalar_one_or_none()
                    if sig_obj:
                        signal_ids.append(sig_obj.id)
                    else:
                        print(f"Warning: Signal '{name}' not found for pool '{p['pool_name']}'")

            if existing:
                print(f"Updating pool: {p['pool_name']}")
                # existing.description = p["description"]
                existing.signal_ids = signal_ids
                existing.logic = p["logic"]
                existing.enabled = p["enabled"]
            else:
                print(f"Creating pool: {p['pool_name']}")
                new_pool = SignalPool(
                    pool_name=p["pool_name"],
                    # description=p["description"],
                    signal_ids=signal_ids,
                    logic=p["logic"],
                    enabled=p["enabled"]
                )
                session.add(new_pool)

        await session.commit()
        print("✅ Signals and Pools sync complete.")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(sync_signals())
