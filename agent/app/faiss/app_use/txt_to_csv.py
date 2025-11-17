# 把app_use.txt转换为csv文件


import pandas as pd
import os

cur_dir = os.path.dirname(os.path.abspath(__file__))
txt_file_path = os.path.join(cur_dir,'app_use.txt')
with open(txt_file_path,'r',encoding='utf-8') as f:
    data = f.read().split('\n')

data_ls = []
for i in range(0,len(data),2):
    question = data[i].replace('User：','').replace('用户：','')
    answer = data[i+1].replace('Agent：','')
    type = 'app_use'
    # if '上传' not in question and '上传' not in answer:
    #     data_ls.append([type,question,answer])
    # else:
    #     continue
    data_ls.append([type,question,answer])

df = pd.DataFrame(data_ls,columns=['type','question','answer'])
csv_save_path = os.path.join(cur_dir,'app_use.csv')
df.to_csv(csv_save_path,index=False)