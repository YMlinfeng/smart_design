from langchain_community.embeddings.dashscope import DashScopeEmbeddings

# ==================== 常量配置 ====================

"""
智能家装Agent常量配置模块
包含系统中使用的常量配置定义，包括：
阿里云api配置：
ALIYUN_API_KEY：阿里云api密钥
ALIYUN_BASE_URL：阿里云api基础url

请求头配置：
HEADERS_CONFIG：请求头配置

嵌入模型api配置：
EMBED_API_KEY：嵌入模型api密钥

对话类型：
CONVERSATION_TYPES：对话类型

路由>>节点映射：
conditional_router：路由>>节点映射函数

响应类型：
RESPONSE_TYPES：响应类型

风格选项：
STYLE_OPTIONS：风格选项
"""

# ==================== 阿里云api配置 ====================
ALIYUN_API_KEY = "sk-a708960cdb7b4bdbbb13ca0db0296b84"
ALIYUN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1" 

# ==================== 请求头配置 ====================
HEADERS_CONFIG = {
    "AUTHORIZATION": "Bearer b31682c9-4dae-4f3f-8ed4-3f822e7eeea0",
    "CONTENT_TYPE": "application/json"
}

# ==================== 嵌入模型配置 ====================
EMBED = DashScopeEmbeddings(
    dashscope_api_key='sk-a708960cdb7b4bdbbb13ca0db0296b84',  # DashScope API密钥
    model="text-embedding-v3"  # 嵌入模型版本
)


# ==================== 路由->节点映射 ====================
def conditional_router(state):
    conversation_type = state['conversation_type']
    if conversation_type=='城市小区类':
        return 'area'
    elif conversation_type=="通用问答类":
        return 'universal_chat'
    elif conversation_type=='装修知识类':
        return 'rag_run'
    elif conversation_type=="设计房屋类":
        return 'design_house'
    elif conversation_type=='切换参数类':
        return "switch_params"
    elif conversation_type=='调用户型类':
        return "see_user_house_type"
    elif conversation_type=='小区+风格/品牌类':
        return 'area_style'
    elif conversation_type=='换一批方案类':
        return 'switch'
    elif conversation_type=='小区+风格/品牌+户型面积类':
        return 'area_style_area'
    elif conversation_type=='小区+户型面积类':
        return 'area_house_type'



# ==================== 响应类型 ====================
RESPONSE_TYPES = {
    "TEXT": 1,           # 文本回复
    "SEARCH_RESULT": 13,  # 搜索结果
    "NO_RESULT": 36,      # 无搜索结果,给出户型识别和相似户型两种选择
    "BRAND_CASES": 37,    # 分空间筛选品牌案例
    "HOT_PRODUCTS": 33,   # 热门商品
    "SIMILAR_HOUSE": 29,  # 相似户型
    "HOUSE_RECOGNITION": 30,  # 户型识别
    "ASK_STYLE": 32,     # 询问风格
    "HOUSE_TYPE_RESULT": 14, # 户型搜索结果
    "ESTATE_RESULT_FEEDBACK": 5, # 小区结果反馈
    "NO_ESTATE_RESULT":18, # 户型检索为0 （旧版本）
    "CASE_LIST": 6,    # 筛选模板反馈
    "HOUSE_RECOMMEND": 20, # 户型推荐
    "RENDER_PARAMS": 3, # 发起渲染
    "GENERATING": 3, # 生成中
    "USER_HOUSE_TYPE": 19, # 用户已添加户型

}

TAB_OPTIONS = ['试试AI设计我的家', '户型推荐', '推荐户型', '帮我设计', 
'装修解惑', '灵感案例推荐', 'AI装修问答', '换一批方案', '其他风格', '风格测试', 
'热门案例', '智能生成']

# ==================== 默认值 ====================
DEFAULT_VALUES = {
    "NEW_CONVERSATION_TITLE": "新对话",
    "MAX_SEARCH_RESULTS": 5,
    "MIN_SEARCH_RESULTS": 1,
    "RAG_DOCS_COUNT": 3,
    "RETRY_COUNT": 3
}

# ==================== API配置 ====================
API_CONFIG = {
    "AUTHORIZATION": "Bearer b31682c9-4dae-4f3f-8ed4-3f822e7eeea0",
    "REQUEST_ID": "xxxx",
    "CONTENT_TYPE": "application/json"
}

# ==================== 日志配置 ====================
LOG_CONFIG = {
    "LEVEL": "INFO",
    "FORMAT": "%(levelname)s: %(message)s"
}
