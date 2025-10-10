
 


import redis
import json
import uuid
from datetime import datetime

# 创建 Redis 连接池 (推荐生产环境使用)
pool = redis.ConnectionPool(
    host='47.96.110.140', 
    port=6939,
    password='wzCTMV!IQEllCSr#',
    max_connections=20  # 最大连接数
)

# 获取 Redis 连接
r = redis.StrictRedis(connection_pool=pool)

def process_design_requests(design_data):
    """处理设计请求的主函数"""
    try:
        

            # 3. 添加唯一ID (使用UUID4)
            unique_id = str(uuid.uuid4())
            # design_data["id"] = unique_id
            print(f"生成ID: {unique_id}")

            # 4. 添加时间戳
            # design_data["processed_at"] = datetime.now().isoformat()

            # 5. 转换回JSON字符串
            result_json = json.dumps(design_data, ensure_ascii=False)

            # 6. 推送到结果队列 (队列名: AutoDesignResultQueue)
            # print(result_json)
            r.rpush("AutoDesignResultQueue", result_json)
            result = r.lrange("AutoDesignResultQueue", 0, 10)
            length = r.llen("AutoDesignResultQueue")
            
            print("处理完成: 结果已推送到队列")
            print("队列长度：")
            print(length)
            # print("队列内容：")
            # print(result)

    except redis.RedisError as e:
        print(f"Redis操作错误: {e}")
    except Exception as e:
        print(f"处理异常: {e}")

if __name__ == "__main__":
    print("="*50)
    print("AutoDesign 队列处理服务已启动")
    print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)

    with open("result_v2.0.0.json", 'r', encoding='utf-8') as json_file:
        datas = json.load(json_file)
    
        process_design_requests(datas)