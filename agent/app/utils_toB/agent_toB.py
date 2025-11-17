# ==================== 智能家装Agent核心模块 ====================
"""
智能家装Agent核心模块

这是重构后的核心Agent模块，仅保留核心的业务逻辑。
其他功能已拆分到专门的模块中：
- constants.py: 常量配置
- models.py: 数据模型
- llm_manager.py: LLM模型管理
- redis_manager.py: Redis数据库管理
- rag_manager.py: RAG知识库管理
- api_manager.py: API接口管理
"""

# ==================== 导入模块 ====================
import json
import logging
from datetime import datetime
import time
from langgraph.graph import StateGraph, END, START
from langchain_community.vectorstores.faiss import FAISS
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel
# 导入自定义模块
from app.utils_toB.models import GraphState, create_graph_state
from app.utils_toB.llm_manager import router_chain,router_parser, get_llm,switch_params_chain
from app.utils_toB.redis_manager import *
from app.utils_toB.rag_manager import rag_search, rag_answer
from app.utils_toB.api_manager import search_estate, find_house_type
from app.utils_toB.constants import *
from app.utils_toB.prompt import get_title_summary_prompt,get_say_hello_text,get_universal_chat_prompt,get_un_use_product_text
from app.utils_toB.decorators import log_execution_time
# 向量数据库
from app.mq import app_use_qa_searcher
# ==================== 日志配置 ====================
logging.basicConfig(level=LOG_CONFIG["LEVEL"], format=LOG_CONFIG["FORMAT"])
logger = logging.getLogger(__name__)


class InputModel(BaseModel):
    """
    输入模板
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


# ==================== 智能家装Agent工作流 ====================
class AgentDesignWorkflow:
    """
    智能家装Agent工作流类
    
    基于LangGraph构建的智能家装对话系统，通过状态图管理整个对话流程。
    该系统能够理解用户的装修需求，提供个性化的装修建议和案例推荐。
    """
    
    def __init__(self, session_id):
        """
        初始化智能家装Agent工作流
        
        Args:
            session_id (int): 会话ID，用于标识用户对话会话
        """
        self.session_id = session_id
        self.house_type = None
        # 创建状态图工作流
        workflow = StateGraph(GraphState)
        
        # 添加各个处理节点
        workflow.add_node('accept_input', self.accept_input) # 接收输入
        workflow.add_node('say_hello',self.say_hello) # 打招呼
        workflow.add_node('un_use_product',self.un_use_product) # 商品应用失败反馈
        workflow.add_node('tab', self.tab)   # 快捷标签节点，处理快捷标签操作
        workflow.add_node('router_run', self.router_run) # 通过llm意图识别
        workflow.add_node('universal_chat', self.universal_chat) # 通用问答
        workflow.add_node('get_house_type', self.get_house_type) # 定位户型
        workflow.add_node('apply_product',self.apply_product) # 应用商品到户型
        workflow.add_node('pop_cases',self.pop_cases) # 热门品牌案例
        workflow.add_node('pop_products',self.pop_products) # 热门商品
        workflow.add_node('rag_run', self.rag_run) # RAG知识问答
        workflow.add_node('see_user_house_type',self.see_user_house_type)
        workflow.add_node('switch_house_type',self.switch_house_type) # 切换户型
        workflow.add_node('transform_to_human',self.transform_to_human) # 转人工
        workflow.add_node('switch_params',self.switch_params) # 切换参数
        workflow.add_node('next_flow',self.next_flow) # 推进下一步流程
        workflow.add_node('switch_cases',self.switch_cases) # 换一批方案
        workflow.add_node('smart_design',self.smart_design) # 智能设计
        workflow.add_node('set_product_params',self.set_product_params) # 确认商品参数
        # 添加条件边：根据输入类型决定路由
        workflow.add_conditional_edges(
            'accept_input', 
            self.is_tab, 
            {
                'tab': 'tab', 
                'router_run': 'router_run', 
                'next_flow': 'next_flow', 
                'say_hello': 'say_hello', 
                'un_use_product': 'un_use_product',
                'see_user_house_type': 'see_user_house_type',
            }
        )
        # 添加条件边：根据对话类型决定后续处理
        workflow.add_conditional_edges(
            'router_run', 
            conditional_router, 
            {
                'get_house_type': 'get_house_type', # 让用户输入城市小区几室几厅从而确认户型
                'universal_chat': 'universal_chat', # 通用问答
                'rag_run': 'rag_run', # RAG知识问答
                'pop_cases': 'pop_cases', # 热门品牌案例
                'pop_products': 'pop_products', # 热门商品
                'apply_product': 'apply_product', # 应用商品到户型
                'switch_house_type':'switch_house_type', # 切换户型
                'transform_to_human':'transform_to_human', # 转人工
                'see_user_house_type':'see_user_house_type', # 查看用户户型
                'switch_params':'switch_params', # 切换参数类
                'switch_cases':'switch_cases', # 换一批方案
                'smart_design':'smart_design', # 智能设计
                'set_product_params':'set_product_params', # 确认商品参数
            }
        )
        
        # 添加起始边和结束边
        workflow.add_edge(START, 'accept_input')
        workflow.add_edge(
            [
                "tab", "rag_run", "get_house_type", "universal_chat", "set_product_params",
                "switch_house_type", "pop_cases", "pop_products","say_hello",
                "apply_product", "transform_to_human","see_user_house_type",
                "switch_params","next_flow","switch_cases","un_use_product","smart_design"], END)
        
        # 编译工作流
        self.agent = workflow.compile()



    @log_execution_time()
    async def type_6_content(self, state: GraphState):
        s = ''
        if state['styles']:
            styles = "、".join(state['styles'])
            s += f"● 风格偏好:{styles}\n"
        if 13 in state['finish_type_list'] or 14 in state['finish_type_list']:
            s += f"● 城市:{state['search_city']}\n" + f"● 小区:{state['search_area']}\n"
        if state['cur_house_type']:
            s += f"● 户型:{state['cur_house_type']}\n"
        # if state['brand']:
        #     s += f"● 品牌:{state['brand']['query']['keyword']}\n"
        return (
            """根据您的需求\n""" + s +
            """推荐以下案例，可进行以下操作：\n• 选择方案：点击「应用同款」启动参数化适配\n"""
            """• 刷新案例库：点击「换一批」加载新方案（保留原需求）\n• 重定义需求：告知其他需求"""
        )


    @log_execution_time()
    async def initialize(self):
        """初始化Agent，连接Redis，获取户型信息"""
        # logger.info("开始: AgentDesignWorkflow.initialize")
        # 获取用户的户型信息
        try:
            self.house_type = await find_house_type(self.session_id)
        except Exception as e:
            logger.error(f"获取用户户型库已有信息失败: {e}")
            self.house_type = []
        # logger.info("结束: AgentDesignWorkflow.initialize")

    @log_execution_time()
    async def say_hello(self,state:GraphState):
        state['content']=get_say_hello_text()
        state['type']=RESPONSE_TYPES["TEXT"]
        return state

    @log_execution_time()
    async def un_use_product(self,state:GraphState):
        unuse_product_text = ','.join(state['un_use_product'])
        state['content']=get_un_use_product_text().format(unuse_product_text=unuse_product_text)
        state['type']=RESPONSE_TYPES["TEXT"]
        return state

    @log_execution_time()
    async def accept_input(self, state: GraphState):
        """接收并预处理用户输入"""
        print("---------用户输入---------\n", state)
        
        # 初始化状态变量
        state['receive_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        state['output_token'] = 0
        state['finish_time'] = None
        state['input_token'] = 0

        # 更新标题
        # # 初始化
        # if not state.get('conversation_title'):
        #     state['conversation_title'] = '新对话'
        # # 判断是否是新的会话id
        # if not await key_exists(f"task_history1:{self.session_id}"):
        #     # 更新标题
        #     if state['user_input'] in TAB_OPERATIONS:
        #         if state['cur_house_type']:
        #             state['conversation_title'] = state['user_input'] + '-' + state['cur_house_type']
        #         else:
        #             state['conversation_title'] = state['user_input']
        #     else:
        #         # llm 总结标题，仅根据用户输入
        #         sum_title = await self.summary_title(state['user_input'])
        #         state['conversation_title'] = sum_title
        #     print(f"---------更新conversation_title为: {state['conversation_title']}---------")
        # else:
        #     # 判断是否需要补充户型信息
        #     if '-' not in state['conversation_title'] and state.get('cur_house_type'):
        #         state['conversation_title'] = state['conversation_title'] + '-' + state['cur_house_type']

        # 简化标题更新逻辑
        # 安全获取conversation_title，如果不存在则初始化为'新对话'
        state['title_update'] = False
        conversation_title = state['conversation_title']
        logger.info(f'当前标题为：{conversation_title}')
        if conversation_title == '新对话':
            # 取前8个字符
            title = state['user_input'][:8]+'...' if state.get('user_input') else '新对话'
            state['conversation_title'] = title
            if title!=conversation_title:
                state['title_update'] = True
        else:
            print(f'当前标题为：{conversation_title}')
            # 判断是否需要填补小区信息
            cur_house_type = state.get('cur_house_type', '')
            if state['conversation_title'].endswith('...') and cur_house_type != '':
                state['conversation_title'] += cur_house_type
            if state['conversation_title']!=conversation_title:
                state['title_update'] = True
        
        print(f"---------更新会话标题为: {state['conversation_title']}---------")
        return state
    

    @log_execution_time()
    async def router_run(self, state: GraphState):
        """路由节点函数，通过llm意图识别，返回state"""
        logger.info("开始: 进入意图识别节点router_run")
        # 获取历史对话记录
        # logger.info("开始：获取历史对话记录")
        st_time_get_history = time.perf_counter()
        history = await get_conversation_history(self.session_id)
        _dt = (time.perf_counter() - st_time_get_history) * 1000
        # logger.info(f"结束: 获取历史对话记录, 用时 {int(_dt)} ms")
        # 使用路由链进行重试，确保成功解析
        # logger.info("开始：使用路由链进行重试获取response")
        st_time_router_chain = time.perf_counter()
        for i in range(DEFAULT_VALUES["RETRY_COUNT"]):
            logger.info(f"第{i+1}次尝试获取router_chain响应")
            try:
                response = await router_chain.ainvoke({
                    'input': state['user_input'], # 用户输入
                    'history': await self.trans_history(history[-4:]) # 历史对话,仅参考最近两条
                })

                # 记录Token使用情况
                state['input_token'] = response.response_metadata['token_usage']['prompt_tokens'] #token
                state['output_token'] = response.response_metadata['token_usage']['completion_tokens']
                # 规范化llm输出
                response = router_parser.parse(response.content)
                break
            except Exception as e:
                continue
        _dt = (time.perf_counter() - st_time_router_chain) * 1000
        logger.info(f"结束: 使用路由链进行重试获取response, 用时 {int(_dt)} ms")
        # 判断用户输入的对话类型，仅打印3条记录
        print('-----------历史会话-------------\n', await self.trans_history(history[-6:]), '\n------------------------------\n')
        
        # 更新状态中的提取信息
        if response.search_city:
            state['search_city'] = response.search_city
        if response.search_area:
            state['search_area'] = response.search_area
        # if response.search_house_type > 0:
        #     print("---------LLM提取的户型为---------\n", response.search_house_type)
        #     state['search_house_type'] = str(response.search_house_type)
        state['rag_query'] = response.rag_query
        if response.styles:
            state['styles'] = response.styles
        state['conversation_type'] = response.conversation_type
        if response.switch_params_dict:
            self.switch_params_dict = response.switch_params_dict
        # 路由兜底，返回通用问答
        if not state['conversation_type']:
            state['conversation_type'] = CONVERSATION_TYPES["UNIVERSAL_CHAT"]
        logger.info("结束: router_run")
        return state

    async def trans_history(self, history: list[dict]):
        """转换历史对话记录为字符串格式"""
        history_str = ''
        for data in history:
            try:
                if data['role'] == 'user':
                    history_str += f"user:{data['user_input']}\n\n"
                elif data['role'] == 'assistant':
                    history_str += f"AI:{data['content']}\n\n"
            except Exception as e:
                pass
        return history_str

    async def summary_title(self, user_input: str) -> str:
        """
        使用LLM总结用户输入生成对话标题,只输出标题内容即可！
        
        Args:
            user_input (str): 用户输入内容
            
        Returns:
            str: 生成的对话标题
        """
        try:
            # 获取LLM实例和提示词模板
            llm = get_llm('qwen-flash',temperature=0.0,top_p=0.9)
            # 创建提示词模板
            summary_title_prompt = PromptTemplate.from_template(get_title_summary_prompt())
            # 调用LLM生成标题
            response = await llm.ainvoke(summary_title_prompt.format(user_input=user_input))
            # 提取标题内容，去除可能的引号
            title = response.content.strip().strip('"').strip("'")
            # 限制标题长度，避免过长
            if len(title) > 20:
                title = title[:20] + "..."
            return title
        except Exception as e:
            logger.error(f"生成标题时出错: {e}")
            # 如果出错，返回默认标题
            return f"新对话-{datetime.now().strftime('%m%d')}"

    @log_execution_time()
    async def get_house_type(self, state: GraphState):
        """创建户型"""
        logger.info("开始: 进入小区搜索节点get_house_type")
        # 初始化区域和户型状态
        # 检查是否只提供了城市或小区中的一个（不完整信息）
        if not state['search_area'] or not state['search_city']:
            state['type'] = RESPONSE_TYPES["HOUSE_TYPE_HISTORY"]
            state['content'] = """请完整提供以下住宅信息：\n1.所在城市（必填）\n2.小区/楼盘名称（必填）\n示例格式：北京市橡树湾 / 成都市麓湖生态城\n注：数据加密处理，仅用于调取对应户型图"""
        else:
            # 清除确认户型状态
            if 13 in state['finish_type_list']:
                state['finish_type_list'].remove(13)
            if 14 in state['finish_type_list']:
                state['finish_type_list'].remove(14)
            # 搜索小区
            # print(f'开始搜索城市：{state["search_city"]}，小区：{state["search_area"]}')
            search_result = await search_estate(state['search_city'], state['search_area'])
            state['search_result'] = search_result['data'][:5]
            logger.info(f'小区搜索结果：{search_result}\n结果数量：{len(search_result["data"])}')
            if DEFAULT_VALUES["MIN_SEARCH_RESULTS"] <= len(search_result['data']) <= DEFAULT_VALUES["MAX_SEARCH_RESULTS"]:
                # 找到相似的小区
                state['type'] = RESPONSE_TYPES["SEARCH_RESULT"]
                state['content'] = """根据您的小区名称查找到以下结果,请进一步确认您的小区名称。"""
                # logger.info("结束: get_house_type (返回搜索结果)")
                return state
            elif len(search_result['data']) == 0:
                # 没有找到任何小区，提供相似户型或AI识别
                state['type'] = RESPONSE_TYPES["NO_RESULT"]
                state['content'] = """抱歉，未搜到相关内容，您可以先进行以下操作:\n1.户型推荐\n●系统将基于空间特征推荐各个面积区域的户型，推荐常用户型\n\n2.户型识别\n●通过AI对户型图进行识别，自行创建户型两步即达，一分钟速享"""        
                logger.info("结束: get_house_type (无搜索结果)")
                return state
            else:
                # 结果过多，提示用户补充完整信息
                state['type'] = RESPONSE_TYPES["TEXT"]
                state['content'] = """根据您的输入,小U搜索到多于5个小区结果信息,为精准匹配户型资源,请您补充以下关键信息:\n1. 城市名称(格式:XX市)\n2. 小区完整命名(含分期/楼栋等标识)\n示例:北京市万柳书院一期/杭州市杨柳\n郡四期\n注:数据加密处理,仅用于调取对应户型图"""
                # logger.info("结束: get_house_type (结果过多)")
                return state
        # logger.info("结束: get_house_type (已定义户型)")
        return state

    @log_execution_time()
    async def switch_house_type(self, state: GraphState):   
        """切换户型流程"""
        logger.info("开始: 进入切换户型节点switch_house_type")
        # 删除当前户型信息
        state['search_area'] = None
        state['search_city'] = None
        state['cur_house_type'] = None
        state['search_result'] = []
        if 13 in state['finish_type_list']:
            state['finish_type_list'].remove(13)
        if 14 in state['finish_type_list']:
            state['finish_type_list'].remove(14)
        state['type'] = RESPONSE_TYPES["TEXT"]
        state['content'] = """请提供以下住宅信息：\n1.所在城市（必填）\n2.小区/楼盘名称（必填）\n示例格式：北京市橡树湾 / 成都市麓湖生态城\n注：数据加密处理，仅用于调取对应户型图"""
        # logger.info("结束: switch_house_type")
        return state

    @log_execution_time()
    async def smart_design(self,state:GraphState):
        """进入设计流程"""
        # 没确认户型
        # if not state['define_house_type']:
        #     state['type'] = RESPONSE_TYPES["TEXT"]
        #     state['content'] = """请提供以下住宅信息：\n1.所在城市（必填）\n2.小区/楼盘名称（必填）\n示例格式：北京市橡树湾 / 成都市麓湖生态城\n注：数据加密处理，仅用于调取对应户型图"""
        #     return state
        # elif not state['define_product_sku']:
        #     state['type'] = RESPONSE_TYPES["SET_PRODUCT_PARAMS"]
        #     state['content'] = """请确认商品参数吧"""
        #     return state
        # else:
        #     state['type'] = RESPONSE_TYPES["DESIGN_MODE"]
        #     state['content'] = """请根据您的需求选择生成模式:\n1. 样板间设计\n· 精准还原品牌案例样板\n2. Al 智能设计\n· 快速生成方案"""
        
        # 经过agent灵活处理
        # 触发生成模式选择
        state['type'] = RESPONSE_TYPES["DESIGN_MODE"]
        state['content'] = """请根据您的需求选择生成模式:\n1. 样板间设计\n· 精准还原品牌案例样板\n2. Al 智能设计\n· 快速生成方案"""
        return state
        
    
    @log_execution_time()
    async def set_product_params(self,state:GraphState):
        """设置商品参数"""
        state['type'] = RESPONSE_TYPES["SET_PRODUCT_PARAMS"]
        state['content'] = """请确认商品参数吧"""
        return state

    async def see_user_house_type(self,state:GraphState):
        state['type']=RESPONSE_TYPES['USER_HOUSE_TYPE'] # 用户已添加户型
        state['content']="""小U在您的家中找到以下户型,可以直接选择使用,也可以输入城市小区来查找新的户型哦"""
        return state

    @log_execution_time()
    async def switch_params(self,state:GraphState):
        # 切换风格/品牌
        response=await switch_params_chain.ainvoke({'input':state['user_input']})
        print('---------切换参数响应---------\n',response)
        response_str = ''
        # 更新状态
        for param in response.switch_params:
            if param in ['风格','品牌']:
                if response.switch_params_dict[param]:
                    if param=='风格':
                        if response.pre_params[param] and not response.pre_params[param].strip():
                            state['type']=RESPONSE_TYPES['TEXT'] # 文本回复
                            state['content']="""小U暂时不支持您切换的风格,您可以尝试其他风格哦"""
                            return state
                        state['styles']=[response.switch_params_dict[param]]
                        state['type']=RESPONSE_TYPES['CASE_LIST'] # 筛选模板反馈
                        state['content']=await self.type_6_content(state)
                        state['content']=state['content'].replace(response.switch_params_dict[param],response.pre_params[param])
                        return state
                    elif param=='品牌':
                        if response.pre_params[param] and not response.pre_params[param].strip():
                            state['type']=RESPONSE_TYPES['TEXT'] # 文本回复
                            state['content']="""小U暂时不支持您切换的品牌,您可以尝试其他品牌哦"""
                            return state
                        state['brand']=response.switch_params_dict[param]
                        state['type']=RESPONSE_TYPES['TEXT'] # 文本回复
                        return state
                    response_str+=f"好的，小U已经成功应用{response.switch_params_dict[param]}{param}哦\n"
                else:
                    response_str+=f"请直接告诉我们您要切换的{param}是什么哦\n"
        state['content']=response_str
        self.type_6=0
        return state

    # 通用问答类函数，回答常规问题
    @log_execution_time()
    async def universal_chat(self,state:GraphState):
        # 获取LLM实例和提示词模板
        logger.info("开始: 进入通用对话节点universal_chat")
        llm = get_llm('qwen-flash',temperature=1.0,top_p=0.8) # 调用qwen-flash快速回答通用问题
        # 检索app使用相关问答文档
        # app_use_docs=await app_use_faiss.asimilarity_search(state['user_input'],k=1)
        start_time = time.time()
        app_use_docs  = app_use_qa_searcher.search(state['user_input'],k=1)
        end_time = time.time()
        print(f'检索app_use文档耗时: {end_time - start_time} 秒')
        docs_content = '\n'.join([doc['answer']+'\n'+doc['question'] for doc in app_use_docs])
        print(f'检索到的文档app_use_docs: {docs_content}')
        chat_prompt = get_universal_chat_prompt()
        # 调用LLM生成回答
        response = await llm.ainvoke(chat_prompt.format(user_input=state['user_input'],app_use_docs=docs_content))
        # 提取回答内容，去除可能的引号
        answer = response.content.strip().strip('"').strip("'")
        # 返回回答
        state['content']=answer
        state['type']=1
        # logger.info("结束: universal_chat")
        return state

    async def transform_to_human(self,state:GraphState):
        state['type']=RESPONSE_TYPES["HUMAN_AGENT"]
        state['content']="""好的，小U将为您转接人工客服，请稍等。"""
        return state
    
    # async def switch_style(self,state:GraphState):
        
    #     return state

    @log_execution_time()
    async def rag_run(self, state: GraphState):
        """执行RAG知识问答"""
        logger.info("开始: 开始进入装修知识rag节点rag_run")
        # 从知识库中检索相关文档
        docs = await rag_search(query=state['rag_query'], k=DEFAULT_VALUES["RAG_DOCS_COUNT"])
        
        # 使用RAG链生成回答
        response = await rag_answer(query=state['rag_query'], docs=docs)
        
        # 记录Token使用情况
        state['input_token'] = response.response_metadata['token_usage']['prompt_tokens']
        state['output_token'] = response.response_metadata['token_usage']['completion_tokens']
        
        # 处理回答内容，将*符号替换为●符号
        response_content = response.content
        state['content'] = response_content.replace("*", "•")
        state['type'] = RESPONSE_TYPES["TEXT"]
        state['switch_intelligent'] = 0
        logger.info("结束: rag_run")
        return state

    @log_execution_time()
    async def is_tab(self, state: GraphState):
        """判断用户输入是否为标签页操作"""
        logger.info('开始：is_tab')
        state['user_input'] = state['user_input'].strip()
        if state['user_input'] in ["你好","在吗","你好呀","嗨","哈喽","你好呀！","hi","哈喽！","小U","这是什么"]:
            return 'say_hello'
        # 判断是否是商品应用失败反馈
        # if state['un_use_product']:
        #         return 'un_use_product'
        # 检查是否为标签页操作
        if state['cur_flow_finish']:
            logger.info("is_tab -> 路由到下一步流程节点next_flow")
            return 'next_flow'
        if state['user_input'] in TAB_OPERATIONS:
            logger.info("is_tab -> 路由到标签处理节点tab")
            return 'tab'
        # 检查当前状态是否为需要标签页处理的状态
        elif state['type'] in SPECIAL_STATE_TYPES:
            logger.info("is_tab -> 路由到标签处理节点tab")
            return 'tab'
        
        logger.info("结束：is_tab,路由到路由执行节点router_run")
        return 'router_run'

    @log_execution_time()
    async def tab(self, state: GraphState):
        """处理标签页操作"""

        # 初始化标签页状态
        state['conversation_type'] = ''

        if state['user_input'] in SHOW_PRODUCT_TO_CUSTOMER_INPUT:
            # state['type'] = RESPONSE_TYPES["HOUSE_TYPE_HISTORY"] # 41,户型问询（包含历史户型快捷卡）
            # state['content'] = """请提供以下住宅信息：\n1.所在城市（必填）\n2.小区/楼盘名称（必填）\n示例格式：北京市橡树湾 / 成都市麓湖生态城\n注：数据加密处理，仅用于调取对应户型图"""

            # 跳转到next_flow流程
            state = await self.next_flow(state)
            # return state
        elif state['user_input'] in POPULAR_BRAND_CASES_INPUT: # 给出热门案例选择卡片
            state['type'] = RESPONSE_TYPES["BRAND_CASES"]
            state['content'] = """已为您查找以下热门样板案例，试试一键应用同款吧~"""
        elif state['user_input'] == '查看最近使用的样板间':
            state['type'] = RESPONSE_TYPES["RECENT_CASES"]
            state['content'] = """以下是最近使用的样板案例，试试一键应用同款吧~"""
        elif state['user_input'] in POPULAR_PRODUCTS_INPUT:
            state['type'] = RESPONSE_TYPES["HOT_PRODUCTS"]
            state['content'] = """已为您查找以下品牌热门家具商品，试试生成设计搭配效果吧~"""
        # elif state['user_input'] == '相似户型':
        #     state['type'] = RESPONSE_TYPES["SIMILAR_HOUSE"]
        #     state['content'] = """已为您查找以下相似户型，试试一键应用同款吧~"""
        elif state['user_input'] == 'AI智能设计':
            state['type'] = RESPONSE_TYPES["SMART_DESIGN"]
            state['content'] = """请选择需要智能设计的方案参数"""
        elif state['user_input'] == '设置商品参数':
            state['type'] = RESPONSE_TYPES["SET_PRODUCT_PARAMS"]
            state['content'] = """请确认商品参数吧"""
        elif state['user_input'] == '转人工':
            state['type'] = RESPONSE_TYPES["HUMAN_AGENT"]
            state['content'] = """好的，小U将为您转接人工客服，请稍等。"""


        # elif state['user_input'] == '开启AI户型识别':
        #     state['type'] = RESPONSE_TYPES["HOUSE_RECOGNITION"]
            # state['content'] = """已为您查找以下户型识别，试试一键应用同款吧~"""
        # elif state['type'] == RESPONSE_TYPES["RECENT_CASES"]:
            # for style in STYLE_OPTIONS:
            #     if style in state['user_input'] and style not in state['styles']:
            #         state['styles'].append(style)
            # response = await brand_chain.ainvoke({'input': state['user_input']})
            # if response.brand:
            #     state['brand'] = {
            #         "query": {
            #             "type": "case",
            #             "keyword": response.brand,
            #             "limit": 10,
            #             "offset": 0
            #         },
            #         "context": {
            #             "session_id": self.session_id
            #         }
            #     }
            # if state['define_house_type']:
            #     state['type'] = RESPONSE_TYPES["DESIGN_MODE"]
            #     state['content'] = """请根据您的需求选择生成模式:\n1. 样板间设计\n· 精准还原品牌案例样板\n2. Al 智能设计\n· 快速生成方案"""
        return state # 回传给后端

    @log_execution_time()
    async def apply_product(self,state:GraphState):
        """应用商品到户型流程"""
        logger.info("开始: apply_product")
        state['type'] = RESPONSE_TYPES["HOUSE_TYPE_HISTORY"] # 41,户型问询（包含历史户型快捷卡）
        # 引导定位户型
        state['content'] = """请提供以下住宅信息：\n1.所在城市（必填）\n2.小区/楼盘名称（必填）\n示例格式：北京市橡树湾 / 成都市麓湖生态城\n注：数据加密处理，仅用于调取对应户型图"""
        return state

    @log_execution_time()
    async def pop_cases(self,state:GraphState):
        """热门品牌案例流程"""
        logger.info("开始: pop_cases")
        state['type'] = RESPONSE_TYPES["BRAND_CASES"]
        state['content'] = """已为您查找以下热门样板案例，试试一键应用同款吧~"""
        # logger.info("结束: pop_cases")
        return state

    @log_execution_time()
    async def pop_products(self,state:GraphState):
        """热门商品流程"""
        logger.info("开始: pop_products")
        state['type'] = RESPONSE_TYPES["HOT_PRODUCTS"] # 热门商品卡片
        state['content'] = """已为您查找到以下品牌热门家具商品，试试生成设计搭配效果吧~"""
        logger.info("结束: pop_products")
        return state

    async def next_flow(self,state:GraphState):
        """确定下一步流程"""
        # 还原state['cur_flow_finish']
        logger.info("开始: next_flow")
        state['cur_flow_finish'] = False
        if 13 in state['finish_type_list'] or 14 in state['finish_type_list']:
            if 35 not in state['finish_type_list']:
                state['type'] = RESPONSE_TYPES["SET_PRODUCT_PARAMS"]
                state['content'] = """请确认商品参数吧"""
                return state
            else:
                if state['generation_type'] == '1':
                    # AI智能设计
                    state['type'] = RESPONSE_TYPES["AI_DESIGN"]
                    return state
                elif state['generation_type'] == '2':
                    # 案例设计
                    state['type'] = RESPONSE_TYPES["CASE_DESIGN"]
                    return state
                else:
                    # 设计模式选择
                    state['type'] = RESPONSE_TYPES["DESIGN_MODE"]
                    state['content'] = """请根据您的需求选择生成模式:\n1. 样板间设计\n· 精准还原品牌案例样板\n2. Al 智能设计\n· 快速生成方案"""
                    return state
        else:
            state['type'] = RESPONSE_TYPES["HOUSE_TYPE_HISTORY"] # 41,户型问询（包含历史户型快捷卡）
            state['content'] = """请提供以下住宅信息：\n1.所在城市（必填）\n2.小区/楼盘名称（必填）\n示例格式：北京市橡树湾2期/成都市麓湖生态城\n注：数据仅用于调取对应户型图资源"""
        return state
    @log_execution_time()
    async def switch_cases(self,state:GraphState):
        """换一批方案流程"""
        logger.info("开始: switch_cases")
        state['type'] = RESPONSE_TYPES["CASE_LIST"] # 换一批方案卡片
        state['switch_cases'] = True
        state['content'] = """已为您切换的案例，点击案例卡片可查看完整设计方案，挑选您喜欢的方案应用同款吧"""
        logger.info("结束: switch_cases")
        return state

    @log_execution_time()
    async def run(self, state: GraphState):
        """运行智能家装Agent工作流"""
        # logger.info("开始: AgentDesignWorkflow.run")
        # 初始化Agent
        await self.initialize()
        
        # try:
        #     # 运行工作流
        #     state = await self.agent.ainvoke(state)
        # except Exception as e:
        #     # 处理异常情况
        #     logger.error(e)
        #     state['type'] = RESPONSE_TYPES["TEXT"]
        #     state['content'] = f"小U出错了,请稍后再试......\n报错：{e}"

        state = await self.agent.ainvoke(state)
        # 设置最终状态
        state['role'] = 'assistant'
        state['finish_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # logger.info("结束: AgentDesignWorkflow.run")
        return state


# ==================== 设计助手主类 ====================
class DesignAssistant:
    """
    设计助手主类
    
    这是智能家装系统的入口类，负责管理整个对话流程。
    它封装了Agent_design工作流，提供了更高级的接口来处理用户请求。
    项目启动时仅需要初始化设计助手即可，后续通过设计助手处理用户输入
    """
    
    def __init__(self, data: dict):  
        """初始化设计助手"""
        self.data = data # 新接收数据
        self.agent = AgentDesignWorkflow(session_id=data['conversation_id'])
        self.state = None
        self.history = None
    @log_execution_time()
    async def initialize(self):
        """初始化设计助手"""
        logger.info("开始: DesignAssistant.initialize")
        # 获取或创建历史记录(通过conversation_id获取或者创建历史记录)
        self.history = await get_conversation_history(self.data['conversation_id'])
        # 确保history是列表类型（防御性编程）
        if not isinstance(self.history, list):
            logger.error(f"历史记录类型不正确，期望list，实际为{type(self.history)}，值: {self.history}，将重置为空列表")
            self.history = []
        # 添加当前用户输入到历史记录
        self.data['role'] = 'user' # 角色初始化
        self.history.append(self.data)
        logger.info(f'用户输入state: {self.data}')
        # 恢复或创建状态
        self.state = await get_session_state(self.data['conversation_id'])
        if self.state:
            logger.info("存在历史对话，更新state")
            logger.info("历史state: %s", self.state)
            # 若存在历史对话，则更新state
            # 确保所有参数存在，不存在则使用默认值
            default_state = create_graph_state(self.data)
            # 去除额外的参数
            extra_keys = []
            for key in self.state:
                if key not in default_state:
                    extra_keys.append(key)
            for key in extra_keys:
                del self.state[key]
            for key, value in default_state.items():
                if key not in self.state:
                    self.state[key] = value
             # todo:确认哪些参数需要更新，哪些参数保持历史值就行
            # 确保所有列表类型的字段都是列表
            list_fields = ['finish_type_list', 'styles', 'search_result']
            for field in list_fields:
                if field in self.state and not isinstance(self.state[field], list):
                    logger.warning(f"状态字段 {field} 类型不正确，期望list，实际为{type(self.state[field])}，将重置为空列表")
                    self.state[field] = []
            if 'finish_type' in self.data and int(self.data['finish_type']) in [13,14,35,33,37]:
                self.data['cur_flow_finish'] = True
            if 'generation_type' in self.data and self.data['generation_type'] in ['1','2']:
                logger.info(f"完成生成模式选择，设置cur_flow_finish为True")
                self.data['cur_flow_finish'] = True
                # 补充你用户输入的流程结束信息
            for key, value in self.data.items():
                # 更新当前完成流程类型
                if key=='finish_type_list':
                    continue
                elif key == 'finish_type' and value not in self.state['finish_type_list']:
                    # 确保 finish_type_list 是列表类型
                    if not isinstance(self.state['finish_type_list'], list):
                        logger.warning(f"finish_type_list类型不正确，期望list，实际为{type(self.state['finish_type_list'])}，将重置为空列表")
                        # self.state['finish_type_list'] = []
                    self.state['finish_type_list'].append(int(value))
                    if value ==37 and 35 not in self.state['finish_type_list']:
                        self.state['finish_type_list'].append(35)
                    self.state['finish_type'] = "" # 清空列表
                else:
                    self.state[key] = value                
            logger.info("更新后的state: %s", self.state)
        else:
            # 若不存在历史对话，则创建状态
            logger.info("不存在历史对话，创建state")
            # 使用 create_graph_state 函数，自动用默认值补充缺失的参数
            self.state = create_graph_state(self.data)
            logger.info("新创建的state: %s", self.state)
        logger.info("结束: DesignAssistant.initialize")
            
    @log_execution_time()
    async def process_input(self) -> dict:
        """处理用户输入"""
        # logger.info("开始: DesignAssistant.process_input")
        # 初始化助手
        await self.initialize()
        
        # 运行Agent工作流 start-->accept_input-->[router_run or tab]-->END(除了accept_input和)
        result: dict = await self.agent.run(state=self.state)
        # 记录结果
        # logger.info("---result---\n %s", result)
        # 更新历史记录和状态
        result['role'] = 'assistant' # 角色切换为assistant
        # 确保history是列表类型（防御性编程）
        if not isinstance(self.history, list):
            logger.error(f"历史记录类型不正确，期望list，实际为{type(self.history)}，值: {self.history}，将重置为空列表")
            self.history = []
        self.history.append(result)
        logger.info(f'agent输出result: {result}')
        result['finish_type'] = "" # 复原当前流程类型
        # result['cur_flow_finish'] = False # 复原当前流程完成状态
        if 'cur_flow_finish' in result:
            del result['cur_flow_finish']
        # result['finish_type_list'] = [] # 清空已结束的流程类型列表
        await set_session_state(self.data['conversation_id'], result)
        await set_conversation_history(self.data['conversation_id'], self.history)
        # logger.info(f'历史记录最后两条: {self.history[-2:]}')
        # logger.info("结束: DesignAssistant.process_input")

        return result
        

