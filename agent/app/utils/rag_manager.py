# ==================== RAG知识库管理 ====================
"""
智能家装Agent 装修知识RAG知识库管理模块

负责管理RAG（检索增强生成）相关的功能，包括：
- 向量数据库初始化
- 文档检索
- 知识问答处理
"""

from langchain_community.vectorstores.faiss import FAISS
from langchain_community.embeddings.dashscope import DashScopeEmbeddings
from app.utils.llm_manager import rag_chain
from app.utils.constants import EMBED
from app.mq import knowledge_faiss
# ==================== 向量数据库初始化 ====================
class RAGManager:
    """
    RAG知识库管理器
    
    负责管理向量数据库的初始化和文档检索功能
    """
    
    def __init__(self):
        """初始化RAG管理器"""
        self.embed = None
        self.faiss = None
        self._initialize_embeddings()
        self._load_vector_store()
    
    def _initialize_embeddings(self):
        """初始化嵌入模型"""
        self.embed = EMBED
    
    def _load_vector_store(self):
        """加载本地FAISS向量数据库"""
        self.faiss = knowledge_faiss
    async def search_documents(self, query: str, k: int = 1):
        """
        从本地知识库中获取信息答案
        
        Args:
            query (str): 用户的输入问题
            k (int): 从知识库中获取的相关文档数量
            
        Returns:
            list[str]: 知识库中相关文档的内容
        """
        docs = await self.faiss.asimilarity_search(query, k=k)
        return [doc.metadata['答案'] for doc in docs]
    
    async def generate_answer(self, query: str, docs: list[str]):
        """
        基于检索到的文档生成回答
        
        Args:
            query (str): 用户问题
            docs (list[str]): 检索到的文档列表
            
        Returns:
            str: 生成的回答
        """
        # 确保有足够的文档
        while len(docs) < 3:
            docs.append("")
        
        # 使用RAG链生成回答
        response = await rag_chain.ainvoke({
            'doc1': docs[0], 
            'doc2': docs[1], 
            'doc3': docs[2], 
            'question': query
        })
        return response


# ==================== 全局RAG管理器实例 ====================
# 创建全局RAG管理器实例
rag_manager = RAGManager()


# ==================== 便捷函数 ====================
async def rag_search(query: str, k: int = 1):
    """
    便捷的RAG搜索函数
    
    Args:
        query (str): 搜索查询
        k (int): 返回文档数量
        
    Returns:
        list[str]: 检索到的文档
    """
    return await rag_manager.search_documents(query, k)


async def rag_answer(query: str, docs: list[str] = None):
    """
    便捷的RAG问答函数
    
    Args:
        query (str): 用户问题
        docs (list[str], optional): 预检索的文档，如果为None则自动检索
        
    Returns:
        str: 生成的回答
    """
    if docs is None:
        docs = await rag_search(query)
    
    return await rag_manager.generate_answer(query, docs)
