# ==================== 数据模型定义 ====================
"""
智能家装Agent数据模型模块

定义系统中使用的所有Pydantic数据模型，包括：
- 图状态模型,可通过state前后端传递状态数据
- 路由模型
- 品牌模型
- 其他业务模型
"""

from typing import *
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from dataclasses import dataclass


# ==================== 图状态模型 ====================
class GraphState(TypedDict):
    """
    图状态类 - 定义整个对话流程中需要维护的状态信息
    
    该状态类包含了智能家装Agent在处理用户请求时需要的所有状态信息，
    包括用户输入、对话类型、搜索条件、户型信息、风格偏好等。
    """
    # 用户输入相关
    user_input: str=""  # 用户当前输入内容
    type: int=0  # 响应类型标识
    content: str=""  # AI回复内容
    search_city: str=""  # 搜索城市
    search_area: str=""  # 搜索小区
    search_result:list[dict]=[] # 搜索结果列表
    styles:list[str]=[] # 风格偏好列表
    
    # 对话管理相关
    conversation_id: int # 对话会话ID
    conversation_title: str="新对话"  # 对话标题
    title_update: bool=False # 是否更新标题
    conversation_type: str=""  # 对话类型
    role: str="user"  # 角色标识（user/assistant）
    
    # 状态标识
    cur_flow_finish: bool=False # 是否结束 热门商品选择/热门品牌案例/户型确定 流程
    # define_house_type: bool=False  # 是否已确定户型
    # define_product_sku: bool=False  # 是否已确定商品sku
    # define_room_example: bool=False  # 是否已确定样板房间示例
    # define_product_params: bool=False  # 是否已确定商品参数
    finish_type_list: list[int]=[] # 已结束的流程类型列表
    finish_type:int=0 # 当前的流程类型
    cur_house_type: str="" # 当前对话确定的户型信息，用于命名会话标题
    # switch_cases: bool=False # 是否换一批案例
    # un_use_product: list[str]=[] # 未使用的商品id列表
    generation_type: str=""  # 生成模式,1:AI智能设计,2:案例设计

    # Token统计
    input_token: int=0  # 输入Token数量
    output_token: int=0  # 输出Token数量
    
    # 时间记录
    receive_time: str=""  # 接收时间
    finish_time: str=""  # 完成时间
    # rag
    rag_query: str="" # RAG知识库查询的query


# ==================== GraphState 默认值 ====================
# TypedDict 不支持默认值语法，所以需要单独定义默认值字典
GRAPH_STATE_DEFAULTS: dict = {
    "user_input": "",
    "type": 0,
    "content": "",
    "search_city": "",
    "search_area": "",
    "styles": [],
    "conversation_title": "新对话",
    "title_update": False,
    "conversation_type": "",
    "role": "user",
    "cur_flow_finish": False,
    # "define_product_params": False,
    # "define_house_type": False,
    # "define_product_sku": False,
    # "un_use_product": [],
    "finish_type_list": [],
    "finish_type": 0,
    "generation_type": "",
    "cur_house_type": "",
    "switch_cases": False,
    "input_token": 0,
    "output_token": 0,
    "receive_time": "",
    "finish_time": "",
    "rag_query": "",
}


def create_graph_state(data: dict) -> GraphState:
    """
    创建 GraphState，用默认值补充 data 中缺失的参数
    
    Args:
        data: 用户提供的数据字典
        
    Returns:
        GraphState: 完整的图状态字典，包含所有必需字段和默认值
    """
    # 合并默认值和用户数据，用户数据优先
    state_dict = {**GRAPH_STATE_DEFAULTS, **data}
    return GraphState(**state_dict)


# ==================== 路由模型 ====================
class RouterMode(BaseModel):
    """
    路由智能体数据模型
    
    用于解析用户输入并提取关键信息，包括对话类型、地理位置、户型面积、
    风格偏好、品牌偏好和知识查询内容等。这些信息将用于后续的流程路由。
    """
    conversation_type: str = Field(
        description='结合历史对话与用户输入,判断出的用户输入的对话类型'
    )
    search_city: str = Field(
        description="""结合历史对话与用户输入判断出的用户预装修房子所在的城市,如果无法提取,则为空字符串"""
    )
    search_area: str = Field(
        description="""结合历史对话与用户输入判断出的用户预装修房子所在的小区,如果无法提取,则为空字符串"""
    )
    # house_area: int = Field(
    #     description="""结合历史对话与用户输入判断出的用户预装修房子的面积,该值是一个数值,如果无法提取,则为0 ,例如:使用4室2厅3卫164m²户型,则该值为164"""
    # )
    styles:list[str]=Field(description="""结合历史对话与用户输入,判断和用户描述内容最相似的风格,根据家装设计知识进行判断，比如古风/雕花对应中式，喜欢直线条对应极简，曲线感/艺术感/舒适对应欧式,弧形/精致/优雅/浪漫/米色对应法式，大理石/高级感/皮革/丝绒对应轻奢，温柔圆润对应奶油，金属玻璃对应现代，温馨/复古/自由对应美式，最终匹配的风格只能是
    ["现代","极简","轻奢","奶油","中式","欧式","美式","法式","侘寂","原木","复古","北欧"]这些选项,如果无法提取,则为空列表""")
    
    brand: str = Field(
        description="""结合历史对话与用户输入,判断出的用户选择的品牌,如果无法提取,则为空字符串.目前有["简一","马可波罗","诺贝尔"]等品牌"""
    )
    rag_query: str = Field(
        description="""如果对话类型是"装修知识类",结合用户输入与历史对话,判断出的用户当前需要查询的内容,否则是空字符串 """
    )
    switch_params_dict: dict = Field(
        description="""若对话类型为切换参数类,判断出的用户要切换的参数以及其值,例如:{"户型": "3室2厅1卫", "风格": "现代简约"}，未明确值为空字符串，例如:{"风格": ""}"""
    )




# ==================== 切换风格模型 ====================
class SwitchParamsMode(BaseModel):
    """
    切换参数智能体数据模型
    """

    switch_params:list[str]=Field(description="""根据用户输入,判断出的用户要切换的参数有哪些,里面的元素只能是["品牌","风格"]中的某一个""")
    pre_params:dict=Field(description="""总结用户自己描述的需求，是用户的原生输入，例如用户说"有带雕花的吗"，则pre_params为{"风格": "雕花","品牌":""}，用户说"我喜欢直线条"，则pre_params为{"风格": "直线条","品牌":""}""")
    switch_params_dict:dict=Field(description="""根据用户输入,判断出的用户要切换的参数以及其值,对于风格你需要判断和用户描述内容最相似的风格,根据家装设计知识进行判断，比如古风/雕花对应中式，喜欢直线条对应极简，弧形/精致/优雅/浪漫/米色对应法式，
    大理石/高级感/皮革/丝绒对应轻奢，温柔圆润对应奶油，金属玻璃对应现代，曲线/艺术感/舒适对应欧式，温馨/复古/自由对应美式，最终匹配的风格只能是
    ["现代","极简","轻奢","奶油","中式","欧式","美式","法式","侘寂","原木","复古","北欧"]这些选项,如果无法提取,则为空列表，例如:{"品牌": "简一", "风格": "简约"}，，品牌只能是["简一","马可波罗","诺贝尔"]品牌""")


