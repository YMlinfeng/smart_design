import time
# app/mq.py
import os, json, asyncio, aio_pika, aiofiles, httpx, sys, logging
from datetime import datetime
from zoneinfo import ZoneInfo

# 配置logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stderr
)

logger = logging.getLogger(__name__)

logger.info(f"[MQ_MODULE] ========== mq.py 模块被导入, PID={os.getpid()} ==========")

from app.config import RABBITMQ_URL, QUEUE_NAME, callback_url, callback_toB_url
# from app.utils.agent import DesignAssistant

# 向量数据库相关
from langchain_community.vectorstores.faiss import FAISS
from langchain_community.embeddings.dashscope import DashScopeEmbeddings
from app.utils.constants import EMBED
from app.faiss.QA_searcher import QASearcher

MQ_CONCURRENCY = int(os.getenv("MQ_CONCURRENCY", "8"))
HEARTBEAT_SEC = int(os.getenv("RABBIT_HEARTBEAT", "30"))
TASK_TIMEOUT_SEC = int(os.getenv("MQ_TASK_TIMEOUT", "120"))  # 每条消息处理超时

# 加载Faiss向量库
logger.info('==========加载Faiss向量库==========')
start_time = time.time()

app_use_qa_searcher = QASearcher(faiss_path='app/faiss/QA_test')
knowledge_faiss=FAISS.load_local(
            'app/faiss/knowledge',  # 向量数据库路径
            embeddings=EMBED,  # 嵌入模型
            allow_dangerous_deserialization=True  # 允许反序列化（安全考虑）
        )
end_time = time.time()
logger.info(f'加载Faiss向量库耗时: {end_time - start_time} 秒')
logger.info('==========加载Faiss向量库成功==========')

app_use_faiss = FAISS.load_local(
    'app/faiss/app_use',
    embeddings=EMBED,
    allow_dangerous_deserialization=True
)


class MissingFieldError(Exception):
    """业务必填字段缺失时抛出的异常"""

    def __init__(self, field: str, payload: dict):
        super().__init__(f"missing required field: {field}")
        self.field = field
        self.payload = payload


class MQRunner:
    def __init__(self):
        logger.info(f"[MQRunner] 初始化MQRunner实例, PID={os.getpid()}")
        self._conn: aio_pika.RobustConnection | None = None
        self._ch: aio_pika.RobustChannel | None = None
        self._queue: aio_pika.RobustQueue | None = None
        self._sem = asyncio.Semaphore(MQ_CONCURRENCY)
        self._consumer_tag: str | None = None
        self._bg_tasks: set[asyncio.Task] = set()
        self._stopping = False
        self._http: httpx.AsyncClient | None = None
        logger.info(f"[MQRunner] MQRunner初始化完成, concurrency={MQ_CONCURRENCY}")

    async def start(self):
        # 1) 建立 robust 连接（带心跳）
        logger.info('==========启动mq==========')
        logger.info(f"[MQ] 连接参数: RABBITMQ_URL={RABBITMQ_URL}, QUEUE_NAME={QUEUE_NAME}")
        try:
            self._conn = await aio_pika.connect_robust(
                RABBITMQ_URL,
                heartbeat=HEARTBEAT_SEC,
                timeout=10,
                client_properties={"connection_name": "mq_consumer"}
            )
            logger.info("[MQ] RabbitMQ连接建立成功")
        except Exception as e:
            logger.error(f"[MQ] RabbitMQ连接失败: {repr(e)}")
            import traceback
            logger.error(f"[MQ] 连接错误详情: {traceback.format_exc()}")
            raise
        
        # 2) 新开 channel & qos
        try:
            self._ch = await self._conn.channel()
            await self._ch.set_qos(prefetch_count=MQ_CONCURRENCY)
            logger.info(f"[MQ] Channel创建成功, prefetch_count={MQ_CONCURRENCY}")
        except Exception as e:
            logger.error(f"[MQ] Channel创建失败: {repr(e)}")
            raise

        # 3) 声明 queue（robust 对象）
        try:
            self._queue = await self._ch.declare_queue(QUEUE_NAME, durable=True)
            logger.info(f"[MQ] Queue声明成功: {QUEUE_NAME}")
        except Exception as e:
            logger.error(f"[MQ] Queue声明失败: {repr(e)}")
            raise
        
        # 4) 复用 http 客户端
        self._http = httpx.AsyncClient(timeout=30)
        logger.info("[MQ] HTTP客户端创建成功")
        
        # 5) 用 consume（robust 会在断线后自动恢复）
        try:
            self._consumer_tag = await self._queue.consume(self._on_message, no_ack=False)
            logger.info(f"[MQ] 消费者注册成功: consumer_tag={self._consumer_tag}")
        except Exception as e:
            logger.error(f"[MQ] 消费者注册失败: {repr(e)}")
            raise

        logger.info(f"[MQ] connected queue={QUEUE_NAME} concurrency={MQ_CONCURRENCY} heartbeat={HEARTBEAT_SEC}")
        logger.info('==========启动mq成功==========')
        logger.info(f"[MQ] 当前进程ID: {os.getpid()}")
        logger.info(f"[MQ] 消费者已就绪，等待消息...")
    async def stop(self):
        logger.info('==========停止mq==========')
        self._stopping = True
        # 先取消消费，避免新任务进来
        if self._queue and self._consumer_tag:
            try:
                await self._queue.cancel(self._consumer_tag)
            except Exception:
                pass

        # 等待后台任务
        await asyncio.gather(*self._bg_tasks, return_exceptions=True)

        # 关闭 http 客户端
        if self._http:
            await self._http.aclose()

        # 关 channel/connection
        if self._ch and not self._ch.is_closed:
            await self._ch.close()
        if self._conn and not self._conn.is_closed:
            await self._conn.close()
        logger.info("==========停止mq成功==========")

    async def _on_message(self, message: aio_pika.IncomingMessage):
        # consume 的回调里不要做重活；交给后台 task，控制并发
        if self._stopping:
            logger.warning("[MQ] 收到消息但正在停止，忽略")
            return

        # logger.info(f"[MQ] 收到新消息: delivery_tag={message.delivery_tag}, routing_key={message.routing_key}")
        await self._sem.acquire()
        t = asyncio.create_task(self._dispatch(message))
        self._bg_tasks.add(t)
        t.add_done_callback(lambda _: (self._bg_tasks.discard(t), self._sem.release()))

    async def _dispatch(self, message: aio_pika.IncomingMessage):
        try:
            await asyncio.wait_for(self._handle_message_safe(message), timeout=TASK_TIMEOUT_SEC)
            try:
                await message.ack()
                logger.info("[MQ] ack ok")
            except Exception as e:
                logger.error(f"[MQ] ack failed: {repr(e)}")  # 打印 repr 便于看到底层 errno / 类名
        except asyncio.TimeoutError:
            logger.warning(f"[MQ] task timeout ({TASK_TIMEOUT_SEC}s)")
            try:
                await message.nack(requeue=True)
                logger.info("[MQ] nack requeue ok (timeout)")
            except Exception as e:
                logger.error(f"[MQ] nack failed after timeout: {repr(e)}")
        except MissingFieldError as e:
            logger.error(f"[MQ] handle error (business missing field): {repr(e)}")
            try:
                await message.ack()
                logger.info(f"[MQ] ack dropped message (missing field: {e.field})")
            except Exception as ack_err:
                logger.error(f"[MQ] ack failed after missing field: {repr(ack_err)}")
        except Exception as e:
            logger.error(f"[MQ] handle error (business): {repr(e)}")  # 明确：业务异常
            # 对于业务异常，ack掉消息避免重复消费和消息堆积
            try:
                await message.ack()
                logger.info("[MQ] ack dropped message (business error)")
            except Exception as ack_err:
                logger.error(f"[MQ] ack failed after business error: {repr(ack_err)}")

    async def _handle_message_safe(self, message: aio_pika.IncomingMessage):
        # logger.info(f"[MQ] 开始处理消息: delivery_tag={message.delivery_tag}")
        try:
            payload = json.loads(message.body.decode())
            # logger.info(f"[MQ] 消息解析成功: payload keys={list(payload.keys())}")
            data = payload["data"]
            logger.info(f"[MQ] data keys={list(data.keys()) if isinstance(data, dict) else type(data)}")

            # —— 业务处理（逐步打开开关）——
            # 根据 source 字段选择不同的 agent
            source = data.get("source", "toC")  # 默认为 toC
            logger.info(f"[MQ] 检测到source={source}")
            use_B = False
            if source == "toB":
                use_B = True
                from app.utils_toB.agent_toB import DesignAssistant
                logger.info("[MQ] 使用 toB 版本的 agent")
            else:
                from app.utils.agent import DesignAssistant
                logger.info("[MQ] 使用 toC 版本的 agent")
            # 校验 conversation_id（toB 强依赖）
            if use_B:
                conversation_id = data.get("conversation_id")
                if not conversation_id:
                    fallback_id = payload.get("job_id")
                    if fallback_id:
                        data["conversation_id"] = fallback_id
                        logger.warning(f"[MQ] missing conversation_id, fallback to job_id={fallback_id}")
                    else:
                        raise MissingFieldError("conversation_id", payload)

            # 保证存在 job_id，便于后续日志追踪
            if "job_id" not in data and payload.get("job_id"):
                data["job_id"] = payload["job_id"]
        except MissingFieldError:
            raise
        except Exception as e:
            logger.error(f"[MQ] 消息解析或初始化失败: {repr(e)}")
            import traceback
            logger.error(f"[MQ] 错误详情: {traceback.format_exc()}")
            raise
        
        # 1) Agent
        assistant = DesignAssistant(data)
        result: dict = await assistant.process_input()
        if 'title_update' not in result or result['title_update']!=True:
            result['conversation_title'] = ''
        logger.info(f'---------agent结果---------\n{result}')
        logger.info("[MQ] agent ok")

        # 2) 写文件（先关、后开）
        try:
            # 暂时注释掉以便 StepB 精准定位
            # await self._write_file(data, result)
            pass
        except Exception as e:
            logger.error(f"[MQ] file write exception: {repr(e)}")  # 明确归属

        # 3) HTTP 回调（先关、后开；或把 URL 换成 http://httpbin.org/post 验证网络）
        try:
            assert self._http is not None
            url = callback_toB_url if use_B else callback_url
            # logger.info(f"[MQ] callback url: {url}")
            
            # 准备回调数据：移除内部使用的字段，确保只发送接收端需要的字段
            callback_data = result.copy()
            # 移除内部路由字段（不应该发送给接收端）
            callback_data.pop("source", None)
            callback_data.pop("job_id", None)  # job_id 是内部使用的
            
            # logger.info(f"[MQ] callback data keys: {list(callback_data.keys())}")
            # logger.info(f"[MQ] callback data sample: {json.dumps(callback_data, ensure_ascii=False)[:500]}")

            resp = await self._http.post(url, json=callback_data, headers={"Content-Type": "application/json"})
            if resp.status_code >= 400:
                body = await resp.aread()
                body_str = body.decode('utf-8', errors='ignore')[:1000]
                logger.error(f"[MQ] callback failed {resp.status_code} body={body_str!r}")
                logger.error(f"[MQ] callback request data: {json.dumps(callback_data, ensure_ascii=False)[:500]}")
            else:
                logger.info(f"[MQ] callback success {resp.status_code}")
        except Exception as e:
            logger.error(f"[MQ] callback exception: {repr(e)}")  # 明确归属
            import traceback
            logger.error(f"[MQ] callback traceback: {traceback.format_exc()}")


mq_runner = MQRunner()
logger.info(f"[MQ_MODULE] mq_runner 单例已创建, PID={os.getpid()}")
