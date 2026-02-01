import asyncio
import os
import sys

# Add current directory to path so we can import app
sys.path.append(os.getcwd())

from app.database import DatabaseManager
from app.models.okooo_match import OkoooMatch
from sqlalchemy import select

async def main():
    # Try to get DB URL from env or use default
    db_url = os.getenv("DATABASE_URL", "mysql+aiomysql://root:123456@localhost:3306/stock_monitor")
    print(f"Connecting to DB: {db_url}")
    
    db_manager = DatabaseManager()
    # Need to manually set config or use default (which reads env)
    # Or just use initialize() which uses get_config()
    
    try:
        await db_manager.initialize()
    except Exception as e:
        print(f"Failed to connect to DB: {e}")
        return
    
    async with db_manager.get_session() as session:
        # Check JCZQ
        print("\n--- Checking JCZQ match_no ---")
        stmt = select(OkoooMatch).where(OkoooMatch.match_type == 'jczq')
        result = await session.execute(stmt)
        jczq_matches = result.scalars().all()
        
        total_jczq = len(jczq_matches)
        missing_no_jczq = [m for m in jczq_matches if not m.match_no]
        
        print(f"Total JCZQ matches: {total_jczq}")
        print(f"JCZQ matches missing match_no: {len(missing_no_jczq)}")
        if missing_no_jczq:
            print("Sample missing IDs:", [m.match_id for m in missing_no_jczq[:5]])
        elif total_jczq > 0:
            print("Sample valid match_no:", jczq_matches[0].match_no)

        # Check SFC
        print("\n--- Checking SFC match_no ---")
        stmt = select(OkoooMatch).where(OkoooMatch.match_type == 'sfc')
        result = await session.execute(stmt)
        sfc_matches = result.scalars().all()
        
        total_sfc = len(sfc_matches)
        valid_format_sfc = [m for m in sfc_matches if m.match_no and "期" in m.match_no]
        
        print(f"Total SFC matches: {total_sfc}")
        print(f"SFC matches with '期' in match_no: {len(valid_format_sfc)}")
        if valid_format_sfc:
            print("Sample SFC match_no:", valid_format_sfc[0].match_no)
        
        if total_sfc > 0 and not valid_format_sfc:
            print("WARNING: SFC matches exist but match_no format seems wrong (expected '第XXXX期 001')")
            if sfc_matches[0].match_no:
                print("Sample SFC match_no:", sfc_matches[0].match_no)
            else:
                print("Sample SFC match_no is None")

        # Check BJDC
        print("\n--- Checking BJDC match_no ---")
        stmt = select(OkoooMatch).where(OkoooMatch.match_type == 'bjdc')
        result = await session.execute(stmt)
        bjdc_matches = result.scalars().all()
        print(f"Total BJDC matches: {len(bjdc_matches)}")
        if bjdc_matches:
             print("Sample BJDC match_no:", bjdc_matches[0].match_no)


        # Check Field Alignment (Comprehensive)
        print("\n--- Checking Field Alignment ---")
        
        # Get all column names
        columns = OkoooMatch.__table__.columns.keys()
        print(f"Total Columns in DB: {len(columns)}")
        
        # Check for empty columns across the table
        # We'll check a sample of rows (e.g., 100) or all if small
        stmt = select(OkoooMatch).limit(100)
        result = await session.execute(stmt)
        rows = result.scalars().all()
        
        if not rows:
            print("Table is empty.")
        else:
            empty_cols = []
            for col in columns:
                has_value = False
                for row in rows:
                    val = getattr(row, col)
                    if val is not None and val != "":
                        has_value = True
                        break
                if not has_value:
                    empty_cols.append(col)
            
            if empty_cols:
                print(f"WARNING: The following columns appear to be empty in the first {len(rows)} rows:")
                for col in empty_cols:
                    print(f"  - {col}")
            else:
                print(f"All columns have data in at least some rows (checked {len(rows)} rows).")

            # Print Sample Data Detail
            print("\nSample Row Data:")
            sample = rows[0]
            for col in columns:
                val = getattr(sample, col)
                # Truncate long values
                val_str = str(val)
                if len(val_str) > 50:
                    val_str = val_str[:47] + "..."
                print(f"  {col}: {val_str}")

if __name__ == "__main__":
    asyncio.run(main())
