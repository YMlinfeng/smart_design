# 智能家装Agent系统

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Latest-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📖 项目简介

凡华科技智能家装Agent系统是一个基于LangGraph和FastAPI构建的多模块智能家装平台，包含toC端、toB端和VR眼镜等多个业务模块。通过AI Agent技术为用户提供家装设计咨询、户型推荐、风格匹配、商品展示等服务。系统采用异步消息队列架构，支持高并发处理用户请求。

### ✨ 核心特性

- 🤖 **智能对话**: 基于LangGraph的多轮对话管理
- 🏠 **户型推荐**: 智能匹配小区、户型、风格
- 📚 **知识问答**: RAG技术驱动的装修知识问答
- 🛍️ **商品展示**: toB端商品推荐和客户服务
- 🥽 **VR体验**: VR眼镜模块提供沉浸式家装体验
- ⚡ **高并发**: 异步消息队列架构，支持大规模并发
- 🔄 **状态管理**: Redis持久化对话状态和历史
- 🎨 **多风格支持**: 现代、极简、轻奢、奶油等12种装修风格
- 🏢 **多端支持**: toC端、toB端、VR端多业务场景覆盖

## 🏗️ 技术架构

### 核心技术栈

- **Web框架**: FastAPI + Uvicorn
- **AI框架**: LangGraph + LangChain Core + LangChain Community + OpenAI API
- **消息队列**: RabbitMQ (aio_pika)
- **缓存**: Redis (异步支持)
- **向量数据库**: FAISS (通过 langchain-community)
- **部署**: Docker + Gunicorn
- **可选依赖**: 火山引擎ARK Runtime SDK (用于AI图片生成)

### 系统架构

```
用户请求 → FastAPI → RabbitMQ → Agent处理 → Redis缓存 → 回调API
    ↓           ↓         ↓         ↓         ↓
   HTTP     消息队列   异步处理   状态管理   结果返回
```

## 📁 项目结构

```
凡华科技/
├── agent/                    # toC端智能体
│   ├── app/
│   │   ├── main.py          # FastAPI应用入口
│   │   ├── config.py        # 系统配置
│   │   ├── mq.py            # 消息队列处理
│   │   ├── utils/            # toC端工具模块
│   │   │   ├── agent.py     # 核心Agent逻辑
│   │   │   ├── api_manager.py # API管理器
│   │   │   ├── constants.py  # 常量定义
│   │   │   ├── llm_manager.py # LLM管理器
│   │   │   ├── models.py     # 数据模型
│   │   │   ├── prompt.py     # 提示词模板
│   │   │   ├── rag_manager.py # RAG管理器
│   │   │   └── redis_manager.py # Redis管理器
│   │   ├── utils_toB/        # toB端工具模块（共享代码）
│   │   │   ├── agent_toB.py  # toB端Agent逻辑
│   │   │   ├── api_manager.py # API管理器
│   │   │   ├── constants.py  # 常量定义
│   │   │   ├── decorators.py # 装饰器（性能监控）
│   │   │   ├── llm_manager.py # LLM管理器
│   │   │   ├── models.py      # 数据模型
│   │   │   ├── prompt.py      # 提示词模板
│   │   │   ├── rag_manager.py # RAG管理器
│   │   │   ├── redis_manager.py # Redis管理器（增强版）
│   │   │   └── get_ai_generation_route.py # AI图片生成路由
│   │   ├── views/
│   │   │   └── view.py      # API路由定义
│   │   ├── faiss/           # 向量数据库
│   │   │   ├── knowledge/   # 装修知识库
│   │   │   └── app_use/     # App使用问答库
│   │   ├── test_chat.py     # 聊天测试
│   │   ├── test_reids.py    # Redis测试
│   │   └── test.ipynb       # Jupyter测试
│   ├── Dockerfile
│   ├── requirement.txt
│   ├── test_toC.py          # toC端测试
│   └── house.csv            # 房屋数据
├── agent-toB/               # toB端智能体
│   ├── app/
│   │   ├── main.py          # FastAPI应用入口
│   │   ├── config.py        # 系统配置
│   │   ├── mq.py            # 消息队列处理
│   │   ├── utils/            # 工具模块
│   │   │   ├── agent_toB.py # toB端Agent逻辑
│   │   │   ├── api_manager.py # API管理器
│   │   │   ├── constants.py  # 常量定义
│   │   │   ├── decorators.py # 装饰器
│   │   │   ├── llm_manager.py # LLM管理器
│   │   │   ├── models.py     # 数据模型
│   │   │   ├── prompt.py     # 提示词模板
│   │   │   ├── rag_manager.py # RAG管理器
│   │   │   └── redis_manager.py # Redis管理器
│   │   ├── views/
│   │   │   └── view.py      # API路由定义
│   │   ├── faiss/           # 向量数据库
│   │   │   ├── knowledge/   # 装修知识库
│   │   │   └── app_use/     # App使用问答库
│   │   └── requirement.txt
│   ├── Dockerfile
│   ├── README.md
│   ├── requirement.txt
│   ├── test_reids.py        # Redis测试
│   ├── test_toB.py          # toB端测试
│   ├── test_展示商品到客户家.py # 商品展示测试
│   ├── test_热门商品.py      # 热门商品测试
│   └── test_热门案例.py      # 热门案例测试
├── vr_glasses/              # VR眼镜模块
│   ├── app/
│   │   ├── main.py          # FastAPI应用入口
│   │   ├── config.py        # 系统配置
│   │   ├── agent.py         # VR Agent逻辑
│   │   ├── exceptions.py    # 异常处理
│   │   ├── logging_config.py # 日志配置
│   │   ├── models.py        # 数据模型
│   │   └── views.py         # API路由定义
│   ├── env.example          # 环境变量示例
│   ├── readme.md            # VR模块说明
│   ├── requirements.txt     # 依赖文件
│   ├── run.py               # 运行脚本
│   └── test_agent.py        # Agent测试
├── tmp/                     # 临时文件
│   ├── agent.py             # 原始Agent代码
│   ├── agnet_toB_ori.py     # 原始toB Agent代码
│   ├── readme.md            # 临时说明
│   ├── requirement.txt      # 临时依赖
│   └── 技术文档.md           # 技术文档
├── B端智能体传输json定义.docx # B端API定义文档
└── 智能家装Agent技术文档.docx # 技术文档
```

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Redis 6.0+
- RabbitMQ 3.8+

### 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd 凡华科技

# 安装各模块依赖
pip install -r agent/requirement.txt
pip install -r agent-toB/requirement.txt
pip install -r vr_glasses/requirements.txt

# 重要：LangChain相关依赖
# 新版本LangChain已拆分为多个包，确保安装以下核心包：
pip install langchain-core langchain-community langchain-openai

# 可选：AI图片生成功能（火山引擎SDK）
# 注意：此包可能不在标准PyPI源中，请根据火山引擎官方文档安装
# pip install volcenginesdkarkruntime
```

### 配置环境

1. 在config.py中配置必要的环境变量：
```bash
# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your_password

# AI服务配置
DASHSCOPE_API_KEY=your_dashscope_key
LLM_BASE_URL=your_llm_base_url

# 外部API配置
SEARCH_ESTATE_URL=your_estate_search_url
SEARCH_HOUSE_URL=your_house_search_url
FIND_HOUSE_TYPE_URL=your_house_type_url
AUTH_TOKEN=your_auth_token
```

### 启动服务

#### 开发环境

```bash
# 启动Redis和RabbitMQ服务
redis-server
rabbitmq-server

# 启动toC端应用
cd agent
uvicorn app.main:app --host 0.0.0.0 --port 7754 --reload

# 启动toB端应用（新终端）
cd agent-toB
uvicorn app.main:app --host 0.0.0.0 --port 7755 --reload

# 启动VR眼镜模块（新终端）
cd vr_glasses
python run.py
```

#### 生产环境

```bash
# toC端使用Gunicorn
cd agent
gunicorn -w 10 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:7754 --timeout 120 app.main:app

# toB端使用Gunicorn
cd agent-toB
gunicorn -w 10 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:7755 --timeout 120 app.main:app

# VR眼镜模块
cd vr_glasses
python run.py
```

#### Docker部署

```bash
# 构建各模块镜像
docker build -t agent-toc ./agent
docker build -t agent-tob ./agent-toB
docker build -t vr-glasses ./vr_glasses

# 运行容器
docker run -p 7754:7754 --env-file .env agent-toc
docker run -p 7755:7755 --env-file .env agent-tob
docker run -p 7756:7756 --env-file .env vr-glasses
```

## 📖 使用指南

### API接口

#### toC端智能体 (端口: 7754)

```http
POST /process
Content-Type: application/json

{
  "user_input": "我想装修一套现代风格的房子",
  "conversation_id": 12345,
  "type": 1
}
```

#### toB端智能体 (端口: 7755)

```http
POST /process
Content-Type: application/json

{
  "user_input": "展示热门商品到客户家",
  "conversation_id": 12345,
  "type": 1
}
```

#### VR眼镜模块 (端口: 7756)

```http
POST /vr/process
Content-Type: application/json

{
  "user_input": "VR家装体验",
  "conversation_id": 12345
}
```


### 对话类型

#### toC端对话类型
- **定位户型类**: 查询特定城市的小区信息
- **风格类**: 装修风格咨询和推荐
- **知识类**: 装修知识问答
- **通用对话**: 通用llm对话
- **案例类**: 装修案例推荐
- **切换类**: 方案和风格切换

#### toB端对话类型
- **商品展示类**: 展示商品到客户家
- **热门商品类**: 推荐热门商品
- **热门案例类**: 推荐热门装修案例
- **客户服务类**: B端客户服务对话

#### VR端对话类型
- **VR体验类**: VR家装体验相关对话
- **沉浸式交互**: VR环境下的交互对话

### 支持的装修风格

- 现代、极简、轻奢、奶油
- 中式、欧式、美式、法式
- 侘寂、原木、复古、北欧

## 🔧 核心功能

### 1. 智能路由系统

基于LangGraph构建的状态图，支持复杂的多分支对话流程：

```python
# 路由节点示例
def router_run(state: GraphState):
    # 分析用户输入，确定对话类型
    conversation_type = analyze_user_input(state.user_input)
    return {"conversation_type": conversation_type}
```

### 2. RAG知识问答

- 使用DashScope Embeddings进行文本向量化
- FAISS向量数据库存储和检索
- 支持相似度搜索（默认返回3个相关文档）

### 3. 状态管理

Redis存储结构：
- `task_history1:{session_id}`: 对话历史（JSON格式，自动类型检查）
- `state:{session_id}`: 当前状态（JSON格式，自动类型修复）
- `type_6:{session_id}`: 类型6状态标记

**增强功能**：
- 自动类型检查和修复（防止类型错误）
- 异常处理和日志记录
- 列表字段自动验证（finish_type_list, styles, search_result）

### 4. 外部API集成

- **小区搜索**: 根据城市和关键词搜索小区
- **户型查询**: 获取用户会话相关的户型信息
- **户型详情**: 查询具体户型的详细信息

### 5. AI图片生成（可选功能）

- **火山引擎ARK**: 调用火山平台API生成优化后的图片
- **可选依赖**: 如果未安装 `volcenginesdkarkruntime`，功能将自动禁用
- **路由**: `/ai_generate` (POST)

## 📊 监控与日志

### 关键指标

- 任务处理时间
- 队列积压情况
- API调用成功率
- Token消耗统计

### 日志记录

- 请求处理日志
- 错误异常日志
- 性能指标日志

## 🛠️ 开发指南

### 添加新的对话类型

1. 在`agent.py`中添加新的节点函数
2. 在路由逻辑中注册新的条件边
3. 更新对话类型枚举

### 扩展知识库

#### toC端知识库
1. 准备知识文档
2. 运行向量化脚本：
```bash
cd agent
python app/faiss/knowledge/build_knowledge_faiss.py
```

#### toB端知识库
1. 准备知识文档
2. 运行向量化脚本：
```bash
cd agent-toB
python app/faiss/knowledge/build_knowledge_faiss.py
python app/faiss/app_use/build_app_use_faiss.py
```

**注意**：toB端代码位于 `agent/app/utils_toB/` 目录，与toC端共享部分代码结构。

### 测试

#### toC端测试
```bash
cd agent
# 聊天功能测试
python app/test_chat.py

# Redis连接测试
python app/test_reids.py

# toC端完整测试
python test_toC.py
```

#### toB端测试
```bash
cd agent-toB
# Redis连接测试
python test_reids.py

# toB端完整测试
python test_toB.py

# 商品展示测试
python test_展示商品到客户家.py

# 热门商品测试
python test_热门商品.py

# 热门案例测试
python test_热门案例.py
```

#### VR眼镜模块测试
```bash
cd vr_glasses
# Agent功能测试
python test_agent.py
```

## 🐛 故障排查

### 常见问题

1. **Redis连接失败**
   - 检查网络连接和认证信息
   - 确认Redis服务正常运行
   - 检查Redis数据格式是否正确（系统会自动修复类型错误）

2. **RabbitMQ连接超时**
   - 检查队列配置和网络连接
   - 确认RabbitMQ服务状态

3. **Agent处理异常**
   - 查看详细日志信息
   - 检查状态信息
   - 查看是否有类型错误（如 'str' object has no attribute 'append'）

4. **API调用失败**
   - 检查外部服务可用性
   - 验证API密钥和权限

5. **导入错误（ModuleNotFoundError）**
   
   **LangChain相关导入错误**：
   ```bash
   # 确保安装正确的LangChain包
   pip install langchain-core langchain-community langchain-openai
   ```
   
   **常见错误及解决方案**：
   - `No module named 'langchain.vectorstores'` 
     → 使用 `from langchain_community.vectorstores.faiss import FAISS`
   - `No module named 'langchain.prompts'`
     → 使用 `from langchain_core.prompts import PromptTemplate`
   - `No module named 'langchain.output_parsers'`
     → 使用 `from langchain_core.output_parsers import PydanticOutputParser`
   
   **火山引擎SDK导入错误**：
   - `No module named 'volcenginesdkarkruntime'`
     → 这是可选依赖，不影响系统启动
     → 如需使用AI图片生成功能，请根据火山引擎官方文档安装

6. **类型错误（TypeError）**
   - `'str' object has no attribute 'append'`
     → 系统已自动修复，检查Redis数据格式
     → 查看日志中的类型警告信息
   - `finish_type_list` 类型错误
     → 系统会自动修复为列表类型
     → 检查Redis中存储的数据格式

7. **Redis数据类型错误**
   - 系统已实现多层防护机制
   - 自动类型检查和修复
   - 查看日志了解具体修复情况


## 🔄 版本更新日志

### 最新更新

- ✅ **修复LangChain导入问题**: 更新为新版本LangChain的导入路径
  - `langchain.vectorstores` → `langchain_community.vectorstores`
  - `langchain.prompts` → `langchain_core.prompts`
  - `langchain.output_parsers` → `langchain_core.output_parsers`

- ✅ **增强Redis类型安全**: 添加多层类型检查和自动修复机制
  - 自动检测和修复历史记录类型错误
  - 自动检测和修复状态字段类型错误
  - 详细的错误日志和警告信息

- ✅ **可选依赖支持**: AI图片生成功能支持可选依赖
  - `volcenginesdkarkruntime` 为可选依赖
  - 未安装时系统仍可正常启动
  - 使用功能时会给出明确的错误提示

- ✅ **代码结构优化**: toB端代码重构
  - 独立的 `utils_toB` 模块
  - 增强的装饰器支持（性能监控）
  - 改进的错误处理机制

## 📞 联系我们

- 项目维护者: [凡华科技]
