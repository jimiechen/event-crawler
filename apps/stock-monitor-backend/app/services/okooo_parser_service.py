#!/usr/bin/env python3
"""
Okooo比赛数据解析服务
支持按日期批量解析
"""
import os
import sys
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger

# 添加 scripts 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
from parse_okooo_mobile import OkoooParser

# 路径配置
BASE_DIR = "/Users/mac/StudioProjects/2026/open-citycloud-workspace/python/event-crawler/apps/stock-monitor-backend/data/okooo"
MATCHES_DIR = os.path.join(BASE_DIR, "matches")
PROCESSED_DIR = os.path.join(BASE_DIR, "processed")


class OkoooParserService:
    """Okooo解析服务"""

    def __init__(self):
        self.matches_dir = MATCHES_DIR
        self.processed_dir = PROCESSED_DIR
        self.parser = OkoooParser(self.matches_dir, self.processed_dir)
        os.makedirs(self.processed_dir, exist_ok=True)

    async def parse_daily_matches(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        """
        解析指定日期的所有比赛

        Args:
            date_str: 日期 (YYYY-MM-DD)，None则使用当天

        Returns:
            {"success": True, "date": "2026-02-02", "total": 50, "processed": 50, "failed": 0}
        """
        if date_str is None or date_str == "auto":
            date_str = datetime.now().strftime("%Y-%m-%d")

        date_dir = os.path.join(self.matches_dir, date_str)

        if not os.path.exists(date_dir):
            return {
                "success": False,
                "error": f"日期目录不存在: {date_dir}",
                "date": date_str
            }

        # 获取所有比赛ID
        match_ids = [d for d in os.listdir(date_dir)
                     if os.path.isdir(os.path.join(date_dir, d))]

        logger.info(f"📅 开始解析 {date_str} 的比赛数据，共 {len(match_ids)} 场")

        # 确保输出目录存在
        os.makedirs(os.path.join(self.processed_dir, date_str), exist_ok=True)

        # 批量解析
        processed = 0
        failed = 0
        failed_matches = []

        for match_id in match_ids:
            try:
                # 解析
                result = self.parser.process_date_match(date_str, match_id)

                # 保存
                output_path = self.parser.save_result(date_str, match_id, result)

                processed += 1
                logger.info(f"✅ [{processed}/{len(match_ids)}] {match_id} -> {output_path}")

            except Exception as e:
                failed += 1
                failed_matches.append({"match_id": match_id, "error": str(e)})
                logger.error(f"❌ [{failed}] {match_id} 解析失败: {e}")

        result = {
            "success": True,
            "date": date_str,
            "total": len(match_ids),
            "processed": processed,
            "failed": failed,
            "output_dir": os.path.join(self.processed_dir, date_str)
        }

        if failed_matches:
            result["failed_matches"] = failed_matches

        logger.info(f"📊 解析完成: {result}")
        return result

    async def parse_specific_match(self, date_str: str, match_id: str) -> Dict[str, Any]:
        """解析指定比赛"""
        try:
            result = self.parser.process_date_match(date_str, match_id)
            output_path = self.parser.save_result(date_str, match_id, result)

            return {
                "success": True,
                "match_id": match_id,
                "date": date_str,
                "output_path": output_path
            }
        except Exception as e:
            return {
                "success": False,
                "match_id": match_id,
                "date": date_str,
                "error": str(e)
            }

    def get_available_dates(self) -> List[str]:
        """获取所有可解析的日期列表"""
        if not os.path.exists(self.matches_dir):
            return []

        dates = []
        for item in os.listdir(self.matches_dir):
            item_path = os.path.join(self.matches_dir, item)
            if os.path.isdir(item_path) and re.match(r'\d{4}-\d{2}-\d{2}', item):
                dates.append(item)

        return sorted(dates, reverse=True)


# 全局服务实例
okooo_parser_service = OkoooParserService()
