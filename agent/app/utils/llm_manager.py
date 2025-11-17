# ==================== LLM模型管理 ====================
"""
智能家装Agent LLM模型管理模块

负责管理所有LLM相关的配置、模型实例和处理链，包括：
- 模型配置和实例化
- 提示词模板定义
- 处理链构建
- 输出解析器配置
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.output_parsers import StrOutputParser
from app.utils.models import RouterMode, SwitchParamsMode
from app.utils.prompt import get_know_rag_prompt,get_router_prompt,get_switch_params_prompt
from app.utils.constants import ALIYUN_API_KEY,ALIYUN_BASE_URL

# ==================== LLM模型配置 ====================
def get_llm(model: str,temperature:float=0.7,top_p=0.9):
    """
    获取配置好的LLM模型实例
    
    Args:
        model (str): 模型名称，如'qwen-plus-latest'、'qwen-flash'等
        
    Returns:
        ChatOpenAI: 配置好的聊天模型实例
    """
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        top_p=top_p,
        api_key=ALIYUN_API_KEY,  # 阿里云DashScope API密钥
        base_url=ALIYUN_BASE_URL, # DashScope API基础URL
    )


# ==================== 路由智能体配置 ====================
# 创建路由解析器，用于将LLM输出解析为RouterMode对象，规范llm响应结果
router_parser = PydanticOutputParser(pydantic_object=RouterMode)
# 创建路由处理链：模板 -> LLM -> 解析器
router_chain = PromptTemplate.from_template(
    get_router_prompt(), 
    # 固定instruction变量
    partial_variables={"instruction": router_parser.get_format_instructions()}
) | get_llm('qwen-plus-latest',temperature=0.2,top_p=0.9)




# ==================== RAG知识库配置 ====================
# RAG提示词模板 - 用于基于检索到的文档回答用户问题
rag_prompt = PromptTemplate.from_template(get_know_rag_prompt())

# RAG处理链：模板 -> LLM
rag_chain = rag_prompt | get_llm('qwen-plus-latest',temperature=0.7,top_p=0.9)



# ==================== 切换参数智能体配置 ====================
# 切换参数解析器
switch_params_parser = PydanticOutputParser(pydantic_object=SwitchParamsMode)
# 切换风格智能体提示词模板
switch_params_prompt = PromptTemplate.from_template(
    get_switch_params_prompt(),
    partial_variables={"instruction": switch_params_parser.get_format_instructions()}
)
# 切换风格处理链：模板 -> LLM -> 解析器
switch_params_chain = switch_params_prompt | get_llm('qwen-flash',temperature=0.2,top_p=0.9) | switch_params_parser