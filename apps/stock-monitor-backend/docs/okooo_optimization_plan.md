# Okooo 数据存储逻辑优化方案 (v2 - 2026-01-30 更新)

## 1. 问题分析

### 1.1 数据库字段与代码不匹配
- **字段名不一致**：代码中使用 `exchange_data`，但数据库表定义为 `exchanges_data`。
- **缺失字段**：数据库表包含 `handicap_data` (亚盘), `game_data` (联赛) 等字段，但代码模型中缺失。
- **导致结果**：入库保存时抛出 `Unknown column` 错误，导致数据无法保存。

### 1.2 日期字段 (match_date) 类型不一致
- **类型冲突**：代码此前将 `match_date` 处理为时间戳 (BigInteger)，但数据库定义为 `varchar(20)`。
- **查询失败**：使用时间戳范围查询字符串类型的日期字段导致查询结果为空。

### 1.3 数据未入库与重复插入
- `save-list-html` 接口曾缺少解析入库逻辑（已在 v1 修复）。
- 现有的 Upsert 逻辑需要确保使用 `match_id` 作为唯一键进行更新，避免重复插入。

## 2. 优化方案 (已执行)

### 2.1 修正数据模型 (`app/models/okooo_match.py`)
1.  **字段重命名**：`exchange_data` -> `exchanges_data`。
2.  **新增字段**：添加 `handicap_data`, `game_data` 等缺失字段。
3.  **类型变更**：将 `match_date` 从 `BigInteger` 修改为 `String(20)`，直接存储 "YYYY-MM-DD" 格式字符串。

### 2.2 调整存储逻辑 (`app/crawler/okooo/storage.py`)
1.  **直接存储日期字符串**：不再将 `date_str` 转换为时间戳，而是直接存入数据库。
2.  **增强 Upsert**：在更新现有记录时，强制更新 `match_date` 为传入的日期字符串。

### 2.3 调整查询逻辑 (`app/services/okooo_service.py`)
1.  **字符串匹配查询**：`get_db_matches` 方法改为使用 `OkoooMatch.match_date == date_str` 进行精确匹配，移除时间戳范围查询。
2.  **日期列表获取**：`get_matches_dates` 直接返回去重后的日期字符串列表。

## 3. 修改详情

### 3.1 `app/models/okooo_match.py`
```python
class OkoooMatch(Base):
    # ...
    match_date: Mapped[str] = mapped_column(String(20), comment="比赛日期", nullable=True)
    
    handicap_data: Mapped[str] = mapped_column(Text, comment="亚盘数据", nullable=True)
    game_data: Mapped[str] = mapped_column(Text, comment="联赛数据", nullable=True)
    exchanges_data: Mapped[str] = mapped_column(Text, comment="盈亏数据", nullable=True) # Renamed
    # ...
```

### 3.2 `app/crawler/okooo/storage.py`
```python
async def save_basic_match_info(self, match_data: Dict[str, Any], date_str: Optional[str] = None) -> bool:
    # ...
    final_date_str = date_str if date_str else inferred_date_str
    
    # Update logic
    if existing_match:
        if final_date_str:
            existing_match.match_date = final_date_str
    # ...
```

## 4. 预期效果
1.  **解决报错**：消除 `Unknown column 'exchange_data'` 错误。
2.  **数据准确**：`match_date` 字段准确存储为 "2026-01-30" 等格式，与前端传参一致。
3.  **查询正常**：修复后，前端请求列表和数据修复接口时，后端能正确从数据库查找到对应的比赛记录。
