# app/views/view.py
import os
import json
import uuid
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Request, HTTPException


from app.config import RABBITMQ_URL, QUEUE_NAME

from app.utils.agent import InputModel
from app.utils_toB.agent_toB import InputModel as InputModelToB
from app.utils_toB.get_style_route import get_style_route
from app.utils_toB.get_ai_generation_route import generate_images
from pydantic import BaseModel, Field
from typing import List
import aio_pika
from aio_pika.pool import Pool

logger = logging.getLogger(__name__)

print(555, RABBITMQ_URL)

router = APIRouter()

# ---- 简单连接池（发布端） ----
async def _get_connection():
    return await aio_pika.connect_robust(RABBITMQ_URL)
connection_pool: Pool = Pool(_get_connection, max_size=2)

async def _get_channel():
    async with connection_pool.acquire() as conn:
        ch = await conn.channel()
        return ch
channel_pool: Pool = Pool(_get_channel, max_size=10)

@router.on_event("startup")
async def ensure_queue():
    async with channel_pool.acquire() as ch:
        await ch.set_qos(prefetch_count=32)
        await ch.declare_queue(QUEUE_NAME, durable=True)

async def publish_task(payload: dict) -> str:
    logger.info(f"[PUBLISH] 准备发布消息: payload={payload}")
    job_id = payload.get("conversation_id") or str(uuid.uuid4())
    payload["job_id"] = job_id
    
    body = json.dumps({"job_id": job_id, "data": payload}, ensure_ascii=False).encode()

    msg = aio_pika.Message(
        body=body,
        content_type="application/json",
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        correlation_id=job_id,
        message_id=job_id,
        timestamp=datetime.now(ZoneInfo('Asia/Shanghai')),
    )

    print(f"[PUBLISH] 准备发布消息: job_id={job_id}, queue={QUEUE_NAME}")
    print(f"[PUBLISH] Message对象: {msg}")
    try:
        async with channel_pool.acquire() as ch:
            await ch.default_exchange.publish(msg, routing_key=QUEUE_NAME)
        print(f"[PUBLISH] 消息发布成功: job_id={job_id}")
    except Exception as e:
        logger.error(f"[PUBLISH] 消息发布失败: job_id={job_id}, error={repr(e)}", exc_info=True)
        raise
    return job_id

@router.post("/process")
async def process_route(input_data: InputModel):
    data = input_data.model_dump()
    data["source"] = "toC"  # 标识为 toC 版本
    job_id = await publish_task(data)
    print("job_id", job_id)
    return {"status": "queued", "job_id": job_id}

@router.post("/processtoB")
async def process_toB_route(request: Request):
    data = await request.json()
    data["source"] = "toB"
    job_id = await publish_task(data)
    return {"status": "queued", "job_id": job_id}

@router.post("/get_style")
async def get_style(input_data: InputModelToB):
    """
    根据用户输入获取匹配的家居风格列表
    
    Args:
        input_data: 包含用户输入的请求数据
        
    Returns:
        dict: 包含风格列表的字典，格式为 {"style": ["风格1", "风格2"]}
    """
    try:
        data = input_data.model_dump()
        style_description = data.get("user_input", "")
        
        if not style_description:
            return {"error": "user_input不能为空", "style": []}
        
        style_list = await get_style_route(style_description)
        print(f"风格匹配结果: {style_list}")
        return style_list
        
    except ValueError as e:
        logger.error(f"参数错误: {e}")
        return {"error": str(e), "style": []}
    except Exception as e:
        logger.error(f"获取风格列表失败: {e}", exc_info=True)
        return {"error": "获取风格列表失败，请稍后重试", "style": []}

# ==================== AI图片生成请求模型 ====================
class AIGenerateRequest(BaseModel):
    """AI图片生成请求模型"""
    image_urls: List[str] = Field(
        ...,
        description="输入图片的URL列表",
        min_items=1
    )
    size: str = Field(
        default="2K",
        description="图片尺寸，默认2K"
    )
    max_images: int = Field(
        default=4,
        description="最多生成几张图，默认4",
        ge=1,
        le=10
    )


class AIGenerateResponse(BaseModel):
    """AI图片生成响应模型"""
    generated_images: List[str] = Field(
        ...,
        description="生成的图片URL列表"
    )


@router.post("/ai_generate", response_model=AIGenerateResponse)
async def ai_generate(request: AIGenerateRequest):
    """
    AI图片生成接口
    
    根据输入的图片URL列表，调用火山平台API生成改善光效后的图片
    
    Args:
        request: 包含图片URL列表、尺寸和最大生成数量的请求数据
        
    Returns:
        AIGenerateResponse: 包含生成的图片URL列表的响应
        
    Raises:
        HTTPException: 当参数错误或API调用失败时
    """
    try:
        data = request.model_dump()
        image_urls = data.get("image_urls", [])
        size = data.get("size", "2K")
        max_images = data.get("max_images", 4)
        
        if not image_urls:
            raise HTTPException(status_code=400, detail="image_urls不能为空")
        
        logger.info(f"收到AI图片生成请求: 图片数量={len(image_urls)}, 尺寸={size}, 最大生成数={max_images}")
        
        # 调用生成函数
        result = await generate_images(
            image_urls=image_urls,
            size=size,
            max_images=max_images
        )
        
        logger.info(f"AI图片生成成功: 生成图片数量={len(result.get('generated_images', []))}")
        
        return result
        
    except ValueError as e:
        logger.error(f"参数错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI图片生成失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="图片生成失败，请稍后重试")