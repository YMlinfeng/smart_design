# app/main.py
import os
import sys
import logging

# 配置logging，确保输出到stderr（gunicorn会捕获stderr）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stderr  # 输出到stderr，gunicorn会捕获
)

logger = logging.getLogger(__name__)

logger.info(f"[MODULE] ========== main.py 模块被导入, PID={os.getpid()} ==========")

from fastapi import FastAPI
from app.views import api_router
from app.mq import mq_runner  # 👈 MQ 运行器（单例）

logger.info("[MODULE] mq_runner 已导入")

app = FastAPI()
app.include_router(api_router)

@app.on_event("startup")
async def _startup():
    logger.info("=" * 60)
    logger.info("[STARTUP] ========== FastAPI应用启动中 ==========")
    logger.info(f"[STARTUP] 进程ID: {os.getpid()}")
    logger.info(f"[STARTUP] mq_runner状态: {mq_runner}")
    logger.info(f"[STARTUP] mq_runner类型: {type(mq_runner)}")
    try:
        await mq_runner.start()  # 启动MQ消费者
        logger.info("[STARTUP] ========== MQ消费者启动成功 ==========")
    except Exception as e:
        logger.error("=" * 60)
        logger.error("[STARTUP] ========== MQ消费者启动失败 ==========")
        logger.error(f"[STARTUP] 错误信息: {repr(e)}")
        import traceback
        logger.error(f"[STARTUP] 详细错误:\n{traceback.format_exc()}")
        logger.error("=" * 60)
        # 不抛出异常，让HTTP服务继续运行
    logger.info("=" * 60)

@app.on_event("shutdown")
async def _shutdown():
    logger.info("[SHUTDOWN] 正在关闭MQ消费者...")
    await mq_runner.stop()
    logger.info("[SHUTDOWN] MQ消费者已关闭")

if __name__ == "__main__":
    import uvicorn
    logger.info(f"[MAIN] 主进程启动, PID={os.getpid()}")
    logger.info(f"[MAIN] 使用workers=4模式启动")
    uvicorn.run("app.main:app", host="0.0.0.0", port=7754, workers=4, reload=False)
