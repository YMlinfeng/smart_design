from langchain_community.embeddings.dashscope import DashScopeEmbeddings
# ==================== 常量配置 ====================
"""
智能家装Agent常量配置模块

包含系统中使用的各种常量定义，包括：
- 对话类型
- 响应类型
- 风格选项
- 品牌选项
- 标签页操作
"""

EMBED = DashScopeEmbeddings(
    dashscope_api_key='sk-a708960cdb7b4bdbbb13ca0db0296b84',  # DashScope API密钥
    model="text-embedding-v3"  # 嵌入模型版本
)

# ==================== Openai api ====================

ALIYUN_API_KEY = "sk-a708960cdb7b4bdbbb13ca0db0296b84"
ALIYUN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1" 
# ==================== 对话类型 ====================
CONVERSATION_TYPES = {
    "SEARCH_COMMUNITY": "定位户型类",
    "KNOWLEDGE": "装修知识类", 
    "UNIVERSAL_CHAT": "通用问答类",
    "POPULAR_BRAND_CASES": "热门品牌案例类别",
    "POPULAR_PRODUCTS": "热门商品类别",
    "APPLY_PRODUCT": "应用商品到户型类",
    "SWITCH_HOUSE_TYPE": "切换户型类",
    "SEE_USER_HOUSE_TYPE": "调用户型类",
    "TRANSFORM_TO_HUMAN": "转人工类",
    "SWITCH_PARAMS": "切换参数类",
    "SWITCH_CASES": "换一批方案类",
    "SMART_DESIGN": "智能设计类",
    "SET_PRODUCT_PARAMS": "确认商品参数类"
    }

# ==================== 路由->节点映射 ====================
def conditional_router(state):
    """条件路由函数"""
    conversation_type = state['conversation_type']
    # 根据对话类型进行路由
    if conversation_type == CONVERSATION_TYPES["SEARCH_COMMUNITY"]:
        return 'get_house_type' # 定位户型类
    elif conversation_type == CONVERSATION_TYPES["UNIVERSAL_CHAT"]:
        return 'universal_chat'  # 通用问答类
    elif conversation_type == CONVERSATION_TYPES["KNOWLEDGE"]:
        return 'rag_run'  # rag知识问答类，装修知识
    elif conversation_type == CONVERSATION_TYPES["POPULAR_BRAND_CASES"]:
        return 'pop_cases'  # 热门品牌案例
    elif conversation_type == CONVERSATION_TYPES["POPULAR_PRODUCTS"]:
        return 'pop_products'   # 热门商品
    elif conversation_type == CONVERSATION_TYPES["APPLY_PRODUCT"]:
        return 'apply_product'  # 应用商品到户型
    elif conversation_type == CONVERSATION_TYPES["SWITCH_HOUSE_TYPE"]:
        return 'switch_house_type'  # 切换户型
    elif conversation_type == CONVERSATION_TYPES["TRANSFORM_TO_HUMAN"]:
        return 'transform_to_human' # 转人工
    elif conversation_type == CONVERSATION_TYPES["SWITCH_PARAMS"]:
        return 'switch_params'  # 切换参数
    elif conversation_type == CONVERSATION_TYPES["SEE_USER_HOUSE_TYPE"]:
        return 'see_user_house_type'  # 查看用户户型
    elif conversation_type == CONVERSATION_TYPES["SWITCH_CASES"]:
        return 'switch_cases'  # 换一批方案
    elif conversation_type == CONVERSATION_TYPES["SMART_DESIGN"]:
        return 'smart_design'  # 智能设计
    elif conversation_type == CONVERSATION_TYPES["SET_PRODUCT_PARAMS"]:
        return 'set_product_params'  # 确认商品参数


# ==================== 响应卡片类型 ====================
RESPONSE_TYPES = {
    "TEXT": 1,           # 文本回复
    "SEARCH_RESULT": 13,  # 搜索结果
    "NO_RESULT": 18,      # 无搜索结果,给出户型识别和户型推荐两种选择
    "BRAND_CASES": 37,    # 分空间筛选品牌案例
    "HOT_PRODUCTS": 33,   # 热门商品
    "SIMILAR_HOUSE": 29,  # 相似户型
    "HOUSE_RECOGNITION": 30,  # 户型识别
    "RECENT_CASES": 6,    # 最近使用的样板间案例
    "CASE_LIST": 6,    # 案例筛选卡片
    "DESIGN_MODE": 38,     # 设计模式选择
    "SET_PRODUCT_PARAMS": 35, # 设置商品生成参数
    "HOUSE_TYPE_HISTORY": 41, # 户型问询(包含历史户型快捷卡)
    "USER_HOUSE_TYPE": 19, # 用户已添加户型
    "SMART_DESIGN": 38, # 选择设计
    "HUMAN_AGENT": 8, # 转人工
    "AI_DESIGN": 39, # AI智能设计
    "CASE_DESIGN": 37, # 分空间筛选案例
    "RENDER": 3 # 发起渲染
}



# ==================== 预设路径输入 ================
# 展示商品到客户家预设输入
SHOW_PRODUCT_TO_CUSTOMER_INPUT = [
    '展示商品到客户家',
    '展示商品到客户',
    '帮我展示商品到客户家',
    '展示商品到户型',
    '展示商品到户型中',
    '展示商品到客户家中',
    '帮我设计房屋',
    '帮我设计',
    '帮我设计我的家',
    '设计我的家',
    '设计房屋',
]

# 热门品牌案例预设输入
POPULAR_BRAND_CASES_INPUT = [
    '热门品牌案例',
    '热门品牌装修案例',
    '帮我看看热门品牌案例',
    '热门案例',
    '热门样板案例',
    '热门装修案例',
    '展示热门品牌案例',
    '使用热门品牌案例',
    '应用热门品牌案例',
    '展示热门案例'
]

# 热门商品预设输入
POPULAR_PRODUCTS_INPUT = [
    '热门商品',
    '热门家具商品',
    '帮我看看热门商品',
    '展示热门商品',
    '热门家具商品',
    '展示一下热门商品',
    '使用热门商品',
    '应用热门商品',
    '展示热门家具商品'
]


# ==================== 风格选项 ====================
STYLE_OPTIONS = [
    "现代", "极简", "轻奢", "奶油", "中式", "欧式", 
    "美式", "法式", "侘寂", "原木", "复古", "北欧"
]

# ==================== 品牌选项 ====================
BRAND_OPTIONS = [
    "简一", "马可波罗", "诺贝尔"
]

# ==================== 标签页操作 ====================
TAB_OPERATIONS = [
    '热门品牌案例', '热门商品', '展示商品到客户家','查看最近使用的样板间','AI智能设计','设置商品参数','转人工'
]


# ==================== 特殊状态类型 ====================
SPECIAL_STATE_TYPES = [32, 3, 6, 33, 34, 36, 37, 38]

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
