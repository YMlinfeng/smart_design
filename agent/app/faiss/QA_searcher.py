"""QA向量数据库检索器"""

from langchain_community.vectorstores.faiss import FAISS
from typing import List, Dict
from app.faiss.qa_embeddings import create_embeddings, DEFAULT_MODEL, DEFAULT_DIMENSION
import os
import time
import torch

class QASearcher:
    """QA向量数据库检索器（带缓存优化）"""
    
    def __init__(
        self,
        embedding_model: str = DEFAULT_MODEL,
        embedding_dimension: int = DEFAULT_DIMENSION,
        faiss_path: str = 'app/faiss/QA_test',
        cache_size: int = 100
    ):
        self.faiss_path = faiss_path
        self.embeddings = create_embeddings(model=embedding_model, dimensions=embedding_dimension)
        self.faiss = self._load_vector_store()
        self._search_cache = {}
        self._cache_size = cache_size
    
    def _load_vector_store(self) -> FAISS:
        """加载FAISS向量数据库"""
        # 处理相对路径，转换为绝对路径
        if not os.path.isabs(self.faiss_path):
            # 获取app目录（当前文件所在目录的父目录）
            cur_dir = os.path.dirname(os.path.abspath(__file__))
            app_dir = os.path.dirname(cur_dir)  # agent/app
            
            # 尝试多个可能的路径
            possible_paths = [
                os.path.join(cur_dir, self.faiss_path.replace('app/faiss/', '')),  # app/faiss/QA_test
                os.path.join(app_dir, self.faiss_path),  # app/faiss/QA_test（从app目录）
                self.faiss_path  # 原始路径
            ]
            
            faiss_path = None
            for path in possible_paths:
                index_file = os.path.join(path, 'index.faiss')
                pkl_file = os.path.join(path, 'index.pkl')
                if os.path.exists(index_file) and os.path.exists(pkl_file):
                    faiss_path = path
                    break
            
            if faiss_path is None:
                # 如果没找到，使用第一个路径并检查
                faiss_path = possible_paths[0]
        else:
            faiss_path = self.faiss_path
        
        # 检查必要文件是否存在
        index_file = os.path.join(faiss_path, 'index.faiss')
        pkl_file = os.path.join(faiss_path, 'index.pkl')
        
        if not os.path.exists(index_file):
            raise FileNotFoundError(
                f'FAISS索引文件不存在: {index_file}\n'
                f'请确保向量数据库已正确构建。\n'
                f'尝试的路径: {faiss_path}'
            )
        if not os.path.exists(pkl_file):
            raise FileNotFoundError(
                f'FAISS元数据文件不存在: {pkl_file}\n'
                f'向量数据库文件不完整，请重新构建。\n'
                f'尝试的路径: {faiss_path}'
            )
        
        print(f'正在加载向量数据库: {faiss_path}')
        print(f'使用模型: {self.embeddings.model}, 维度: {self.embeddings.dimensions}')
        
        try:
            faiss = FAISS.load_local(
                faiss_path,
                embeddings=self.embeddings,
                allow_dangerous_deserialization=True
            )
            print('向量数据库加载成功！')
            
            # 验证维度匹配
            if hasattr(faiss, 'index') and hasattr(faiss.index, 'd'):
                index_dimension = faiss.index.d
                if index_dimension != self.embeddings.dimensions:
                    raise ValueError(
                        f'维度不匹配！向量数据库维度: {index_dimension}, '
                        f'当前嵌入模型维度: {self.embeddings.dimensions}。\n'
                        f'请使用相同的维度重新构建向量数据库或设置 embedding_dimension={index_dimension}。'
                    )
            
            return faiss
        except FileNotFoundError:
            raise
        except ValueError:
            raise
        except Exception as e:
            raise RuntimeError(f'加载向量数据库失败: {e}')
    
    def search(self, query: str, k: int = 5) -> List[Dict]:
        """
        检索相似问题（带缓存优化）
        
        Args:
            query: 查询问题
            k: 返回最相似的k个结果
        
        Returns:
            检索结果列表，每个结果包含问题、答案和距离分数
            注意：score 是距离值，越小表示越相似（FAISS使用L2距离）
        """
        
        # 执行搜索（FAISS返回的是距离，不是相似度）
        docs = self.faiss.similarity_search_with_score(query, k=k)
        results = [
            {
                'question': doc.metadata.get('question', doc.page_content),
                'answer': doc.metadata.get('answer', ''),
                'distance': float(score),  # 距离值，越小越相似
                'question_id': doc.metadata.get('question_id', -1),
                'source': doc.metadata.get('source', '')
            }
            for doc, score in docs
        ]
        
        return results
    
    def print_search_results(self, query: str, k: int = 5, show_similarity: bool = False):
        """
        格式化打印检索结果
        
        Args:
            query: 查询问题
            k: 返回最相似的k个结果
            show_similarity: 是否显示相似度（True）或距离（False）
        """
        print(f'\n{"="*60}\n查询问题: {query}\n{"="*60}\n')
        
        results = self.search(query, k=k)
        if not results:
            print('未找到相关结果')
            return
        
        for i, r in enumerate(results, 1):
            distance = r["distance"]
            if show_similarity:
                # 将距离转换为相似度（使用简单的倒数转换，距离越小相似度越大）
                max_distance = max(r["distance"] for r in results) if results else 1.0
                similarity = 1.0 / (1.0 + distance)  # 归一化到0-1之间
                print(f'【结果 {i}】相似度: {similarity:.4f} (越大越相似) | 距离: {distance:.4f} | ID: {r["question_id"]}')
            else:
                print(f'【结果 {i}】距离: {distance:.4f} (越小越相似) | ID: {r["question_id"]}')
            print(f'问题: {r["question"]}')
            print(f'答案: {r["answer"]}\n{"-"*60}')


def main():
    """主函数：测试检索功能"""
    # 初始化检索器
    start_time = time.time()
    searcher = QASearcher(faiss_path='app/faiss/QA_test')
    end_time = time.time()
    print(f"初始化检索器用时: {end_time - start_time} 秒")
    # 测试查询
    test_queries = [
        "可以识别CAD吗",
        "可以用拼音检索吗",
        "能看户型朝南的优先吗",
        "户型库有二手房的图吗",
        "我选的户型能不能直接渲染",
        "为什么搜索到的户型缺少尺寸标注"
    ]
    
    print("\n" + "="*60)
    print("开始检索测试")
    print("="*60)
    start_time = time.time()
    for query in test_queries:
        searcher.print_search_results(query, k=3)
    end_time = time.time()
    print(f"检索测试用时: {end_time - start_time} 秒,平均每次检索用时: {(end_time - start_time) / len(test_queries)} 秒")
    # 交互式查询
    print("\n" + "="*60)
    print("进入交互式查询模式（输入 'quit'/'exit'/'q' 退出）")
    print("="*60)
    
    while True:
        try:
            query = input("\n请输入查询问题: ").strip()
            if not query:
                continue
            if query.lower() in ('quit', 'exit', 'q'):
                print("退出查询")
                break
            searcher.print_search_results(query, k=5)
        except KeyboardInterrupt:
            print("\n\n退出查询")
            break
        except Exception as e:
            print(f"查询出错: {e}")


# if __name__ == '__main__':
#     main()

