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
    user_input:str # 用户当前输入内容
    type:int # 响应类型标识
    search_city:str # 搜索城市
    search_area:str # 搜索小区
    define_area:bool # 是否已确定户型面积
    define_house_type:bool # 是否已确定户型
    search_house_type:str # 搜索户型
    styles:list[str] # 风格偏好列表
    conversation_id:int # 对话会话ID
    content:str # AI回复内容
    need_house_type:bool # 是否需要户型信息
    conversation_type:str # 对话类型
    role:str # 角色标识
    rag_query:str # RAG知识库查询的query
    is_switch_scenes:int # 是否切换场景
    switch_intelligent:int # 智能切换标识
    search_result:list[dict] # 搜索结果列表
    input_token:int # 输入Token数量
    output_token:int # 输出Token数量
    receive_time:str # 接收时间
    finish_time:str # 完成时间
    brand:dict # 品牌偏好信息


# ==================== 路由模型 ====================

class RouterMode(BaseModel):
    conversation_type:str=Field(description='结合历史对话与用户输入,判断出的用户输入的对话类型')
    search_city:str=Field(description="""结合历史对话与用户输入判断出的用户预装修房子所在的城市,无法提取则为空字符""")
    search_area:str=Field(description="""结合历史对话与用户输入判断出的用户预装修房子所在的小区,无法提取则为空字符""")
    search_house_type:int=Field(description="""结合历史对话与用户输入判断出的用户预装修房子的面积,该值是一个数值,如果无法提取,则为0 ,例如:使用4室2厅3卫164m²户型,则该值为164""")
    styles:list[str]=Field(description="""结合历史对话与用户输入,判断和用户描述内容最相似的风格,根据家装设计知识进行判断，比如古风/雕花对应中式，喜欢直线条对应极简，曲线感/艺术感/舒适对应欧式,弧形/精致/优雅/浪漫/米色对应法式，大理石/高级感/皮革/丝绒对应轻奢，温柔圆润对应奶油，金属玻璃对应现代，温馨/复古/自由对应美式，最终匹配的风格只能是
    ["现代","极简","轻奢","奶油","中式","欧式","美式","法式","侘寂","原木","复古","北欧"]这些选项,如果无法提取,则为空列表""")
    brand:str=Field(description="""结合历史对话与用户输入,判断出的用户选择的品牌,如果无法提取,则为空字符串.目前有["简一","马可波罗","诺贝尔"]品牌""")
    rag_query:str=Field(description="""对话类型为"知识类"时，结合用户输入与历史对话判断出的用户需要查询的内容""")
    content:str=Field(description="""对话类型为打"招呼类"时,直接生成的回复内容""")

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


