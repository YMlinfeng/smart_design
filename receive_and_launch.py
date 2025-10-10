import redis
import json
import uuid
from datetime import datetime
import time
import os
import ast
import re
from pathlib import Path
import torch
from copy import deepcopy
from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig
from peft import PeftModel
from accelerate import Accelerator
from torch.autograd import grad_mode

# 导入您的提示词模块
from sys_prompt import DESIGN_INSTRUCT_V4
from house_prompt import living_canteen_room, bedroom, balcony, toilet, study_room, Kitchen, general_prompt

# Redis连接配置
REDIS_CONFIG = {
    'host': '47.96.110.140',
    'port': 6939,
    'password': 'wzCTMV!IQEllCSr#',
    'max_connections': 20
}

# 模型配置
MODEL_CONFIG = {
    'model_path': "/root/autodl-tmp/models/qwen3_32b",
    'lora_weights': "/root/autodl-tmp/smart_design/lora/2.0/ckpt/09-18-23-32_eval_epoch4-p"
}

# 创建 Redis 连接池
pool = redis.ConnectionPool(**REDIS_CONFIG)
r = redis.StrictRedis(connection_pool=pool)

# 确保必要的目录存在
os.makedirs('json', exist_ok=True)
os.makedirs('results', exist_ok=True)
os.makedirs('experiments', exist_ok=True)

# 设置CUDA设备
os.environ['CUDA_VISIBLE_DEVICES'] = '0'
os.environ["HF_HUB_OFFLINE"] = '1'

class Qwen3ModelHandler:
    def __init__(self, model_path, lora_weights):
        self.model_path = model_path
        self.lora_weights = lora_weights
        self.model = None
        self.tokenizer = None
        self.device = None
        self.accelerator = None
        
    def load_model(self):
        """加载模型和tokenizer"""
        print("正在加载模型...")
        
        # 加载基础模型
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            trust_remote_code=True,
            torch_dtype=torch.bfloat16,
            attn_implementation="flash_attention_2",
            device_map="auto"
        )
        
        # 加载LoRA权重
        self.model = PeftModel.from_pretrained(
            self.model,
            self.lora_weights,
            autocast_adapter_dtype=False
        )
        self.model = self.model.merge_and_unload()
        
        # 加载tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        
        # 设置设备
        self.device = self.model.device
        self.accelerator = Accelerator()
        self.model = self.accelerator.prepare(self.model)
        
        print(f"模型已加载到设备: {self.device}")
        return self
    
    def prepare_messages(self, room_data, room_type):
        """准备模型输入消息"""
        messages = []
        messages.append({
            "role": "system",
            "content": DESIGN_INSTRUCT_V4
        })
        
        # 根据房间类型选择提示词
        if room_type.startswith("LivingRoom"):
            instruction = living_canteen_room
        elif room_type.startswith("SecondBedroom") or room_type.startswith("MasterBedroom"):
            instruction = bedroom
        elif room_type.startswith("Balcony"):
            instruction = balcony
        elif room_type.startswith("Bathroom"):
            instruction = toilet
        elif room_type.startswith("Study"):
            instruction = study_room
        elif room_type.startswith("Kitchen"):
            instruction = Kitchen
        else:
            instruction = general_prompt
            
        # 添加用户消息
        user_input = f"\n用户需求指令：请帮我整体设计一下{room_type}"
        messages.append({
            "role": "user",
            "content": "\n通用规则" + general_prompt + "\n房间JSON:" + str(room_data) + "\n用户生成指南：" + instruction + user_input,
        })
        
        return messages
    
    def generate_response(self, messages):
        """使用模型生成响应"""
        # 准备输入文本
        texts = []
        message_text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False
        )
        texts.append(message_text)
        
        # 标记化输入
        inputs = self.tokenizer(
            text=texts, 
            return_tensors="pt", 
            padding=True
        ).to(self.device)
        
        # 生成配置
        generation_config = GenerationConfig(
            do_sample=True,
            temperature=0.3,
            max_new_tokens=20000,
        )
        
        # 生成响应
        with grad_mode.inference_mode():
            self.model.eval()
            self.model.config.use_cache = True
            
            generate_ids = self.model.generate(**inputs, generation_config=generation_config)
            
            # 解码响应
            generated_ids = [
                output_ids[len(input_ids):] for input_ids, output_ids in zip(inputs.input_ids, generate_ids)
            ]
            output = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)
            
            return output[0]
    
    def process_room(self, room_data):
        """处理单个房间数据"""
        room_type = room_data["englishName"]
        print(f"处理房间: {room_type}")
        
        # 准备消息
        messages = self.prepare_messages(room_data, room_type)
        
        # 生成响应
        start_time = time.time()
        response = self.generate_response(messages)
        end_time = time.time()
        
        print(f"房间 {room_type} 处理完成，耗时: {end_time - start_time:.2f}秒")
        
        # 尝试解析响应
        try:
            parsed_data = ast.literal_eval(response)
            room_data.append(parsed_data)
        except (SyntaxError, ValueError):
            print(f"响应解析失败，存储原始文本")
            room_data["modelInfos"] = response
            
        return room_data

def push_result_to_queue(design_data):
    """将处理结果推送到结果队列"""
    try:
        # 添加处理时间戳
        design_data["processed_at"] = datetime.now().isoformat()
        
        # 转换回JSON字符串
        result_json = json.dumps(design_data, ensure_ascii=False)
        
        # 推送到结果队列
        r.rpush("AutoDesignResultQueue", result_json)
        
        # 获取队列信息
        queue_length = r.llen("AutoDesignResultQueue")
        recent_results = r.lrange("AutoDesignResultQueue", 0, 10)  # 获取最近10个结果
        
        print("处理完成: 结果已推送到队列")
        print(f"队列长度: {queue_length}")
        print("最近10个结果预览:")
        for i, result in enumerate(recent_results):
            print(f"{i+1}. {result.decode('utf-8')[:100]}...")  # 只显示前100个字符
            
    except redis.RedisError as e:
        print(f"Redis操作错误: {e}")
    except Exception as e:
        print(f"推送结果时发生异常: {e}")

def del_key(obj, key):
    """递归删除字典/列表中的指定 key"""
    if isinstance(obj, dict):
        obj.pop(key, None)
        for k, v in list(obj.items()):
            obj[k] = del_key(v, key)
    elif isinstance(obj, list):
        obj = [del_key(item, key) for item in obj]
    return obj

def format_number(value):
    """格式化数字，保留1位小数"""
    if isinstance(value, (int, float)):
        return round(float(value), 1)
    return value

def remove_z_coordinate(coord_str):
    """从坐标字符串中移除Z坐标"""
    if not isinstance(coord_str, str):
        return coord_str
    
    if coord_str.startswith("X=") and " Z=" in coord_str:
        parts = coord_str.split()
        if len(parts) >= 3:
            return f"{parts[0]} {parts[1]}"
    
    return coord_str

def transform_data(data):
    """转换数据：格式化数字并移除Z坐标"""
    if isinstance(data, dict):
        new_dict = {}
        for key, value in data.items():
            if key in ["isValid", "views", "rectangles", "heightToFloor", "height"]:
                continue
                
            if key in ["pos", "points", "centerPos", "clipLocations", "direction"]:
                if isinstance(value, list):
                    new_dict[key] = [remove_z_coordinate(format_number(item)) for item in value]
                else:
                    new_dict[key] = remove_z_coordinate(format_number(value))
            elif key == "rotator" and isinstance(value, dict):
                new_value = {k: format_number(v) for k, v in value.items() if k != "roll"}
                new_dict[key] = new_value
            elif key in ["box", "location", "scale", "min", "max"] and isinstance(value, dict):
                new_box = {}
                for box_key, box_value in value.items():
                    if isinstance(box_value, dict):
                        new_box[box_key] = {k: format_number(v) for k, v in box_value.items() if k != "z"}
                    elif box_key not in ["z", "isValid"]:
                        new_box[box_key] = format_number(box_value)
                new_dict[key] = new_box
            else:
                new_dict[key] = transform_data(value)
        return new_dict
    
    elif isinstance(data, list):
        return [transform_data(item) for item in data]
    
    elif isinstance(data, (int, float)):
        return format_number(data)
    
    else:
        return data

def process_design_data(design_data, model_handler):
    """处理设计数据"""
    task_id = design_data["taskId"]
    print(f"开始处理任务: {task_id}")
    
    # 复制并清理数据
    processed_data = deepcopy(design_data)
    del_list = ["isValid", "views", "rectangles", "heightToFloor", "height", 
                "clipLocations", "views", "lightParams", "lightInfos", "yDList", 
                "baseInfo", "wallHeight", "totalArea", "taskId"]
    
    for del_item in del_list:
        processed_data = del_key(processed_data, del_item)
    
    # 转换数据
    processed_data = transform_data(processed_data)
    
    # 处理每个房间
    new_room_list = []
    for room_data in design_data["roomList"]:
        try:
            processed_room = model_handler.process_room(room_data)
            new_room_list.append(processed_room)
        except Exception as e:
            print(f"处理房间时出错: {e}")
            new_room_list.append(room_data)  # 保留原始房间数据
    
    # 更新房间列表
    design_data["roomList"] = new_room_list
    
    # 保存结果
    result_filename = f"results/result_{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(result_filename, 'w', encoding='utf-8') as f:
        json.dump(design_data, f, ensure_ascii=False, indent=4)
    
    print(f"任务 {task_id} 处理完成，结果已保存到: {result_filename}")
    
    # 推送结果到队列
    push_result_to_queue(design_data)
    
    return design_data

def process_design_requests(model_handler):
    """处理设计请求的主函数"""
    try:
        # 从请求队列阻塞获取数据
        print("等待队列数据...")
        queue_data = r.blpop("AutoDesignRequestQueue", timeout=0)
        
        if queue_data:
            # 解包数据
            _, json_str = queue_data
            
            # 解析JSON数据
            try:
                design_data = json.loads(json_str)
                task_id = design_data.get("taskId", str(uuid.uuid4()))
                print(f"接收时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"任务ID: {task_id}")
                
                # 保存原始JSON
                with open(f'json/{task_id}.json', 'w', encoding='utf-8') as f:
                    json.dump(design_data, f, ensure_ascii=False, indent=4)
                
                # 处理数据
                result = process_design_data(design_data, model_handler)
                
            except json.JSONDecodeError:
                print("错误: 无效的JSON格式")
            except Exception as e:
                print(f"处理数据时出错: {e}")

    except redis.RedisError as e:
        print(f"Redis操作错误: {e}")
    except Exception as e:
        print(f"处理异常: {e}")

if __name__ == "__main__":
    print("="*50)
    print("AutoDesign 队列处理服务已启动")
    print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    
    # 加载模型
    model_handler = Qwen3ModelHandler(MODEL_CONFIG['model_path'], MODEL_CONFIG['lora_weights'])
    model_handler.load_model()
    
    # 持续监听队列
    while True:
        try:
            process_design_requests(model_handler)
        except Exception as e:
            print(f"主循环异常: {e}")
            time.sleep(5)  # 出错后等待5秒再继续