# ==================== API接口管理 ====================
"""
智能家装Agent API接口管理模块

负责管理所有外部API接口的调用，包括：
- 小区搜索API
- 户型信息API
- 其他业务API
"""

import httpx
import json
from app.config import (
    search_estate_url, 
    find_house_type_url
)
from app.utils_toB.constants import API_CONFIG


# ==================== 小区搜索API ====================
async def search_estate(city: str, community: str):
    """
    调用小区搜索API
    
    Args:
        city (str): 城市名称
        community (str): 小区名称
        
    Returns:
        dict: API返回的搜索结果
    """
    url = search_estate_url
    payload = {
        "p": 0,
        "page_size": 10,
        "keyword": community,
        "city": city
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()  # 确保请求成功
        return response.json()


# ==================== 用户户型信息API ====================
async def find_house_type(conversation_id: int):
    """
    调用获取房型信息的API
    
    从后端API获取用户的户型信息，用于后续的户型匹配和推荐。
    
    Args:
        conversation_id (int): 对话ID
        
    Returns:
        list: 户型信息列表，如果失败则返回None
    """
    url = find_house_type_url
    payload = json.dumps({
        "conversation_id": conversation_id
    })
    headers = {
       'Authorization': API_CONFIG["AUTHORIZATION"],
       'Request-ID': API_CONFIG["REQUEST_ID"],
       'Content-Type': API_CONFIG["CONTENT_TYPE"]
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, data=payload)
        response.raise_for_status()  # 确保请求成功
        return response.json().get('data', None)  # 返回 'data' 部分








