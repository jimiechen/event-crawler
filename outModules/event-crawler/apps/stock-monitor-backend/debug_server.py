import asyncio
import sys
import traceback
import linecache
import uvicorn
from app.main import app
from loguru import logger

async def monitor_loop():
    logger.info("🕵️ 启动事件循环监控...")
    while True:
        start_time = asyncio.get_running_loop().time()
        await asyncio.sleep(1)
        end_time = asyncio.get_running_loop().time()
        
        lag = end_time - start_time - 1
        if lag > 0.1:  # 如果延迟超过100ms
            logger.warning(f"⚠️ 事件循环延迟: {lag:.3f}s")
            
        if lag > 1.0:  # 如果延迟严重，打印任务堆栈
            logger.error("🚨 检测到严重阻塞！正在转储任务堆栈...")
            dump_tasks()

def dump_tasks():
    try:
        tasks = asyncio.all_tasks()
        logger.info(f"当前共有 {len(tasks)} 个任务")
        
        for task in tasks:
            if task.done():
                continue
                
            # 获取任务的协程
            coro = task.get_coro()
            if coro is None:
                continue
                
            logger.info(f"Task: {task.get_name()}")
            
            # 打印堆栈
            stack = task.get_stack()
            if stack:
                summary = traceback.StackSummary.extract(
                    traceback.walk_stack(stack[-1]), limit=None
                )
                for line in summary.format():
                    logger.info(line.strip())
            else:
                logger.info("  (No stack available)")
    except Exception as e:
        logger.error(f"转储堆栈失败: {e}")

@app.on_event("startup")
async def start_monitor():
    asyncio.create_task(monitor_loop())

if __name__ == "__main__":
    # 使用uvloop如果可用
    # try:
    #     import uvloop
    #     asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    # except ImportError:
    #     pass

    uvicorn.run(app, host="0.0.0.0", port=8003, log_level="info")
