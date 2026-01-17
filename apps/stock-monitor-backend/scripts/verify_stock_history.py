import asyncio
import os
import pandas as pd
from sqlalchemy import select
from app.database import db_manager
from app.models.stock_daily import StockScoreResult
from datetime import datetime
from decimal import Decimal

async def verify_stock_history(stock_code: str, wencai_dir: str):
    print(f"开始验收股票 {stock_code} 的历史表现...")
    
    # 1. 初始化数据库
    await db_manager.initialize()
    
    # 2. 获取数据库中的评分和排名历史
    print("正在查询数据库评分记录...")
    score_history = {}
    async with db_manager.get_session() as session:
        stmt = select(StockScoreResult).where(
            StockScoreResult.code == stock_code
        ).order_by(StockScoreResult.trade_date)
        result = await session.execute(stmt)
        records = result.scalars().all()
        
        for record in records:
            date_str = record.trade_date.strftime("%Y-%m-%d")
            score_history[date_str] = {
                "score": record.total_score,
                "ranking": record.ranking,
                "detail": record.rule_scores
            }
            
    # 3. 扫描问财 CSV 文件
    print(f"正在扫描问财数据目录: {wencai_dir}")
    wencai_history = {}
    files = sorted([f for f in os.listdir(wencai_dir) if f.startswith("wencai_") and f.endswith(".csv")])
    
    for filename in files:
        # 解析日期 wencai_20251120.csv
        try:
            date_part = filename.split("_")[1].split(".")[0]
            date_obj = datetime.strptime(date_part, "%Y%m%d")
            date_str = date_obj.strftime("%Y-%m-%d")
            
            file_path = os.path.join(wencai_dir, filename)
            df = pd.read_csv(file_path)
            
            # 检查股票是否在当天的列表中
            found = False
            
            # 尝试查找
            for col in df.columns:
                if "代码" in col or "code" in col.lower():
                    # 转换列为字符串并查找
                    matches = df[df[col].astype(str).str.contains(stock_code)]
                    if not matches.empty:
                        found = True
                        break
            
            wencai_history[date_str] = {
                "in_wencai": found,
                "file": filename
            }
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")

    # 4. 合并并输出结果
    all_dates = sorted(set(list(score_history.keys()) + list(wencai_history.keys())))
    
    print("\n" + "="*80)
    print(f"股票 {stock_code} 验收总览")
    print("="*80)
    print(f"{'日期':<12} | {'问财上榜':<10} | {'评分':<10} | {'排名':<10} | {'CSV文件'}")
    print("-" * 80)
    
    summary_data = []
    
    for date_str in all_dates:
        w_info = wencai_history.get(date_str, {"in_wencai": False, "file": "-"})
        s_info = score_history.get(date_str, {"score": "-", "ranking": "-", "detail": {}})
        
        in_wencai_mark = "✅" if w_info["in_wencai"] else "-"
        
        score_raw = s_info['score']
        if isinstance(score_raw, (int, float, Decimal)):
             score_val = f"{float(score_raw):.2f}"
        else:
             score_val = "-"
             
        rank_val = str(s_info['ranking']) if s_info['ranking'] is not None else "-"
        
        print(f"{date_str:<12} | {in_wencai_mark:<10} | {score_val:<10} | {rank_val:<10} | {w_info['file']}")
        
        summary_data.append({
            "date": date_str,
            "in_wencai": w_info["in_wencai"],
            "score": float(score_raw) if isinstance(score_raw, (int, float, Decimal)) else None,
            "ranking": s_info['ranking']
        })

    print("="*80)
    
    # 简单的趋势分析
    print("\n趋势分析:")
    present_dates = [d['date'] for d in summary_data if d['in_wencai']]
    print(f"1. 问财上榜次数: {len(present_dates)} 次")
    if present_dates:
        print(f"   上榜日期: {', '.join(present_dates)}")
        
    scored_dates = [d for d in summary_data if d['score'] is not None]
    if scored_dates:
        first_score = scored_dates[0]
        last_score = scored_dates[-1]
        print(f"2. 评分变化: {first_score['date']} ({first_score['score']}) -> {last_score['date']} ({last_score['score']})")
        
        max_score = max(scored_dates, key=lambda x: x['score'])
        print(f"   最高评分: {max_score['score']} ({max_score['date']})")

if __name__ == "__main__":
    import sys
    # 默认 603601，也可以从命令行参数获取
    code = "603601"
    if len(sys.argv) > 1:
        code = sys.argv[1]
        
    wencai_path = "/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/data/wencai"
    
    try:
        asyncio.run(verify_stock_history(code, wencai_path))
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Runtime error: {e}")
