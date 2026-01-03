# DUPLICATE STOCKS INVESTIGATION & FIX REPORT

## Problem Description
User reported a data discrepancy where:
- Stock `603977` (from Wencai crawler) had historical tags (e.g., `2025-12-11`).
- Stock `603977.SH` (manually added) had new tags (`2025-12-25`, `三倍量`).
- The Stock Monitor, which watches `603977`, could not see the new tags because they were attached to `603977.SH`.

## Root Cause Analysis
1.  **Inconsistent Stock Code Formats**:
    - **Wencai Service**: Automatically strips suffixes (e.g., `603977.SH` -> `603977`) when parsing HTML.
    - **Manual Add API (`/add-custom-stock`)**: Was saving codes exactly as input (e.g., `603977.SH`), retaining the suffix.
    - **Monitor Service**: Uses 6-digit codes (e.g., `603977`).
2.  **Data Split**:
    - This caused two separate entries in the database for the same physical stock.
    - Tags were fragmented across these two entries.

## Resolution
1.  **Code Fix**:
    - Modified `app/api/test_tool_controller.py` to automatically normalize stock codes (remove `.SH`/`.SZ` suffixes) before saving.
    - This ensures all future manual additions match the system standard (6-digit).

2.  **Data Migration**:
    - Created and executed a migration script to repair existing data.
    - Identified all stocks with suffixes in `wencai_stocks` (e.g., `603977.SH`, `000506.SZ`).
    - Merged them into their 6-digit counterparts:
        - Updated `wencai_stocks` to point to 6-digit codes.
        - Updated `stock_tag_relations` to point to 6-digit codes.
        - Updated `stock_concepts` to point to 6-digit codes.
        - Removed the now-redundant suffixed entries.

## Verification Results
- **Before**: `603977` had only historical tags; `603977.SH` had only new tags.
- **After**: `603977` now possesses **ALL** tags:
    - `2025-12-11` (from original crawl)
    - `2025-12-18` (from original crawl)
    - `2025-12-23` (from original crawl)
    - `2025-12-25` (from manual addition)
    - `三倍量` (from manual addition)
- **Status**: Validated via database inspection. The `603977.SH` entry no longer exists, and `603977` is complete.

## Next Steps
- None. The issue is resolved and prevented for the future.
