"""QA向量数据库构建器"""

from langchain_community.vectorstores.faiss import FAISS
import os
from typing import List, Tuple, Optional, Dict
import pandas as pd
from app.faiss.qa_embeddings import create_embeddings, DEFAULT_MODEL, DEFAULT_DIMENSION

cur_dir = os.path.dirname(os.path.abspath(__file__))


class QAVectorStoreBuilder:
    """构建QA向量存储器"""
    
    def __init__(
        self,
        embedding_model: str = DEFAULT_MODEL,
        embedding_dimension: int = DEFAULT_DIMENSION,
        faiss_path: Optional[str] = None
    ):
        self.faiss_path = faiss_path or os.path.join(cur_dir, 'QA_test')
        self.embeddings = create_embeddings(model=embedding_model, dimensions=embedding_dimension)
    
    def build_from_qa_pairs(self, qa_pairs: List[Tuple[str, str]], metadata: Optional[List[Dict]] = None):
        """从问答对构建向量数据库，只对问题进行向量化"""
        print(f'开始构建向量数据库，共 {len(qa_pairs)} 条问答对...')
        
        # 准备文本和元数据
        texts, metadatas = [], []
        for i, (question, answer) in enumerate(qa_pairs):
            texts.append(question)
            metadatas.append({
                "answer": answer,
                "question": question,
                "question_id": i,
                "source": "qa_test"
            })
        
        # 创建并保存FAISS向量数据库
        faiss = FAISS.from_texts(texts=texts, embedding=self.embeddings, metadatas=metadatas)
        faiss.save_local(self.faiss_path)
        print(f'向量数据库创建完成，保存路径: {self.faiss_path}')


# 读取问答对数据
df = pd.read_csv(f'{cur_dir}/app_use/app_use.csv')
qa_pairs = df[['question','answer']].values.tolist()

qa_vector_store_builder = QAVectorStoreBuilder(
    embedding_model="text-embedding-v3",
    embedding_dimension=DEFAULT_DIMENSION,
    faiss_path='app/faiss/QA_test'
)
qa_vector_store_builder.build_from_qa_pairs(qa_pairs)