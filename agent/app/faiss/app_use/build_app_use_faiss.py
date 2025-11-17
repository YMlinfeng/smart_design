# 由于未知原因，该代码只能在faiss/app_use目录下运行

# 创建关于app使用的faiss向量数据库

import os
from langchain_community.vectorstores.faiss import FAISS
from langchain_community.embeddings.dashscope import DashScopeEmbeddings


# 获取脚本所在目录的绝对路径
script_dir = os.path.dirname(os.path.abspath(__file__))
# 构建app_use.txt的完整路径
txt_file_path = os.path.join(script_dir, 'app_use.txt')

# 读取app_use.txt文件的问答对
with open(txt_file_path, 'r', encoding='utf-8') as f:
    text_all = f.read()

# 解析为问答对列表
text_list = [line.strip() for line in text_all.split('\n') if line.strip()]
qa_pairs: list[str] = []
for i in range(0, len(text_list) - 1, 2):
    qa_pairs.append(text_list[i] + '\n' + text_list[i + 1])

# 创建faiss向量数据库
embeddings = DashScopeEmbeddings(
    dashscope_api_key='sk-a708960cdb7b4bdbbb13ca0db0296b84',  # DashScope API密钥
    model="text-embedding-v3"  # 嵌入模型版本
)
print(qa_pairs)
faiss = FAISS.from_texts(qa_pairs, embedding=embeddings)


print("尝试保存到当前目录...")
faiss.save_local('app/faiss/app_use')
print("保存到当前目录成功！")