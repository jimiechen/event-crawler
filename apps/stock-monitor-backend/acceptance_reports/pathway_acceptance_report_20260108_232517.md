# Pathway量价计算系统验收报告

**生成时间**: 2026-01-08 23:25:17

## 测试概要

- **测试股票**: 603601.SH (再升科技)
- **测试周期**: 2025-11-20 至 2025-12-10
- **测试天数**: 0 天
## 每日评分和排名

| 日期 | 评分 | 排名 | 评分变化 |
|------|------|------|----------|

## 标签触发统计

| 标签名称 | 触发次数 |
|----------|----------|
| 3倍量 | {sum(1 for r in self.results if any(tag['name'] == '3倍量' for tag in r.get('tags', [])))} |
| 2倍量 | {sum(1 for r in self.results if any(tag['name'] == '2倍量' for tag in r.get('tags', [])))} |
| 阳包阴 | {sum(1 for r in self.results if any(tag['name'] == '阳包阴' for tag in r.get('tags', [])))} |
| 底分型 | {sum(1 for r in self.results if any(tag['name'] == '底分型' for tag in r.get('tags', [])))} |
| 5日地量 | {sum(1 for r in self.results if any(tag['name'] == '5日地量' for tag in r.get('tags', [])))} |
| 10日地量 | {sum(1 for r in self.results if any(tag['name'] == '10日地量' for tag in r.get('tags', [])))} |

## 验收结论

### ❌ 验收通过

Pathway量价计算系统存在以下问题：

1. 数据处理天数不足
2. 3倍量标签触发次数不足
