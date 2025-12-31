# ALIGNMENT_INVESTIGATE_MISSING_TAGS_603992.md

## 需求理解
用户反馈股票 `603992.SH` 在系统中没有关联任何标签，但根据业务逻辑，所有股票池数据来自问财，至少应该包含：
1. **日期标签**：表示入选股票池的时间。
2. **三倍量标签**：如果满足成交量放大的条件。

用户要求检查问财数据和梳理逻辑，找出标签缺失的原因。

## 现状分析
1. **数据库状态**：
   - `stock_info` 表中存在 `603992.SH`。
   - `stock_tag_relations` 表中没有该股票的记录。
   - `wencai_crawl_batches` 表中应该包含该股票的原始抓取数据。
   - `wencai_service.py` 负责解析问财数据并打标签。

2. **关键逻辑**：
   - `wencai_service.py` 中的 `process_batch_data` 方法负责解析 `query_string` 和 `volume` 数据。
   - 逻辑判断：
     - 如果 `query_string` 包含 "成交量的2.9倍"，打 "三倍量" 标签。
     - 如果 `volume` >= 2.9，打 "三倍量" 标签。
     - 解析日期作为标签。

## 疑问澄清
1. `603992.SH` 在 `wencai_crawl_batches` 中的原始数据是什么样子的？
2. 是否存在数据解析错误或字段匹配失败？
3. `stock_tags_info` 表中是否已存在 "三倍量" 标签？如果不存在，是否创建失败？

## 任务边界
- 本次任务仅针对 `603992.SH` 标签缺失问题进行排查和修复。
- 修复范围可能涉及 `wencai_service.py` 或数据库数据修正。
