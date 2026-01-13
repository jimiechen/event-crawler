"""
Mock工具函数 - 完全独立，不依赖任何原有代码
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import time


def generate_timestamp() -> str:
    """生成ISO格式时间戳"""
    return datetime.now(timezone.utc).isoformat()


class IDGenerator:
    """ID生成器"""
    def __init__(self):
        self._counter = 0
        self._lock = time.time()

    def next_id(self) -> int:
        """生成下一个ID"""
        self._counter += 1
        return int(time.time() * 1000) + self._counter


_id_generator = IDGenerator()


def generate_id() -> int:
    """生成唯一ID"""
    return _id_generator.next_id()


def parse_bool(value: Any, default: bool = True) -> bool:
    """解析布尔值"""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y", "on"}
    return bool(value)


def error_response(status_code: int, message: str) -> Dict[str, Any]:
    """生成错误响应"""
    return {
        "error": message,
        "status_code": status_code
    }


def success_response(message: str, **kwargs) -> Dict[str, Any]:
    """生成成功响应"""
    response = {
        "success": True,
        "message": message
    }
    response.update(kwargs)
    return response


def get_item_from_dict(data: Dict, key: Any, default: Any = None) -> Any:
    """从字典中获取项目"""
    if isinstance(key, int):
        return data.get(key, default)
    return data.get(str(key), default)


def update_item_in_dict(data: Dict, key: Any, value: Any) -> Dict:
    """更新字典中的项目"""
    if isinstance(key, int):
        data[key] = value
    else:
        data[str(key)] = value
    return data


def delete_item_from_dict(data: Dict, key: Any) -> bool:
    """从字典中删除项目"""
    if isinstance(key, int):
        if key in data:
            del data[key]
            return True
    else:
        if str(key) in data:
            del data[str(key)]
            return True
    return False


def filter_items(data: Dict, filters: Dict[str, Any]) -> list:
    """过滤数据"""
    filtered = []
    for item in data.values():
        match = True
        for key, value in filters.items():
            if key not in item or item[key] != value:
                match = False
                break
        if match:
            filtered.append(item)
    return filtered


def paginate_items(items: list, limit: Optional[int] = None, offset: Optional[int] = 0) -> Dict[str, Any]:
    """分页数据"""
    total = len(items)
    if offset:
        items = items[offset:]
    if limit:
        items = items[:limit]
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset
    }
