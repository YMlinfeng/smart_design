# 标准库导入
import asyncio
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import *

# 第三方库导入
import httpx
import redis
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel

# 本地模块导入
from app.config import *
from app.mq import app_use_qa_searcher
from app.utils.api_manager import find_house_type, search_estate
from app.utils.constants import *
from app.utils.decorators import log_execution_time
from app.utils.llm_manager import (
    get_llm,
    router_chain,
    router_parser,
    switch_params_chain
)
from app.utils.models import GraphState
from app.utils.prompt import get_say_hello_text, get_universal_chat_prompt
from app.utils.rag_manager import rag_answer, rag_search
from app.utils.redis_manager import get_redis_value, key_exists, set_redis_value

# 配置日志（可选：设置级别和格式）
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
# 获取一个 logger 实例
logger = logging.getLogger(__name__)

class InputModel(BaseModel):
    user_input: str
    type: int
    search_city: str
    search_area: str
    define_area: bool
    define_house_type: bool
    search_house_type: str
    styles: list[str]
    conversation_id: int
    content: str
    need_house_type: bool
    conversation_type: str
    role: str
    rag_query: str
    is_switch_scenes: int
    switch_intelligent: int
    search_result: list[dict]


@dataclass
class Agent_design:
    """
    agent设计类，负责整个对话流程的控制和状态管理
    Args:
        session_id: 对话会话ID
    Attributes:
        session_id: 对话会话ID
        type_6: 是否已经点击应用示例标识
        workflow: 对话流程图
        agent: 编译后的对话流程
        house_type: 户型信息
    """
    global redis, router_chain, rag_chain

    def __init__(self, session_id):
        self.session_id = session_id
        self.type_6 = None
        workflow = StateGraph(GraphState)
        workflow.add_node('tab', self.tab)
        workflow.add_node('router_run', self.router_run)
        workflow.add_node('area', self.area)
        workflow.add_node('area_style', self.area_style)
        workflow.add_node('rag_run', self.rag_run)
        workflow.add_node('accept_input', self.accept_input)
        workflow.add_node('design', self.design)
        workflow.add_node('universal_chat', self.universal_chat)  # 添加通用问答节点
        workflow.add_node('design_house', self.design_house)  # 添加设计房屋节点
        workflow.add_node('switch', self.switch)
        workflow.add_node("switch_params", self.switch_params)
        workflow.add_node("see_user_house_type", self.see_user_house_type)
        workflow.add_node('area_style_area', self.area_style_area)
        workflow.add_node("area_house_type", self.area_house_type)
        workflow.add_node("say_hello", self.say_hello)
        workflow.add_conditional_edges(
            'accept_input',
            self.is_tab,
            {'tab': 'tab', 'router_run': 'router_run', 'say_hello': 'say_hello'}
        )
        workflow.add_conditional_edges(
            'router_run',
            conditional_router,
            {
                "say_hello": "say_hello",
                "area_house_type": "area_house_type",
                "switch": "switch",
                'area': 'area',
                'area_style': 'area_style',
                'rag_run': 'rag_run',
                'universal_chat': 'universal_chat',
                'design_house': 'design_house',
                'switch_params': 'switch_params',
                "see_user_house_type": "see_user_house_type",
                "area_style_area": "area_style_area"
            }
        )
        workflow.add_edge(START, 'accept_input')
        workflow.add_edge(
            [
                "say_hello", "tab", "area", "area_style", "rag_run", "design",
                "universal_chat", "design_house", "area_style_area", "switch",
                "switch_params", "see_user_house_type", "area_house_type"
            ],
            END
        )
        self.agent = workflow.compile()
        self.house_type = None

    @log_execution_time()
    async def initialize(self):
        if await key_exists(f"type_6:{self.session_id}"):
            self.type_6 = int(await get_redis_value(f"type_6:{self.session_id}"))
        else:
            await set_redis_value(f"type_6:{self.session_id}", 0)
            self.type_6 = 0
        try:
            self.house_type = await find_house_type(self.session_id)
        except Exception as e:
            print('获取用户户型库已有信息失败', e)
            self.house_type = []

    @log_execution_time()
    async def rag_run(self, state: GraphState):
        """执行RAG知识问答"""
        logger.info("开始: rag_run")
        # 从知识库中检索相关文档
        docs = await rag_search(query=state['rag_query'], k=DEFAULT_VALUES["RAG_DOCS_COUNT"])

        # 使用RAG链生成回答
        response = await rag_answer(query=state['rag_query'], docs=docs)
        print('-----------RAG回答-------------\n', response.content, '\n------------------------------\n')

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
    async def accept_input(self, state: GraphState):
        print("---------用户输入---------\n", state)
        state['need_house_type'] = True
        state['receive_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        state['output_token'] = 0
        state['finish_time'] = None
        state['input_token'] = 0
        state['brand'] = {}
        return state

    @log_execution_time()
    async def say_hello(self, state: GraphState):
        state['content'] = get_say_hello_text()
        state['type'] = RESPONSE_TYPES["TEXT"]
        return state

    @log_execution_time()
    async def area_style(self, state: GraphState):
        if state['styles'] or state['brand']:
            return await self.area(state)
        state['type'] = RESPONSE_TYPES["ASK_STYLE"]
        state['content'] = """抱歉!由于您提供的风格偏好/品牌偏好我们目前无法为您精准匹配,您可以从以下类型中选择最多三种风格,
                也可以直接发送文字描述,或者给我某品牌案例,小U将为您精准匹配对应案例"""
        state['switch_intelligent'] = 0
        return state

    @log_execution_time()
    async def define_area(self, state: GraphState):
        areas = []
        for house_type in self.house_type:
            if (house_type['sname'] in state['search_city'] or
                    state['search_city'] in house_type['sname']):
                if (house_type['state_name'] in state['search_area'] or
                        state['search_area'] in house_type['state_name']):
                    areas.append(house_type['state_name'])
        return list(set(areas))

    @log_execution_time()
    async def area(self, state: GraphState):
        state['define_area'] = False
        state['define_house_type'] = False
        if (any([state['search_area'], state['search_city']]) and
                not all([state['search_area'], state['search_city']])):
            state['type'] = RESPONSE_TYPES["TEXT"]
            state['content'] = """请将城市与小区一并提供给我"""
            return state
        areas = await self.define_area(state)
        if len(areas) == 1:
            state['search_area'] = areas[0]
            state['define_area'] = True
            state['type'] = RESPONSE_TYPES['HOUSE_TYPE_RESULT']  # 户型搜索结果
            state['content'] = (
                f"小U在您的户型库中已默认确认您的小区是:{state['search_area']},"
                f"若有误请及时更改小区\n以下是该小区的户型,请确认您家的户型,也可以手动上传噢"
            )
        else:
            search_result = await search_estate(state['search_city'], state['search_area'])
            state['search_result'] = search_result['data']
            if search_result['data']:
                state['type'] = RESPONSE_TYPES['ESTATE_RESULT_FEEDBACK']  # 小区结果反馈
                state['content'] = """根据您的小区名称查找到以下结果,请进一步确认您的小区名称。"""
            else:
                state['type'] = RESPONSE_TYPES['NO_ESTATE_RESULT']  # 未搜索到小区
                state['content'] = (
                    """抱歉，未搜到您的小区，您可以先进行以下操作:\n1.户型推荐\n"""
                    """●系统将基于空间特征推荐各个面积区域的户型,推荐常见户型\n\n"""
                    """2.户型识别\n●通过AI对户型图进行识别,自行创建户型两步即达,一分钟速享"""
                )
        return state

    @log_execution_time()
    async def search_house(self, conversation_id):
        """调用小区搜索API并返回房屋数量"""
        url = search_house_url
        payload = {
            "conversation_id": conversation_id
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()  # 确保请求成功
            return response.json().get('data', {}).get('house_count', 0)

    @log_execution_time()
    async def router_run(self, state: GraphState):
        if await key_exists(f"task_history1:{self.session_id}"):
            history = json.loads(await get_redis_value(f"task_history1:{self.session_id}"))
        else:
            history = []
        for _ in range(3):
            try:
                response = await router_chain.ainvoke({
                    'input': state['user_input'],
                    'history': await self.trans_history(history)
                })
                state['input_token'] = response.response_metadata['token_usage']['prompt_tokens']
                state['output_token'] = response.response_metadata['token_usage']['completion_tokens']
                response = router_parser.parse(response.content)
                break
            except Exception as e:
                continue
        print('-----------历史会话-------------\n', await self.trans_history(history[-6:]), '\n------------------------------\n')
        # 路由提取信息后更新状态
        if response.search_city:
            state['search_city'] = response.search_city
        if response.search_area:
            state['search_area'] = response.search_area
        if response.search_house_type > 0:
            print("---------LLM提取的户型为---------\n", response.search_house_type)
            state['search_house_type'] = str(response.search_house_type)
        state['rag_query'] = response.rag_query
        if response.styles:
            state['styles'] = response.styles
        if response.brand:
            state['brand'] = {
                "query": {
                    "type": "case",
                    "keyword": response.brand,
                    "limit": 10,
                    "offset": 0
                },
                "context": {"session_id": self.session_id}
            }
        logger.info("---result11---\n %s", response)
        state['conversation_type'] = response.conversation_type
        if response.conversation_type == '打招呼类':
            state['content'] = response.content
        return state

    @log_execution_time()
    async def trans_history(self, history: list[dict]):
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

    @log_execution_time()
    def is_tab(self, state: GraphState):
        print("-----用户输入的内容-----\n", state['user_input'], "\n")
        state['user_input'] = state['user_input'].strip()
        user_input = state['user_input']
        if user_input in ["你好", "在吗", "你好呀", "嗨", "哈喽", "你好呀！", "hi", "哈喽！", "小U", "这是什么"]:
            return 'say_hello'
        elif user_input in TAB_OPTIONS:
            return 'tab'
        elif state['type'] in [18, 5, 14, 19, 20, 32, 3, 6]:
            return 'tab'
        return 'router_run'

    @log_execution_time()
    async def switch(self, state: GraphState):
        # 换一批方案
        state['switch_intelligent'] = 1
        state['type'] = RESPONSE_TYPES['CASE_LIST']  # 筛选模板反馈
        state['content'] = """以下是为您切换的案例，点击案例卡片可查看完整设计方案，挑选您喜欢的方案应用同款吧"""
        return state

    @log_execution_time()
    async def tab(self, state: GraphState):
        state['conversation_type'] = ''
        state['switch_intelligent'] = 0
        if state['user_input'] == '试试AI设计我的家' or state['user_input'] == '帮我设计':
            try:
                # 查找用户户型库已有信息
                house_num = await self.search_house(state['conversation_id'])
            except Exception as e:
                house_num = 0
            if house_num > 1:
                state['type'] = RESPONSE_TYPES['USER_HOUSE_TYPE']  # 用户已添加户型
                state['content'] = """小U在您的家中找到以下户型,可以直接选择使用,您也可以输入城市小区查找使用其他户型"""
            elif house_num == 1:
                print("---------用户户型库已有信息---------\n", self.house_type)
                state['type'] = RESPONSE_TYPES['CASE_LIST']  # 筛选模板反馈
                state['define_area'] = True
                state['define_house_type'] = True
                state['search_area'] = self.house_type[0]['state_name']
                state['search_city'] = self.house_type[0]['sname']
                state['search_house_type'] = self.house_type[0]['name']
                state['content'] = await self.type_6_content(state)
            else:
                state['type'] = RESPONSE_TYPES['TEXT']  # 文本回复
                state['content'] = """请提供以下住宅信息：\n1.所在城市（必填）\n2.小区/楼盘名称（必填）\n示例格式：北京市橡树湾 / 成都市麓湖生态城\n注：数据加密处理，仅用于调取对应户型图"""
        elif state['user_input'] == '灵感案例推荐' or state['user_input'] == "热门案例":
            state['type'] = RESPONSE_TYPES['CASE_LIST']  # 筛选模板反馈
            # 此时聊天界面弹出热门案例功能卡片
            self.type_6 = 0
            state['content'] = """以下是为您推荐的热门案例，点击案例卡片可查看完整设计方案，挑选您喜欢的方案应用同款吧"""
        elif state['user_input'] == '风格测试':
            state['type'] = RESPONSE_TYPES['ASK_STYLE']  # 询问风格
            state['content'] = """小U想确认一下您的风格偏好,您可以从以下类型中选择最多三种风格,
                    也可以直接发送文字描述,或者给我某品牌案例,小U将为您精准匹配对应案例"""
        elif state['user_input'] == "智能生成":
            state['type'] = RESPONSE_TYPES['RENDER_PARAMS']  # 发起渲染
            state['content'] = (
                """请确认以下生成参数：\n1. 空间选择\n   ▸ 默认勾选常用空间（可取消/新增）\n"""
                """   ▸ 支持多选（建议≤5个核心区域）\n2. 参数设置\n   ▸ 点击【更多设置】调整渲染参数（默认：效果图+高清）\n"""
                """3. 消耗提示\n   ▸ 每房间生成消耗U币，建议优先生成客餐厅/主卧"""
            )
        elif state['user_input'] == "AI装修问答":
            state['type'] = RESPONSE_TYPES['TEXT']  # 文本回复
            state['content'] = """您在装修或者设计过程中遇到了什么问题吗?可以告诉我,小U为您答疑解惑!"""
        elif state['user_input'] == "装修解惑":
            state['type'] = RESPONSE_TYPES['TEXT']  # 文本回复
            state['content'] = """您在装修或者设计过程中遇到了什么问题吗?可以告诉我,小U为您答疑解惑!"""
        elif state["user_input"] == "户型推荐" or state["user_input"] == "推荐户型":
            state['type'] = RESPONSE_TYPES['HOUSE_RECOMMEND']  # 户型推荐
            print("------开启户型推荐-------")
            state['content'] = "为您推荐以下户型,快来开启体验户型之旅吧!"
        # 相似户型
        elif state['user_input'] == "相似户型":
            state['tyoe'] = 29
            state['content'] = "请输入以下信息，小U帮您查找相似户型"
        elif state['user_input'] == '换一批方案' or state['user_input'] == '其他风格':
            state['switch_intelligent'] = 1
            state['type'] = RESPONSE_TYPES['CASE_LIST']  # 筛选模板反馈
            self.type_6 = 0
            state['content'] = """以下是为您切换的热门案例，点击案例卡片可查看完整设计方案，挑选您喜欢的方案应用同款吧"""
        elif state['type'] == RESPONSE_TYPES['NO_ESTATE_RESULT']:
            state['type'] = RESPONSE_TYPES['HOUSE_RECOMMEND']  # 户型推荐
            state['content'] = """为您推荐以下户型,快来开启体验设计之旅吧!"""
        elif state['type'] == 5:
            state['type'] = RESPONSE_TYPES['HOUSE_TYPE_RESULT']  # 户型搜索结果
            state['content'] = """根据您的小区以及面积查找到以下户型,请确认您家的户型,也可以手动上传哦"""
            state['define_area'] = True
        elif state['type'] in [14, 19, 20]:
            state['define_house_type'] = True
            state['define_area'] = True
            if state['styles'] or state['brand']:
                if self.type_6:
                    state['type'] = RESPONSE_TYPES['RENDER_PARAMS']  # 发起渲染
                    state['content'] = (
                        """请确认以下生成参数：\n1. 空间选择\n   ▸ 默认勾选常用空间（可取消/新增）\n"""
                        """   ▸ 支持多选（建议≤5个核心区域）\n2. 参数设置\n   ▸ 点击【更多设置】调整渲染参数（默认：效果图+高清）\n"""
                        """3. 消耗提示\n   ▸ 每房间生成消耗U币，建议优先生成客餐厅/主卧"""
                    )
                else:
                    state['type'] = RESPONSE_TYPES['CASE_LIST']  # 筛选模板反馈
                    self.type_6 = 0
                    state['content'] = await self.type_6_content(state)
            else:
                if self.type_6:
                    state['type'] = RESPONSE_TYPES['RENDER_PARAMS']  # 发起渲染
                    state['content'] = (
                        """请确认以下生成参数：\n1. 空间选择\n   ▸ 默认勾选常用空间（可取消/新增）\n"""
                        """   ▸ 支持多选（建议≤5个核心区域）\n2. 参数设置\n   ▸ 点击【更多设置】调整渲染参数（默认：效果图+高清）\n"""
                        """3. 消耗提示\n   ▸ 每房间生成消耗U币，建议优先生成客餐厅/主卧"""
                    )
                else:
                    state['type'] = RESPONSE_TYPES['ASK_STYLE']  # 询问风格
                    state['content'] = (
                        """您已成功使用户型!小U想确认一下您的风格偏好,您可以从以下类型中选择最多三种风格,\n"""
                        """                    也可以直接发送文字描述,小U将为您精准匹配对应案例"""
                    )
        elif state['type'] == 3:
            state['type'] = RESPONSE_TYPES['GENERATING']  # 生成中
        elif state['type'] == 6:
            # for style in ["现代","极简","轻奢","奶油","中式","欧式","美式","法式","侘寂","原木","复古","北欧"]:
            #     if style in state['user_input'] and style not in state['styles']:
            #         state['styles'].append(style)
            # response=await brand_chain.ainvoke({'input':state['user_input']})
            # if response.brand:
            #     state['brand']={"query":{"type":"case","keyword":response.brand,"limit":10,"offset":0},"context":{"session_id":self.session_id}}
            self.type_6 = 1
            if state['define_house_type']:
                state['type'] = RESPONSE_TYPES['RENDER_PARAMS']  # 发起渲染
                state['content'] = (
                    """请确认以下生成参数：\n1. 空间选择\n   ▸ 默认勾选常用空间（可取消/新增）\n"""
                    """   ▸ 支持多选（建议≤5个核心区域）\n2. 参数设置\n   ▸ 点击【更多设置】调整渲染参数（默认：效果图+高清）\n"""
                    """3. 消耗提示\n   ▸ 每房间生成消耗U币，建议优先生成客餐厅/主卧"""
                )
            else:
                if state['define_area']:
                    state['type'] = RESPONSE_TYPES['USER_HOUSE_TYPE']  # 用户已添加户型
                    state['content'] = """小U在您的家中找到以下户型,可以直接选择使用,您也可以输入城市小区查找使用其他户型"""
                else:
                    num_house_type = await self.search_house(state['conversation_id'])
                    if num_house_type >= 1:
                        state['type'] = RESPONSE_TYPES['USER_HOUSE_TYPE']  # 用户已添加户型
                        state['content'] = """小U在您的家中找到以下户型,可以直接选择使用,您也可以输入城市小区查找使用其他户型"""
                    else:
                        state['type'] = RESPONSE_TYPES['TEXT']  # 文本回复
                        state['content'] = """请提供以下住宅信息：\n1.所在城市（必填）\n2.小区/楼盘名称（必填）\n示例格式：北京市橡树湾 / 成都市麓湖生态城\n注：数据加密处理，仅用于调取对应户型图"""
        elif state['type'] == 32:
            for style in ["现代", "极简", "轻奢", "奶油", "中式", "欧式", "美式", "法式", "侘寂", "原木", "复古", "北欧"]:
                if style in state['user_input'] and style not in state['styles']:
                    state['styles'].append(style)
            state['type'] = RESPONSE_TYPES['CASE_LIST']  # 筛选模板反馈
            state['content'] = await self.type_6_content(state)
            self.type_6 = 0
        return state

    @log_execution_time()
    async def switch_params(self, state: GraphState):
        # 切换风格/品牌
        response = await switch_params_chain.ainvoke({'input': state['user_input']})
        print('---------切换参数响应---------\n', response)
        response_str = ''
        # 更新状态
        for param in response.switch_params:
            if param == '风格' or param == '品牌':
                if response.switch_params_dict[param]:
                    if param == '风格':
                        if response.pre_params[param] and not response.pre_params[param].strip():
                            state['type'] = RESPONSE_TYPES['TEXT']  # 文本回复
                            state['content'] = """小U暂时不支持您切换的风格,您可以尝试其他风格哦"""
                            return state
                        state['styles'] = [response.switch_params_dict[param]]
                        state['type'] = RESPONSE_TYPES['CASE_LIST']  # 筛选模板反馈
                        state['content'] = await self.type_6_content(state)
                        state['content'] = state['content'].replace(
                            response.switch_params_dict[param],
                            response.pre_params[param]
                        )
                        return state
                    elif param == '品牌':
                        if response.pre_params[param] and not response.pre_params[param].strip():
                            state['type'] = RESPONSE_TYPES['TEXT']  # 文本回复
                            state['content'] = """小U暂时不支持您切换的品牌,您可以尝试其他品牌哦"""
                            return state
                        state['brand'] = response.switch_params_dict[param]
                        state['type'] = RESPONSE_TYPES['TEXT']  # 文本回复
                        return state
                    response_str += f"好的，小U已经成功应用{response.switch_params_dict[param]}{param}哦\n"
                else:
                    response_str += f"请直接告诉我们您要切换的{param}是什么哦\n"
        state['content'] = response_str
        self.type_6 = 0
        return state

    async def see_user_house_type(self, state: GraphState):
        state['type'] = RESPONSE_TYPES['USER_HOUSE_TYPE']  # 用户已添加户型
        state['content'] = """小U在您的家中找到以下户型,可以直接选择使用,也可以输入城市小区来查找新的户型哦"""
        return state

    @log_execution_time()
    async def design(self, state: GraphState):
        state['type'] = RESPONSE_TYPES['TEXT']  # 文本回复
        if state['define_house_type']:
            if state['styles'] or state['brand']:
                state['type'] = RESPONSE_TYPES['CASE_LIST']  # 筛选模板反馈
                state['content'] = await self.type_6_content(state)
            else:
                state['type'] = RESPONSE_TYPES['ASK_STYLE']  # 询问风格
                state['content'] = """小U想确认一下您的风格偏好,您可以从以下类型中选择最多三种风格,
                    也可以直接发送文字描述,或者给我某品牌案例,小U将为您精准匹配对应案例"""
        else:
            if state['define_area']:
                state['type'] = RESPONSE_TYPES['HOUSE_TYPE_RESULT']  # 户型搜索结果
                state['content'] = """根据您的小区以及面积查找到以下户型,请确认您家的户型,也可以手动上传哦"""
            else:
                house_num = await self.search_house(state['conversation_id'])
                if house_num >= 1:
                    state['type'] = RESPONSE_TYPES['USER_HOUSE_TYPE']  # 用户已添加户型
                    state['content'] = """小U在您的家中找到以下户型,可以直接选择使用,您也可以输入城市小区查找使用其他户型"""
                else:
                    state['type'] = RESPONSE_TYPES['TEXT']  # 文本回复
                    state['content'] = """请提供以下住宅信息：\n1.所在城市（必填）\n2.小区/楼盘名称（必填）\n示例格式：北京市橡树湾 / 成都市麓湖生态城\n注：数据加密处理，仅用于调取对应户型图"""
        state['switch_intelligent'] = 0
        return state

    @log_execution_time()
    async def type_6_content(self, state: GraphState):
        s = ''
        if state['styles']:
            styles = "、".join(state['styles'])
            s += f"● 风格偏好:{styles}\n"
        if state['define_area']:
            s += f"● 城市:{state['search_city']}\n" + f"● 小区:{state['search_area']}\n"
        if state['define_house_type']:
            s += f"● 户型:{state['search_house_type']}\n"
        if state['brand']:
            s += f"● 品牌:{state['brand']['query']['keyword']}\n"
        return (
            """根据您的需求\n""" + s +
            """推荐以下案例，可进行以下操作：\n● 选择方案：点击「应用同款」启动参数化适配\n"""
            """● 刷新案例库：点击「换一批」加载新方案（保留原需求）\n● 重定义需求：告知其他需求"""
        )

    @log_execution_time()
    async def define_house_type(self, state: GraphState):
        result, result_city = [], []
        for house_type in self.house_type:
            if ((state['search_area'].strip() in house_type['state_name'].strip() or
                 house_type['state_name'].strip() in state['search_area'].strip()) and
                (state['search_city'].strip() in house_type['sname'].strip() or
                 house_type['sname'].strip() in state['search_city'].strip())):
                result_city.append(house_type['sname'])
                if house_type['show_area']:
                    if int(float(state['search_house_type'])) == int(float(house_type['show_area'])):
                        if house_type not in result:
                            result.append(house_type)
        return result, result_city

    @log_execution_time()
    async def universal_chat(self, state: GraphState):
        # 获取LLM实例和提示词模板
        llm = get_llm('qwen-flash', temperature=1.0, top_p=0.8)  # 调用qwen-flash快速回答通用问题
        # 检索app使用相关问答文档
        # app_use_faiss=FAISS.load_local('app/faiss/app_use',embeddings=EMBED,allow_dangerous_deserialization=True)
        # app_use_docs = await app_use_faiss.asimilarity_search(state['user_input'], k=1)
        app_use_docs = app_use_qa_searcher.search(state['user_input'], k=1)
        docs_content = '\n'.join([doc['answer']+'\n'+doc['question'] for doc in app_use_docs])
        chat_prompt = get_universal_chat_prompt()
        # 调用LLM生成回答
        response = await llm.ainvoke(chat_prompt.format(
            user_input=state['user_input'],
            app_use_docs=docs_content
        ))
        # 提取回答内容，去除可能的引号
        answer = response.content.strip().strip('"').strip("'")
        # 返回回答
        state['content'] = answer
        state['type'] = 1
        return state

    @log_execution_time()
    async def design_house(self, state: GraphState):
        state['type'] = 1
        state['content'] = """请提供以下住宅信息：\n1.所在城市（必填）\n2.小区/楼盘名称（必填）\n示例格式：北京市橡树湾 / 成都市麓湖生态城\n注：数据加密处理，仅用于调取对应户型图"""
        return state

    @log_execution_time()
    async def area_style_area(self,state:GraphState):
        result,result_city=await self.define_house_type(state)
        result_city=list(set(result_city))
        if len(result)==1:
            state['define_house_type']=True
            state['search_city']=result[0]['sname']
            state['search_area']=result[0]['state_name']
            state['define_area']=True
            state['content']=await self.type_6_content(state)
            if state['styles'] or state['brand']:
                state['type']=RESPONSE_TYPES['CASE_LIST'] # 筛选模板反馈
            else:
                state['content']="""抱歉,由于您提供的风格偏好小U无法为您精准匹配,您需要从以下风格偏好中选择您的风格"""
                state['type']=RESPONSE_TYPES['ASK_STYLE'] # 询问风格
        elif len(result)>1:
            state['content']="""由于小U在您的户型库中找到多个类似的小区对应的户型或者同一个小区对应的多个户型面积,请从以下户型中选择您的小区以及户型"""
            state['type']=RESPONSE_TYPES['USER_HOUSE_TYPE'] # 用户已添加户型
        else:
            if len(result_city)==1:
                state['define_area']=True
                state['type']=RESPONSE_TYPES['HOUSE_TYPE_RESULT'] # 户型搜索结果
                state['search_city']=result_city[0]['sname']
                state['search_area']=result_city[0]['state_name']
                state['content']="""由于您的小区的户型小U暂时不支持,小U根据您的小区为您推荐以下户型"""
            elif len(result_city)>1:
                search_result=await self.search_estate(state['search_city'],state['search_area'])
                state['type']=RESPONSE_TYPES['ESTATE_RESULT_FEEDBACK'] # 小区结果反馈
                state['content']="""根据您的小区名称查找到以下结果,请进一步确认您的小区名称。"""
                state['search_result']=search_result['data']
            else:
                search_result=await self.search_estate(state['search_city'],state['search_area'])
                if len(search_result)>0:
                    state['type']=RESPONSE_TYPES['ESTATE_RESULT_FEEDBACK'] # 小区结果反馈
                    state['content']="""根据您的小区名称查找到以下结果,请进一步确认您的小区名称。"""
                    state['search_result']=search_result['data']
                else:
                    state['type']=RESPONSE_TYPES['NO_ESTATE_RESULT'] # 未搜索到小区
                    state['content']="""抱歉，未搜到您的小区，您可以先进行以下操作:\n1.推荐户型\n●系统将基于空间特征推荐各个面积区域的户型，推荐常用户型\n\n2.户型识别\n●通过AI对户型图进行识别,自行创建户型两步即达,1分钟即可体验专属户型"""
        return state

    @log_execution_time()
    async def area_house_type(self,state:GraphState):
        result,result_city=await self.define_house_type(state)
        result_city=list(set(result_city))
        if len(result)==1:
            state['define_house_type']=True
            state['search_city']=result[0]['sname']
            state['search_area']=result[0]['state_name']
            state['define_area']=True
            state['content']=await self.type_6_content(state)
            if state['styles'] or state['brand']:
                state['type']=RESPONSE_TYPES['CASE_LIST'] # 筛选模板反馈
            else:
                state['content']="""小U想确认一下您的风格偏好,您可以从以下类型中选择最多三种风格,
                    也可以直接发送文字描述,或者给我某品牌案例,小U将为您精准匹配对应案例"""
                state['type']=RESPONSE_TYPES['ASK_STYLE'] # 询问风格
        elif len(result)>1:
            state['content']="""由于小U在您的户型库中找到多个类似的小区对应的户型或者同一个小区对应的多个户型面积,请从以下户型中选择您的小区以及户型"""
            state['type']=RESPONSE_TYPES['USER_HOUSE_TYPE'] # 用户已添加户型
        else:
            if len(result_city)==1:
                state['define_area']=True
                state['type']=RESPONSE_TYPES['HOUSE_TYPE_RESULT'] # 户型搜索结果
                state['search_city']=result_city[0]['sname']
                state['search_area']=result_city[0]['state_name']
                state['content']="""由于您的小区的户型小U暂时不支持,小U根据您的小区为您推荐以下户型"""
            elif len(result_city)>1:
                search_result=await self.search_estate(state['search_city'],state['search_area'])
                state['type']=RESPONSE_TYPES['ESTATE_RESULT_FEEDBACK'] # 小区结果反馈
                state['content']="""根据您的小区名称查找到以下结果,请进一步确认您的小区名称。"""
                state['search_result']=search_result['data']
            else:
                try:
                    search_result=await self.search_estate(state['search_city'],state['search_area'])
                except Exception as e:
                    search_result=[]
                if len(search_result)>0:
                    state['type']=RESPONSE_TYPES['ESTATE_RESULT_FEEDBACK'] # 小区结果反馈
                    state['content']="""根据您的小区名称查找到以下结果,请进一步确认您的小区名称。"""
                    state['search_result']=search_result['data']
                else:
                    state['type']=36
                    state['content']="""抱歉，未搜到您的小区，您可以先进行以下操作:\n1.相似户型\n●输入户型面积和户型结构，AI智能匹配库中相似户型，应用样板间效果\n\n2.户型识别\n●通过AI对户型图进行识别,自行创建户型两步即达,1分钟即可体验专属户型"""
        return state


    @log_execution_time()
    async def run(self,state:GraphState):
        await self.initialize()
        print("开始初始化")
        # try:
            # state=await self.agent.ainvoke(state)
        # except Exception as e:
        #     logger.error(e)
        #     state['type']=1
        #     state['content']=f"小U出错了,请稍后再试......\n报错内容：{e}"
        state = await self.agent.ainvoke(state)

        state['role']='assistant'
        state['finish_time']=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        await set_redis_value(f"type_6:{self.session_id}",self.type_6)
        return state
    
class DesignAssistant:
    """
    设计助手类，管理设计房屋的对话流程
    """
    def __init__(self, data:dict):  
        self.data=data
        self.agent=Agent_design(session_id=data['conversation_id'])
        self.state=None
        self.history=None
    async def initialize(self):
        # 初始化
        if await key_exists(f"task_history1:{self.data['conversation_id']}"):
            self.history=json.loads(await get_redis_value(f"task_history1:{self.data['conversation_id']}"))
        else:
            self.history=[]
            await set_redis_value(f"task_history1:{self.data['conversation_id']}",json.dumps(self.history,ensure_ascii=False))
        self.history.append(self.data)
        if await key_exists(f"state:{self.data['conversation_id']}"):
            self.state=json.loads(await get_redis_value(f"state:{self.data['conversation_id']}"))
            self.state['user_input']=self.data['user_input']
            self.state['type']=self.data['type']
        else:
            self.state=GraphState(**self.data)
            await set_redis_value(f"state:{self.data['conversation_id']}",json.dumps(self.state,ensure_ascii=False))
        if self.data['type']==5:
            self.state['search_city']=self.data['search_city']
            self.state['search_area']=self.data['search_area']
            self.state['define_area']=True
        elif self.data['type'] in [14,19,20]:
            self.state['search_city']=self.data['search_city']
            self.state['search_area']=self.data['search_area']
            self.state['define_area']=True
            self.state['search_house_type']=self.data['search_house_type']
            self.state['define_house_type']=True
        elif self.data['type']==32:
            self.state['styles']=self.data['styles']

    @log_execution_time()
    async def process_input(self)->dict:
        # 初始化对话状态
        await self.initialize()
        result:dict=await self.agent.run(state=self.state)
        logger.info("---result---\n %s", result)
        self.history.append(result)
        await set_redis_value(f"state:{self.data['conversation_id']}",json.dumps(result,ensure_ascii=False))
        await set_redis_value(f"task_history1:{self.data['conversation_id']}",json.dumps(self.history,ensure_ascii=False))
        return result