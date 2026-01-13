#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
平台服务
处理平台配置的CRUD操作
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform import PlatformConfig

logger = logging.getLogger(__name__)


class PlatformService:
    """平台服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_platforms(self) -> List[Dict[str, Any]]:
        """
        获取所有平台列表
        """
        try:
            stmt = select(PlatformConfig)
            result = await self.db.execute(stmt)
            platforms = result.scalars().all()
            
            return [
                {
                    "id": p.id,
                    "platform_id": p.platform_id,
                    "name": p.name,
                    "domain": p.domain,
                    "login_url": p.login_url,
                    "home_url": p.home_url,
                    "verify_api": p.verify_api,
                    "verify_type": p.verify_type,
                    "verify_xpath": p.verify_xpath,
                    "verify_parser": p.verify_parser,
                    "icon": p.icon
                }
                for p in platforms
            ]
        except Exception as e:
            logger.error(f"获取平台列表失败: {e}")
            raise e

    async def get_platform_by_id(self, platform_id: str) -> Optional[Dict[str, Any]]:
        """
        根据platform_id获取平台配置
        """
        try:
            stmt = select(PlatformConfig).where(PlatformConfig.platform_id == platform_id)
            result = await self.db.execute(stmt)
            platform = result.scalar_one_or_none()
            
            if not platform:
                return None
            
            return {
                "id": platform.id,
                "platform_id": platform.platform_id,
                "name": platform.name,
                "domain": platform.domain,
                "login_url": platform.login_url,
                "home_url": platform.home_url,
                "verify_api": platform.verify_api,
                "verify_type": platform.verify_type,
                "verify_xpath": platform.verify_xpath,
                "verify_parser": platform.verify_parser,
                "icon": platform.icon
            }
        except Exception as e:
            logger.error(f"获取平台配置失败 {platform_id}: {e}")
            raise e

    async def create_platform(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建平台配置
        """
        try:
            platform = PlatformConfig(**data)
            self.db.add(platform)
            await self.db.commit()
            await self.db.refresh(platform)
            
            logger.info(f"创建平台配置成功: {platform.platform_id}")
            return {
                "id": platform.id,
                "platform_id": platform.platform_id,
                "name": platform.name
            }
        except Exception as e:
            logger.error(f"创建平台配置失败: {e}")
            await self.db.rollback()
            raise e

    async def init_default_platforms(self):
        """初始化默认平台配置"""
        default_platforms = [
            {
                "platform_id": "weibo",
                "name": "微博",
                "domain": "weibo.com",
                "login_url": "https://weibo.com/login.php",
                "home_url": "https://weibo.com",
                "verify_api": "https://weibo.com/ajax/statuses/config",
                "verify_type": "api",
                "icon": "https://weibo.com/favicon.ico"
            },
            {
                "platform_id": "xueqiu",
                "name": "雪球",
                "domain": "xueqiu.com",
                "login_url": "https://xueqiu.com/",
                "home_url": "https://xueqiu.com/",
                "verify_api": "https://xueqiu.com/statuses/original/show.json",
                "verify_type": "api",
                "icon": "https://assets.xueqiu.com/favicon.ico"
            },
            {
                "platform_id": "ths",
                "name": "同花顺",
                "domain": "10jqka.com.cn",
                "login_url": "http://upass.10jqka.com.cn/login",
                "home_url": "http://www.10jqka.com.cn/",
                "verify_api": "http://t.10jqka.com.cn/api.php?method=user.get_user_info",
                "verify_type": "api",
                "icon": "http://www.10jqka.com.cn/favicon.ico"
            },
            {
                "platform_id": "eastmoney",
                "name": "东方财富",
                "domain": "eastmoney.com",
                "login_url": "https://passport.eastmoney.com/passport/login",
                "home_url": "https://www.eastmoney.com/",
                "verify_api": "https://guba.eastmoney.com/check_login.aspx",
                "verify_type": "api",
                "icon": "https://www.eastmoney.com/favicon.ico"
            },
            {
                "platform_id": "bilibili",
                "name": "哔哩哔哩",
                "domain": "bilibili.com",
                "login_url": "https://passport.bilibili.com/login",
                "home_url": "https://www.bilibili.com/",
                "verify_api": "https://api.bilibili.com/x/web-interface/nav",
                "verify_type": "api",
                "icon": "https://www.bilibili.com/favicon.ico"
            },
            {
                "platform_id": "wencai",
                "name": "问财",
                "domain": "iwencai.com",
                "login_url": "http://www.iwencai.com/stockpick/search",
                "home_url": "http://www.iwencai.com/",
                "verify_api": "http://www.iwencai.com/stockpick/search",
                "verify_type": "html",
                "icon": "http://www.iwencai.com/favicon.ico"
            }
        ]
        
        for p_data in default_platforms:
            exists = await self.get_platform_by_id(p_data["platform_id"])
            if not exists:
                logger.info(f"初始化平台配置: {p_data['name']}")
                await self.create_platform(p_data)
            raise e

    async def update_platform(self, platform_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新平台配置
        """
        try:
            stmt = select(PlatformConfig).where(PlatformConfig.platform_id == platform_id)
            result = await self.db.execute(stmt)
            platform = result.scalar_one_or_none()
            
            if not platform:
                raise ValueError(f"平台 {platform_id} 不存在")
            
            for key, value in data.items():
                if hasattr(platform, key):
                    setattr(platform, key, value)
            
            await self.db.commit()
            await self.db.refresh(platform)
            
            logger.info(f"更新平台配置成功: {platform_id}")
            return {
                "id": platform.id,
                "platform_id": platform.platform_id,
                "name": platform.name
            }
        except Exception as e:
            logger.error(f"更新平台配置失败: {e}")
            await self.db.rollback()
            raise e

    async def init_default_platforms(self):
        """初始化默认平台配置"""
        default_platforms = [
            {
                "platform_id": "weibo",
                "name": "微博",
                "domain": "weibo.com",
                "login_url": "https://weibo.com/login.php",
                "home_url": "https://weibo.com",
                "verify_api": "https://weibo.com/ajax/statuses/config",
                "verify_type": "api",
                "icon": "https://weibo.com/favicon.ico"
            },
            {
                "platform_id": "bilibili",
                "name": "B站",
                "domain": "bilibili.com",
                "login_url": "https://passport.bilibili.com/login",
                "home_url": "https://www.bilibili.com",
                "verify_api": "https://api.bilibili.com/x/web-interface/nav",
                "verify_type": "api",
                "icon": "https://www.bilibili.com/favicon.ico"
            },
            {
                "platform_id": "douyin",
                "name": "抖音",
                "domain": "douyin.com",
                "login_url": "https://www.douyin.com/",
                "home_url": "https://www.douyin.com",
                "verify_api": "https://www.douyin.com/aweme/v1/web/user/profile/other/",
                "verify_type": "api",
                "icon": "https://lf1-cdn-tos.bytegoofy.com/goofy/ies/douyin_web/public/favicon.ico"
            },
            {
                "platform_id": "xiaohongshu",
                "name": "小红书",
                "domain": "xiaohongshu.com",
                "login_url": "https://www.xiaohongshu.com/explore",
                "home_url": "https://www.xiaohongshu.com",
                "verify_api": "https://edith.xiaohongshu.com/api/sns/web/v1/user/selfinfo",
                "verify_type": "api",
                "icon": "https://www.xiaohongshu.com/favicon.ico"
            },
            {
                "platform_id": "okooo",
                "name": "澳客",
                "domain": "okooo.com",
                "login_url": "https://www.okooo.com/login/",
                "home_url": "https://www.okooo.com",
                "verify_api": None,
                "verify_type": "dom",
                "verify_xpath": "//a[contains(@href, '/user/')]",
                "icon": "https://www.okooo.com/favicon.ico"
            },
            {
                "platform_id": "wencai",
                "name": "同花顺问财",
                "domain": "iwencai.com",
                "login_url": "http://www.iwencai.com/stockpick/search",
                "home_url": "http://www.iwencai.com/stockpick/search",
                "verify_api": None,
                "verify_type": "dom",
                "icon": "http://s.thsi.cn/js/iwencai/img/favicon.ico"
            }
        ]
        
        for p_data in default_platforms:
            exists = await self.get_platform_by_id(p_data["platform_id"])
            if not exists:
                logger.info(f"初始化平台配置: {p_data['name']}")
                await self.create_platform(p_data)

    async def delete_platform(self, platform_id: str) -> bool:
        """
        删除平台配置
        """
        try:
            stmt = select(PlatformConfig).where(PlatformConfig.platform_id == platform_id)
            result = await self.db.execute(stmt)
            platform = result.scalar_one_or_none()
            
            if not platform:
                return False
            
            await self.db.delete(platform)
            await self.db.commit()
            logger.info(f"删除平台配置成功: {platform_id}")
            return True
        except Exception as e:
            logger.error(f"删除平台配置失败 {platform_id}: {e}")
            await self.db.rollback()
            raise e
