"""
读取问财股票池数据（支持CSV格式）
"""
import os
import csv
from pathlib import Path

def load_wencai_stocks(wencai_dir: str):
    """
    读取问财股票池数据（支持CSV格式）
    
    Args:
        wencai_dir: 问财数据目录
    
    Returns:
        股票代码列表
    """
    wencai_path = Path(wencai_dir)
    
    if not wencai_path.exists():
        print(f"❌ 问财数据目录不存在: {wencai_dir}")
        return []
    
    # 查找所有CSV文件
    csv_files = list(wencai_path.glob("*.csv"))
    
    if not csv_files:
        print(f"❌ 未找到问财数据文件")
        return []
    
    # 读取所有股票代码
    stock_codes = set()
    for csv_file in csv_files:
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                # 读取每一行，提取股票代码
                for row in reader:
                    # 尝试多个可能的字段名
                    code = None
                    for field in ['stock_code', 'code', '股票代码']:
                        if field in row and row[field]:
                            code = row[field].strip()
                            break
                    
                    if code:
                        stock_codes.add(code)
        except Exception as e:
            print(f"⚠️ 读取文件失败 {csv_file}: {e}")
    
    print(f"✅ 从问财数据加载 {len(stock_codes)} 只股票")
    
    return sorted(list(stock_codes))

if __name__ == '__main__':
    import os
    # 使用绝对路径
    wencai_dir = '/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/data/wencai'
    
    stocks = load_wencai_stocks(wencai_dir)
    
    print(f"\n📊 股票池（前20只）:")
    for i, code in enumerate(stocks[:20], 1):
        print(f"   {i}. {code}")
