# ==================== 风格路由模块 ====================
"""
风格路由模块:负责根据用户描述获取匹配的家居风格列表
路由：/get_style
请求方式：POST
请求参数：style_description: 用户的风格描述文本
返回参数：style_list: 包含风格列表的字典，格式为 {"style": ["风格1", "风格2"]}
"""


from app.utils_toB.prompt import get_style_prompt
from app.utils_toB.llm_manager import get_llm
import json
import logging

logger = logging.getLogger(__name__)




async def get_style_route(style_description: str) -> dict:
    """
    根据用户描述获取匹配的家居风格列表
    
    Args:
        style_description: 用户的风格描述文本
        
    Returns:
        dict: 包含风格列表的字典，格式为 {"style": ["风格1", "风格2"]}
        
    Raises:
        ValueError: 当LLM返回的JSON格式不正确时
        Exception: 当LLM调用失败时
    """
    try:
        # 获取提示词模板并格式化
        prompt_template = get_style_prompt()
        prompt = prompt_template.format(input=style_description)
        
        # 调用LLM获取响应
        llm = get_llm('qwen-flash', temperature=0.2, top_p=0.9)
        response = await llm.ainvoke(prompt)
        
        # 提取响应内容
        response_content = response.content.strip()
        
        # 尝试解析JSON，处理可能的markdown代码块
        if response_content.startswith("```"):
            # 移除可能的markdown代码块标记
            lines = response_content.split('\n')
            json_start = next((i for i, line in enumerate(lines) if '{' in line), 0)
            json_end = next((i for i, line in enumerate(lines[json_start:]) if '}' in line), len(lines))
            response_content = '\n'.join(lines[json_start:json_start+json_end+1])
        
        # 解析JSON
        try:
            style_dict = json.loads(response_content)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {response_content}, 错误: {e}")
            # 尝试提取JSON部分
            import re
            json_match = re.search(r'\{[^{}]*"style"[^{}]*\[[^\]]*\][^{}]*\}', response_content)
            if json_match:
                style_dict = json.loads(json_match.group())
            else:
                raise ValueError(f"无法解析LLM返回的JSON格式: {response_content}")
        
        # 验证返回格式
        if not isinstance(style_dict, dict) or 'style' not in style_dict:
            raise ValueError(f"返回格式不正确，期望包含'style'键的字典: {style_dict}")
        
        if not isinstance(style_dict['style'], list):
            raise ValueError(f"'style'字段应该是列表类型: {style_dict['style']}")
        
        return style_dict
        
    except Exception as e:
        logger.error(f"获取风格列表失败: {e}", exc_info=True)
        raise