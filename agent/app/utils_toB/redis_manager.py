from app.utils_toB.constants import LOG_CONFIG
import logging
import time
# ==================== 日志配置 ====================
logging.basicConfig(level=LOG_CONFIG["LEVEL"], format=LOG_CONFIG["FORMAT"])
logger = logging.getLogger(__name__)



# ==================== Redis数据库管理 ====================
"""
智能家装Agent Redis数据库管理模块

负责管理所有Redis相关的操作，包括：
- 连接池管理
- 键值操作
- 会话状态管理
- 历史记录管理
"""

import redis.asyncio as aioredis
from urllib.parse import quote
from app.config import redis_host, redis_port, redis_db, redis_password

# 进程级单例 Redis 客户端
_redis_client: aioredis.Redis | None = None


# ==================== Redis连接管理 ====================
async def _build_redis_client() -> aioredis.Redis:
    """内部方法：根据配置构建 Redis 客户端（带连接池，decode_responses）。"""
    if redis_password:
        safe_password = quote(redis_password)
        url = f"redis://:{safe_password}@{redis_host}:{redis_port}/{redis_db}"
    else:
        url = f"redis://{redis_host}:{redis_port}/{redis_db}"
    # 这里的 from_url 会复用内部连接池，适合全局单例复用
    return await aioredis.from_url(
        url,
        decode_responses=True,
    )


async def get_redis_client() -> aioredis.Redis:
    """获取进程级单例 Redis 客户端。"""
    # logger.info("开始: 获取进程级单例 Redis 客户端")
    st_time_get_redis_client = time.perf_counter()
    global _redis_client
    if _redis_client is None:
        _redis_client = await _build_redis_client()
    _dt = (time.perf_counter() - st_time_get_redis_client) * 1000
    # logger.info(f"结束: 获取进程级单例 Redis 客户端, 用时 {int(_dt)} ms")
    return _redis_client


# 兼容旧接口名（保留函数但改为返回单例）
async def create_redis_pool(redis_host, redis_port, redis_db, redis_password=None):
    return await get_redis_client()


# ==================== 基础键值操作 ====================
async def get_redis_value(key):
    """
    从Redis获取值
    
    Args:
        key (str): Redis键名
        
    Returns:
        str: Redis中存储的值
    """
    redis = await get_redis_client()
    value = await redis.get(key)
    return value


async def set_redis_value(key, value):
    """
    设置Redis键值
    
    Args:
        key (str): Redis键名
        value (str): 要存储的值
    """
    redis = await get_redis_client()
    await redis.set(key, value)


async def key_exists(key):
    """
    检查Redis键是否存在
    
    Args:
        key (str): Redis键名
        
    Returns:
        bool: 键是否存在
    """
    redis = await get_redis_client()
    exists = await redis.exists(key)
    return exists > 0


# ==================== 批量与Pipeline操作 ====================
async def get_many(keys: list[str]):
    """
    批量获取多个键的值（MGET）。
    Returns: list 与 keys 对应的值列表。
    """
    if not keys:
        return []
    redis = await get_redis_client()
    return await redis.mget(keys)


async def set_many(mapping: dict[str, str]):
    """批量设置多个键值（MSET）。"""
    if not mapping:
        return True
    redis = await get_redis_client()
    # mset 返回 True/OK（不同驱动表现略有差异），这里直接返回结果
    return await redis.mset(mapping)


class _AsyncPipelineContext:
    """异步上下文管理器封装 pipeline，退出时自动 execute。"""
    def __init__(self, pipeline):
        self._pipeline = pipeline

    async def __aenter__(self):
        return self._pipeline

    async def __aexit__(self, exc_type, exc, tb):
        if exc is None:
            await self._pipeline.execute()
        else:
            # 出错直接丢弃队列
            try:
                await self._pipeline.reset()
            except Exception:
                pass
        return False


async def pipeline(transaction: bool = False):
    """
    获取一个可复用的 pipeline（异步上下文形式）。
    用法：
    async with pipeline() as p:
        p.set('a', '1')
        p.get('a')
    """
    redis = await get_redis_client()
    return _AsyncPipelineContext(redis.pipeline(transaction=transaction))


async def pipeline_exec(ops: list[tuple[str, list, dict]]):
    """
    直接传入操作列表批量执行。
    ops 形如 [("set", [key, value], {}), ("get", [key], {}), ...]
    返回执行结果列表。
    """
    if not ops:
        return []
    redis = await get_redis_client()
    p = redis.pipeline(transaction=False)
    for method_name, args, kwargs in ops:
        getattr(p, method_name)(*(args or []), **(kwargs or {}))
    return await p.execute()


# ==================== 会话状态管理 ====================
async def get_session_state(session_id):
    """
    获取会话状态
    
    Args:
        session_id (int): 会话ID
        
    Returns:
        dict: 会话状态数据
    """
    import json
    key = f"state:{session_id}"
    if await key_exists(key):
        try:
            state_json = await get_redis_value(key)
            if state_json is not None:
                state = json.loads(state_json)
                # 确保列表类型的字段确实是列表
                list_fields = ['finish_type_list', 'styles', 'search_result']
                for field in list_fields:
                    if field in state and not isinstance(state[field], list):
                        logger.warning(f"状态字段 {field} 类型不正确，期望list，实际为{type(state[field])}，将重置为空列表")
                        state[field] = []
                return state
            else:
                logger.warning(f"Redis键 {key} 存在但值为None")
                return None
        except json.JSONDecodeError as e:
            logger.error(f"解析会话状态JSON失败: {e}，将返回None")
            return None
        except Exception as e:
            logger.error(f"获取会话状态时发生未知错误: {e}，将返回None")
            return None
    return None


async def set_session_state(session_id, state):
    """
    保留会话状态state到redis中
    Args:
        session_id (int): 会话ID
        state (dict): 状态数据
    """
    import json
    key = f"state:{session_id}"
    await set_redis_value(key, json.dumps(state, ensure_ascii=False))


async def get_type_6_state(session_id):
    """
    获取type_6状态
    
    Args:
        session_id (int): 会话ID
        
    Returns:
        int: type_6状态值
    """
    key = f"type_6:{session_id}"
    if await key_exists(key):
        return int(await get_redis_value(key))
    return 0


async def set_type_6_state(session_id, value):
    """
    设置type_6状态
    
    Args:
        session_id (int): 会话ID
        value (int): 状态值
    """
    key = f"type_6:{session_id}"
    await set_redis_value(key, str(value))


# ==================== 历史记录管理 ====================
async def get_conversation_history(session_id):
    # logger.info("开始: 获取历史对话记录")
    st_time_get_history = time.perf_counter()
    """
    获取对话历史记录
    
    Args:
        session_id (int): 会话ID
        
    Returns:
        list: 历史记录列表
    """
    import json
    key = f"task_history1:{session_id}"
    history = []
    if await key_exists(key):
        history_json = None
        try:
            history_json = await get_redis_value(key)
            if history_json is not None:
                # 记录原始值以便调试
                logger.debug(f"从Redis获取的原始值类型: {type(history_json)}, 值: {history_json[:100] if isinstance(history_json, str) and len(history_json) > 100 else history_json}")
                parsed_history = json.loads(history_json)
                # 确保返回的是列表类型
                if isinstance(parsed_history, list):
                    history = parsed_history
                else:
                    logger.warning(f"Redis中的历史记录格式不正确，期望list，实际为{type(parsed_history)}，值: {parsed_history}，将使用空列表")
                    history = []
            else:
                logger.warning(f"Redis键 {key} 存在但值为None，将使用空列表")
        except json.JSONDecodeError as e:
            logger.error(f"解析历史记录JSON失败 (JSONDecodeError): {e}，原始值: {history_json[:200] if history_json and isinstance(history_json, str) else str(history_json)[:200] if history_json else 'None'}，将使用空列表")
            history = []
        except TypeError as e:
            logger.error(f"解析历史记录JSON失败 (TypeError): {e}，原始值类型: {type(history_json)}，值: {history_json}，将使用空列表")
            history = []
        except Exception as e:
            logger.error(f"获取历史记录时发生未知错误: {e}，原始值: {history_json}，将使用空列表")
            history = []
    _dt = (time.perf_counter() - st_time_get_history) * 1000
    # logger.info(f"结束: 获取历史对话记录, 用时 {int(_dt)} ms")
    # 最后再次确保返回的是列表（双重保险）
    if not isinstance(history, list):
        logger.error(f"get_conversation_history返回非列表类型: {type(history)}，值: {history}，强制转换为空列表")
        return []
    return history


async def set_conversation_history(session_id, history):
    """
    设置对话历史记录
    
    Args:
        session_id (int): 会话ID
        history (list): 历史记录列表
    """
    import json
    key = f"task_history1:{session_id}"
    await set_redis_value(key, json.dumps(history, ensure_ascii=False))


async def add_to_history(session_id, data):
    """
    添加数据到历史记录
    
    Args:
        session_id (int): 会话ID
        data (dict): 要添加的数据
    """
    history = await get_conversation_history(session_id)
    history.append(data)
    await set_conversation_history(session_id, history)
