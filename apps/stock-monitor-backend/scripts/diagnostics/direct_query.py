import asyncio
import aiomysql

async def main():
    try:
        pool = await aiomysql.create_pool(
            host='192.168.1.6',
            port=3306,
            user='root',
            password='12345678',
            db='stock_monitor_new',
            autocommit=True
        )

        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                print("\n=== Today's Task Logs (2025-12-29) ===")
                await cur.execute("""
                    SELECT id, task_type, status, start_time, end_time, message
                    FROM sync_task_logs
                    WHERE DATE(start_time) = '2025-12-29'
                """)
                rows = await cur.fetchall()
                if not rows:
                    print("No task logs found for today.")
                for row in rows:
                    print(f"ID: {row[0]}, Type: {row[1]}, Status: {row[2]}, Start: {row[3]}, End: {row[4]}, Msg: {row[5]}")

                print("\n=== Scheduled Task Status ===")
                await cur.execute("""
                    SELECT id, name, task_type, last_run_at, last_run_status, next_run_at
                    FROM scheduled_task
                """)
                rows = await cur.fetchall()
                for row in rows:
                    print(f"Task: {row[1]}, Last Run: {row[3]}, Status: {row[4]}, Next: {row[5]}")



                print("\n=== Recent Sync Logs ===")
                await cur.execute("""
                    SELECT task_type, status, start_time, message
                    FROM sync_task_logs
                    ORDER BY start_time DESC
                    LIMIT 5
                """)
                rows = await cur.fetchall()
                for row in rows:
                    print(f"Type: {row[0]}, Status: {row[1]}, Start: {row[2]}, Msg: {row[3]}")

        pool.close()
        await pool.wait_closed()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
