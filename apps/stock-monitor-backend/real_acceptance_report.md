# Real Acceptance Report

## Daily Processing Stats

| Date | Processed | Passed | Failed | Errors |
|---|---|---|---|---|
| 2025-11-20 | 92 | 34 | 58 | 0 |
| 2025-11-21 | 58 | 28 | 30 | 0 |
| 2025-11-24 | 24 | 12 | 12 | 0 |
| 2025-11-25 | 52 | 13 | 39 | 0 |
| 2025-11-26 | 97 | 9 | 88 | 0 |
| 2025-11-27 | 99 | 38 | 61 | 0 |
| 2025-11-28 | 96 | 33 | 63 | 0 |
| 2025-12-01 | 96 | 35 | 61 | 0 |
| 2025-12-02 | 75 | 15 | 60 | 0 |
| 2025-12-03 | 93 | 43 | 50 | 0 |
| 2025-12-04 | 81 | 38 | 43 | 0 |
| 2025-12-05 | 98 | 49 | 49 | 0 |
| 2025-12-08 | N/A | N/A | N/A | (pymysql.err.OperationalError) (1205, 'Lock wait timeout exceeded; try restarting transaction')
[SQL: UPDATE pattern_stock_pool SET status=%s, updated_at=now() WHERE pattern_stock_pool.id = %s]
[parameters: [('observation', 73), ('core', 122), ('observation', 126), ('core', 153), ('core', 154), ('observation', 193), ('observation', 216), ('observation', 274)  ... displaying 10 of 16 total bound parameter sets ...  ('core', 408), ('core', 433)]]
(Background on this error at: https://sqlalche.me/e/20/e3q8) |
| 2025-12-09 | N/A | N/A | N/A | This Session's transaction has been rolled back due to a previous exception during flush. To begin a new transaction with this Session, first issue Session.rollback(). Original exception was: (raised as a result of Query-invoked autoflush; consider using a session.no_autoflush block if this flush is occurring prematurely)
(pymysql.err.OperationalError) (1205, 'Lock wait timeout exceeded; try restarting transaction')
[SQL: UPDATE stock_daily_temp SET status=%s, reject_reason=%s, updated_at=now() WHERE stock_daily_temp.id = %s]
[parameters: ('rejected', '评分不足', 256)]
(Background on this error at: https://sqlalche.me/e/20/e3q8) (Background on this error at: https://sqlalche.me/e/20/7s2a) |
| 2025-12-10 | 343 | 85 | 258 | 0 |

## 603601 Verification

| Date | Score | Rank | Status | Patterns |
|---|---|---|---|---|
| 2025-11-20 | 0 | -1 | Not in Pool | None |
| 2025-11-21 | 0 | -1 | Not in Pool | None |
| 2025-11-24 | 0 | -1 | Not in Pool | None |
| 2025-11-25 | 0 | -1 | Not in Pool | None |
| 2025-11-26 | 0 | -1 | Not in Pool | None |
| 2025-11-27 | 0 | -1 | Not in Pool | None |
| 2025-11-28 | 0 | -1 | Not in Pool | None |
| 2025-12-01 | 0 | -1 | Not in Pool | None |
| 2025-12-02 | 0 | -1 | Not in Pool | None |
| 2025-12-03 | 0 | -1 | Not in Pool | None |
| 2025-12-04 | 0 | -1 | Not in Pool | None |
| 2025-12-05 | 0 | -1 | Not in Pool | None |
| 2025-12-08 | N/A | N/A | N/A | N/A |
| 2025-12-09 | N/A | N/A | N/A | N/A |
| 2025-12-10 | 0 | -1 | Not in Pool | None |
