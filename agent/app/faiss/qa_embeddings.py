"""QA向量数据库公共模块 - 基于OpenAI客户端的嵌入类实现"""

import os
from openai import OpenAI
from langchain_core.embeddings import Embeddings
from typing import List

# 配置常量
DEFAULT_API_KEY = os.getenv("DASHSCOPE_API_KEY", 'sk-a708960cdb7b4bdbbb13ca0db0296b84')
DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL = "text-embedding-v3"
DEFAULT_DIMENSION = 128
BATCH_SIZE = 10  # DashScope API限制每批最多10个


class OpenAIEmbeddings(Embeddings):
    """基于OpenAI客户端的嵌入类，支持指定维度（完全使用OpenAI SDK，不依赖LangChain的DashScopeEmbeddings）"""
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None, dimensions: int = None):
        self.client = OpenAI(
            api_key=api_key or DEFAULT_API_KEY,
            base_url=base_url or DEFAULT_BASE_URL
        )
        self.model = model or DEFAULT_MODEL
        self.dimensions = dimensions or DEFAULT_DIMENSION
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """为文档列表生成嵌入向量，分批处理"""
        all_embeddings = []
        for i in range(0, len(texts), BATCH_SIZE):
            resp = self.client.embeddings.create(
                model=self.model,
                input=texts[i:i + BATCH_SIZE],
                dimensions=self.dimensions
            )
            all_embeddings.extend([item.embedding for item in resp.data])
        return all_embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """为查询文本生成嵌入向量"""
        resp = self.client.embeddings.create(
            model=self.model,
            input=[text],
            dimensions=self.dimensions
        )
        return resp.data[0].embedding


def create_embeddings(
    api_key: str = None,
    base_url: str = None,
    model: str = None,
    dimensions: int = None
) -> OpenAIEmbeddings:
    """创建嵌入模型实例的便捷函数"""
    return OpenAIEmbeddings(api_key=api_key, base_url=base_url, model=model, dimensions=dimensions)

