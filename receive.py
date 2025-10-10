
 


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

def process_design_requests():
    """处理设计请求的主函数"""
    try:
        # 1. 从请求队列阻塞获取数据 (队列名: AutoDesignRequestQueue)
        # 参数说明: 0 表示无限等待直到有数据
        print("等待中")
        # r.rpush("AutoDesignRequestQueue","demo")
        length = r.llen('AutoDesignRequestQueue')
        print(f"队列长度：{length}")
        queue_data = r.blpop("AutoDesignRequestQueue", timeout=0)
        print("已取出数据")
        if queue_data:
            # 解包数据 (返回格式: (list_name, value))
            _, json_str = queue_data
            
            # 2. 解析JSON数据
            try:
                design_data = json.loads(json_str)
                json_id = design_data["taskId"]
                print(f"接收时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                # print(f"原始数据: {design_data}")
                with open(f'json/{json_id}.json', 'w', encoding='utf-8') as f:
                    json.dump(design_data, f, ensure_ascii=False, indent=4)
            except json.JSONDecodeError:
                print("错误: 无效的JSON格式")
                return


    except redis.RedisError as e:
        print(f"Redis操作错误: {e}")
    except Exception as e:
        print(f"处理异常: {e}")

if __name__ == "__main__":
    print("="*50)
    print("AutoDesign 队列处理服务已启动")
    print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    
    # 持续监听队列
    while True:
        process_design_requests()