import pymysql
import os
import sys
import itertools
from decimal import Decimal
from dotenv import load_dotenv

# Load environment variables
env_path = "/Users/mac/ok-mcp/app/stock-monitor-backend/.env"
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"Loaded .env from {env_path}")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_DATABASE = os.getenv("DB_DATABASE", "stock_monitor")

def is_valid_permutation(prev, open_p, high, low, curr, target_chg):
    # 1. Verify Change Percent
    # Avoid division by zero
    if prev == 0:
        return False
        
    calc_chg = (float(curr) - float(prev)) / float(prev) * 100
    
    # Tolerance for float comparison (0.05%)
    if abs(calc_chg - float(target_chg)) > 0.05:
        return False
        
    # 2. Verify High/Low Logic
    # High must be >= Open and Curr
    # Low must be <= Open and Curr
    if high < open_p or high < curr:
        return False
    if low > open_p or low > curr:
        return False
        
    # High must be >= Low
    if high < low:
        return False
        
    return True

def fix_row(row_id, values, target_chg):
    # values is a list of 5 Decimals
    # Try all permutations
    # Mapping: (prev, open, high, low, curr)
    
    valid_perms = []
    
    # Optimization: Sort values to handle duplicates or consistent processing? No need.
    
    for perm in itertools.permutations(values):
        prev, open_p, high, low, curr = perm
        if is_valid_permutation(prev, open_p, high, low, curr, target_chg):
            valid_perms.append(perm)
            
    if not valid_perms:
        return None # No solution found
        
    # If multiple solutions?
    # e.g. Open = Curr, then High/Low are same...
    # Just pick the first one, or check if they are effectively the same assignment?
    # If values are identical, permutations are identical in value.
    # Set of unique value tuples:
    unique_solutions = sorted(list(set(valid_perms)))
    
    if len(unique_solutions) == 1:
        return unique_solutions[0]
    
    # If multiple unique solutions, we might have ambiguity.
    # e.g. if Chg=0, Prev=Curr. If Open is also same...
    # Usually we prefer High to be strictly Max if possible?
    # But High >= Max is the rule.
    # Let's pick the one where High is maximized? (Usually High IS the max of the set)
    # And Low is minimized.
    
    best_sol = None
    best_score = -1
    
    for sol in unique_solutions:
        prev, open_p, high, low, curr = sol
        # Score: High - Low (Range). We want the widest range?
        # Actually, High should be the Max of the observed set usually.
        # But if we have {10, 10, 10, 10, 10}, Range is 0.
        # If we have {10, 11, 12, 10, 11}. Max=12.
        # If High is assigned 11, it's invalid (must be >= 12).
        # So our validation logic already enforces High >= Open and High >= Curr.
        # But High must also be >= Prev? Not necessarily (Gap down).
        # But High must be >= Low.
        
        # In most cases, unique_solutions will be 1 if values are distinct.
        # If multiple, pick the first one.
        pass
        
    return unique_solutions[0]

def main():
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_DATABASE,
            cursorclass=pymysql.cursors.DictCursor
        )
        print("✅ Connected successfully.")
        
        with connection.cursor() as cursor:
            print("🔄 Fetching data...")
            cursor.execute("SELECT id, prev_close, open_price, high, low, current_price, change_percent FROM tonghuashun_stocks")
            rows = cursor.fetchall()
            print(f"Found {len(rows)} rows to process.")
            
            updates = []
            failed_count = 0
            
            for row in rows:
                if row['change_percent'] is None:
                    continue
                    
                values = [
                    row['prev_close'],
                    row['open_price'],
                    row['high'],
                    row['low'],
                    row['current_price']
                ]
                
                # Check for None values
                if any(v is None for v in values):
                    continue
                    
                solution = fix_row(row['id'], values, row['change_percent'])
                
                if solution:
                    new_prev, new_open, new_high, new_low, new_curr = solution
                    
                    # Only update if changed (to save DB ops, though batch update ignores this check usually)
                    # But we construct the update tuple anyway.
                    updates.append((
                        new_prev, new_open, new_high, new_low, new_curr,
                        row['id']
                    ))
                else:
                    failed_count += 1
                    # print(f"❌ Could not fix row {row['id']} (Code: {row.get('code')}, Chg: {row['change_percent']}) Values: {values}")
            
            print(f"✅ Prepared {len(updates)} updates. Failed to resolve: {failed_count}")
            
            if updates:
                print("Executing batch update...")
                batch_size = 1000
                for i in range(0, len(updates), batch_size):
                    batch = updates[i:i+batch_size]
                    cursor.executemany("""
                        UPDATE tonghuashun_stocks 
                        SET prev_close=%s, open_price=%s, high=%s, low=%s, current_price=%s 
                        WHERE id=%s
                    """, batch)
                    connection.commit()
                    print(f"   Processed {min(i+batch_size, len(updates))}/{len(updates)} rows...")
                print("✅ Smart repair complete!")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()

if __name__ == "__main__":
    main()
