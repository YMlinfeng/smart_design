import pymysql
import random
import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# 数据库配置
DB_CONFIG = {
    "host": "115.159.86.177",
    "port": 3306,
    "user": "dream_vanwodesig",
    "password": "jsNz37nTnGLcDWc6",
    "database": "dream_vanwodesig",
    "charset": "utf8mb4"
}

# API 配置
API_URL = "http://dev.api.jiazhuangwuyou.com/intelligent/submitRenderTask"
#AUTH_TOKEN = "4cdcd859-3044-4a74-955d-53b7db733f24"
AUTH_TOKEN = "2fb47be1-ea4d-407e-b725-5ce50f30cb3b"

# 房间类型映射表
ROOM_TYPE_MAPPING = {
    1: {"name": "客厅", "englishName": "LivingRoom"},
    2: {"name": "主卧", "englishName": "MasterBedroom"},
    3: {"name": "次卧", "englishName": "SecondBedroom"},
    4: {"name": "厨房", "englishName": "Kitchen"},
    5: {"name": "卫生间", "englishName": "Bathroom"},
    6: {"name": "书房", "englishName": "StudyRoom"},
    7: {"name": "儿童房", "englishName": "KidsRoom"},
    8: {"name": "老人房", "englishName": "ElderlyRoom"},
    9: {"name": "衣帽间", "englishName": "Cloakroom"},
    10: {"name": "阳台", "englishName": "Balcony"}
}

# 全局配置
BATCH_SIZE = 400  # 每批处理的任务数量
MAX_WORKERS = 10  # 最大并发线程数
REQUEST_DELAY = 1  # 请求间隔时间(秒)

# 在全局配置部分添加一个变量
DESIGN_LIMIT = 70  # 可以修改这个数字来调整获取的全屋方案数量

def get_intelligent_designs(limit=4000):
    """获取多个全屋设计方案"""
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    sql = """
          SELECT id, house_id
          FROM dy_intelligent
          WHERE typeid = 2
            AND is_deleted = 0
            AND is_show = 1
          ORDER BY RAND()
              LIMIT %s \
          """
    cursor.execute(sql, (limit,))
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data

def get_house_ids(limit=4000):
    """获取多个户型ID"""
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    sql = """
          SELECT house_id
          FROM dy_scene_house
          WHERE is_deleted = 0
            AND is_show = 1
          ORDER BY RAND()
          LIMIT %s \
          """
    cursor.execute(sql, (limit,))
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data


def get_house_detail(house_id):
    """获取户型详情"""
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    sql = """
          SELECT *
          FROM dy_scene_house
          WHERE house_id = %s
            AND is_deleted = 0
            AND is_show = 1 \
          """
    cursor.execute(sql, (house_id,))
    data = cursor.fetchone()
    cursor.close()
    conn.close()
    return data


def parse_room_name_ids(room_name_ids):
    """解析room_name_ids字段"""
    if not room_name_ids:
        return []

    try:
        # 尝试解析为JSON数组
        if room_name_ids.startswith("[") and room_name_ids.endswith("]"):
            return json.loads(room_name_ids)

        # 尝试解析为逗号分隔的字符串
        if "," in room_name_ids:
            return [rid.strip() for rid in room_name_ids.split(",") if rid.strip()]

        # 尝试解析为单个ID
        return [room_name_ids]
    except json.JSONDecodeError:
        return []


def get_room_info(room_id):
    """根据room_id获取房间信息"""
    try:
        room_id_int = int(room_id)
        # 如果在映射表中，使用映射信息
        if room_id_int in ROOM_TYPE_MAPPING:
            return {
                "room_id": room_id_int,
                "name": ROOM_TYPE_MAPPING[room_id_int]["name"],
                "englishName": ROOM_TYPE_MAPPING[room_id_int]["englishName"]
            }

        # 如果不在映射表中，生成默认信息
        return {
            "room_id": room_id_int,
            "name": f"房间{room_id_int}",
            "englishName": f"Room{room_id_int}"
        }
    except (ValueError, TypeError):
        # 如果room_id不是数字，生成随机信息
        random_id = random.randint(10, 99)
        return {
            "room_id": random_id,
            "name": f"房间{random_id}",
            "englishName": f"Room{random_id}"
        }


def get_rooms_for_house(house_id):
    """获取户型的所有房间信息"""
    house_detail = get_house_detail(house_id)
    if not house_detail:
        return None

    # 解析room_name_ids
    room_name_ids = house_detail.get("room_name_ids", "")
    parsed_ids = parse_room_name_ids(room_name_ids)

    # 如果没有解析出任何ID，返回None
    if not parsed_ids:
        return None

    # 获取所有房间信息
    return [get_room_info(rid) for rid in parsed_ids]


def submit_render_task(intelligent_id, house_id, room_list):
    """调用渲染任务接口"""
    payload = {
        "render_task_detail": {
            "light_id": 12,
            "definition_id": 3,
            "composition_id": 1,
            "room_list": [
		 {
                    "room_id": 25,
                    "englishName": "LivingRoom",
                    "name": "客厅"
               },
                {
                    "room_id": 27,
                    "englishName": "DingRoom",
                    "name": "餐厅"
                },
                {
                    "room_id": 48,
                    "englishName": "DingRoom",
                    "name": "次卧"
                },
               {
                    "room_id": 24,
                    "englishName": "MasterBedroom",
                    "name": "主卧"
               },
		{
                    "room_id": 30,
                    "englishName": "Bathroom",
                    "name": "卫生间"
                },
		 {
                    "room_id": 26,
                   "englishName": "Kitchen",
                    "name": "厨房"
                },
                {
                    "room_id": 28,
                    "englishName": "Study",
                    "name": "书房"
                },
            ]
            
        },
        "house_id": house_id,
        "intelligent_id": intelligent_id
    }

    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Request-ID": f"batch-{intelligent_id}-{int(time.time())}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        return {
            "success": response.status_code == 200,
            "intelligent_id": intelligent_id,
            "house_id": house_id,
            "response": response.json(),
            "status_code": response.status_code
        }
    except Exception as e:
        return {
            "success": False,
            "intelligent_id": intelligent_id,
            "house_id": house_id,
            "error": str(e)
        }


def process_batch(batch):
    """处理一批任务"""
    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for design in batch:
            intelligent_id = design["id"]
            house_id = design.get("house_id", 0)

            # 如果方案没有关联户型，跳过
            if not house_id:
                results.append({
                    "success": False,
                    "intelligent_id": intelligent_id,
                    "house_id": None,
                    "error": "No house_id associated"
                })
                continue

            # 获取房间信息
            rooms = get_rooms_for_house(house_id)
            if not rooms:
                results.append({
                    "success": False,
                    "intelligent_id": intelligent_id,
                    "house_id": house_id,
                    "error": "No rooms found"
                })
                continue

            # 随机选择1-3个房间
            selected_rooms = random.sample(rooms, min(len(rooms), random.randint(1, 3)))

            # 提交任务
            future = executor.submit(
                submit_render_task,
                intelligent_id=intelligent_id,
                house_id=house_id,
                room_list=selected_rooms
            )
            futures.append(future)
            time.sleep(REQUEST_DELAY)  # 控制请求频率

        # 获取结果
        for future in as_completed(futures):
            results.append(future.result())

    return results


def main():
    print("开始批量执行渲染任务...")
    total_success = 0
    total_failed = 0

    # 获取所有符合条件的方案 - 使用DESIGN_LIMIT变量
    houses = get_house_ids(limit=5)  # 获取100个户型
    designs = get_intelligent_designs(limit=DESIGN_LIMIT)
    if not designs:
        print("未找到可用的全屋方案")
        return

    print(f"共找到 {len(houses)} 个户型， {len(designs)} 个全屋方案，开始批量处理...")

     # 创建任务列表：每个户型随机配对一个全屋方案
    tasks = []
    for house in houses:
        house_id = house["house_id"]
        # 随机选择一个全屋方案
        random_design = random.choice(designs)
        intelligent_id = random_design["id"]
        
        tasks.append({
            "id": intelligent_id,
            "house_id": house_id
        })

    # 分批处理
    for i in range(0, len(tasks), BATCH_SIZE):
        batch = tasks[i:i + BATCH_SIZE]
        print(f"\n正在处理第 {i // BATCH_SIZE + 1} 批，共 {len(batch)} 个任务...")

        batch_results = process_batch(batch)

        # 统计结果
        for result in batch_results:
            if result["success"]:
                total_success += 1
                print(f"成功: 案例ID {result['intelligent_id']}, 户型ID {result['house_id']}")
            else:
                total_failed += 1
                error_msg = result.get("error", result.get("response", {}).get("message", "未知错误"))
                print(f"失败: 案例ID {result['intelligent_id']}, 户型ID {result['house_id']}, 原因: {error_msg}")

    print("\n批量执行完成！")
    print(f"总计: 成功 {total_success} 个, 失败 {total_failed} 个")


if __name__ == "__main__":
    main()
