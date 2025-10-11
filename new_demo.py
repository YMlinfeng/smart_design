#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ===============================================================
# 1. 通用标准库  —— 基础功能 / 类型注解 / 时间日期
# ===============================================================
import os
import sys
import re
import ast
import csv
import math
import json
import shutil
import random
import datetime as DT
from copy import deepcopy
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

# 提高递归深度避免深层 JSON 处理时报错
sys.setrecursionlimit(8000)

# ===============================================================
# 2. 第三方库  —— 深度学习 / 数据集 / 加速器
# ===============================================================
import torch
import torch.nn.functional as F
from torch.autograd import grad_mode
from tqdm.auto import tqdm

from accelerate import Accelerator
from datasets import load_dataset, concatenate_datasets
from peft import LoraConfig, PeftModel
from transformers import (
    GenerationConfig,
    AutoTokenizer,
    Qwen3ForCausalLM,
)
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.modeling_outputs import CausalLMOutputWithPast
from liger_kernel.transformers import (
    LigerFusedLinearCrossEntropyLoss,
    apply_liger_kernel_to_qwen3,
)
from liger_kernel.transformers.model.loss_utils import LigerForCausalLMLoss

# ===============================================================
# 3. 项目本地依赖  —— 提示词文件
# ===============================================================
from sys_prompt import *
from house_prompt import *
from utilis.process_json import *

# ===============================================================
# 4. 环境变量配置
# ===============================================================
os.environ["HF_HUB_OFFLINE"] = "1"          # 离线加载 HuggingFace 权重
os.environ["CUDA_VISIBLE_DEVICES"] = "0"    # 指定可见显卡

print("CUDA 可用:", torch.cuda.is_available())
# pyright: reportAttributeAccessIssue=false
print("CUDA 版本:", torch.version.cuda)
print("显卡数量:", torch.cuda.device_count())
print("显卡名称:", torch.cuda.get_device_name())
print("显卡内存:", torch.cuda.get_device_properties(0).total_memory)
print("显卡类型:", torch.cuda.get_device_name())
print("显卡计算等级:", torch.cuda.get_device_capability())


# ===============================================================
# 5. 路径与数据清洗
# ===============================================================
EXPERIMENT_DIR = Path("experiments")
EXPERIMENT_DIR.mkdir(exist_ok=True, parents=True)
RESULT_DIR = Path("results")
RESULT_DIR.mkdir(exist_ok=True, parents=True)
JSON_DIR = Path("../data/户型训练json集-7.30/不带家具的户型json")
# JSON_ID_LIST = ["6524", "7143", "8362", "9485", "13130", "18009", "20177", "21989", "23435", "25175"]
# JSON_ID_LIST = ["6524", "6563", "6597", "6690", "6703", "18009", "20177", "21989", "23435", "25175"]
JSON_ID_LIST = ["6524", "6563"]
# Qwen3 思维闭合特殊 token id
THINK_END_ID = 151668
# 生成长度：与“超参数默认”不冲突（不涉及模型权重或训练），仅作为运行上限以免无限生成。
MAX_NEW_TOKENS = 128000


# ===============================================================
# 6. Qwen3 纯原生推理（按官方示范的方法）
# ===============================================================
def build_messages(room_data: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    根据房间英文名选择指令模板，构造 messages（system + user）。
    """
    room_en_name: str = room_data.get("englishName", "")

    if room_en_name.startswith("LivingRoom"):
        instruction = living_canteen_room
    elif room_en_name.endswith("Bedroom"):
        instruction = bedroom
    elif room_en_name.startswith("Balcony"):
        instruction = balcony
    elif room_en_name.startswith("Bathroom"):
        instruction = toilet
    elif room_en_name.startswith("Study"):
        instruction = study_room
    elif room_en_name.startswith("Kitchen"):
        instruction = Kitchen
    else:
        instruction = general_prompt

    messages = [
        {"role": "system", "content": DESIGN_INSTRUCT},
        {
            "role": "user",
            "content": (
                "通用规则：" + general_prompt +
                "\n房间JSON：" + str(room_data) +
                "\n用户生成指南：" + instruction
            ),
        },
    ]
    return messages


def generate_with_thinking(
    # model: Union[AutoModelForCausalLM, _BaseModelWithGenerate],
    model: Any,
    tokenizer: AutoTokenizer,
    messages: List[Dict[str, str]],
    max_new_tokens: int = MAX_NEW_TOKENS,
) -> Tuple[str, str]:
    """
    使用官方示范的方法：
    - apply_chat_template(enable_thinking=True)
    - generate
    - 以 THINK_END_ID(</think>) 将“思维内容”与“最终回答内容”拆分
    返回：(content, thinking_content)
    """
    # 确保有 pad_token，避免批量或长文本时的警告
    if tokenizer.pad_token_id is None and tokenizer.eos_token_id is not None:
        tokenizer.pad_token = tokenizer.eos_token

    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=True,  # 默认启用思维模式
    )

    model_inputs = tokenizer.__call__([text], return_tensors="pt").to(model.device) 

    # 可选：根据上下文长度钳制生成上限，防越界
    # input_len = model_inputs.input_ids.shape[1]
    # ctx = getattr(model.config, "max_position_embeddings", None) \
    #       or getattr(model.config, "max_sequence_length", None) \
    #       or 32768
    # safe_max_new = max(1, min(max_new_tokens, ctx - input_len))

    # 纯默认推理（不设温度等），仅限制上限长度 
    generated_ids = model.generate(
        **model_inputs,
        max_new_tokens=max_new_tokens,
    )

    # 取新生成部分
    output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist()

    # 切分思维与答案
    try:
        index = len(output_ids) - output_ids[::-1].index(THINK_END_ID)
    except ValueError:
        index = 0  # 未产出 </think> 时，认为无思维片段

    thinking_content = tokenizer.decode(output_ids[:index], skip_special_tokens=True).strip("\n").strip()
    content = tokenizer.decode(output_ids[index:], skip_special_tokens=True).strip("\n").strip()

    return content, thinking_content

# ===============================================================
# 7. 主流程
# ===============================================================
def main() -> None:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # —— 加载本地 Qwen3 模型（原始、无任何 Adapter/量化/自定义） —— #
    model_path = "/root/autodl-tmp/models/qwen3_32b"  # 本地模型路径
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype="auto",
        device_map="auto",
    )

    # 小提示：如需强制单卡，可改为 model.to(device) 并移除 device_map

    for json_id in JSON_ID_LIST:
        json_file = JSON_DIR / f"{json_id}.json"
        if not json_file.exists():
            print(f"[Warning] {json_file} 不存在，跳过。")
            continue

        # 实验日志（以 json_id + 时间戳记录）
        exp_file = EXPERIMENT_DIR / f"qwen_experiment_{json_id}_{DT.datetime.now():%Y%m%d_%H%M%S}.txt"

        with json_file.open("r", encoding="utf-8") as f:
            datas = json.load(f)

        sub_datas = deepcopy(datas)
        for k in ["isValid", "views", "rectangles", "heightToFloor", "height",
                  "clipLocations", "views", "lightParams", "lightInfos",
                  "yDList", "baseInfo", "wallHeight", "totalArea", "taskId"]:
            sub_datas = del_key(sub_datas, k)
        sub_datas = transform_data(sub_datas)

        new_room_list: List[Dict[str, Any]] = []

        # —— 遍历每个房间，独立生成 —— #
        for room_data in tqdm(datas.get("roomList", []), desc=f"Processing {json_id}"):
            room_en_name: str = room_data.get("englishName", "UnknownRoom")
            
            if room_en_name.startswith(("LivingRoom", "Study", "Kitchen")):
                print(f"跳过处理 {room_en_name}")
                continue

            messages = build_messages(room_data)

            with exp_file.open("a", encoding="utf-8") as log:
                log.write(f"实验时间: {DT.datetime.now():%Y-%m-%d %H:%M:%S}\n")
                log.write(f"数据文件: {json_file}\n")
                log.write("-" * 50 + "\n")
                log.write(f"[用户]\n{messages}\n")

                start = time.time()
                content, thinking = generate_with_thinking(model, tokenizer, messages)
                cost = time.time() - start

                # —— 解析返回值 —— #
                try:
                    parsed = safe_literal_eval(content)
                    room_data["modelInfos"] = parsed
                except Exception as e:
                    print(f"[ParseError] {e}，原样保留字符串。")
                    room_data["modelInfos"] = content

                new_room_list.append(room_data)

                # 写入日志
                if thinking:
                    log.write(f"[思维内容]\n{thinking}\n")
                log.write(f"[模型最终回答]\n{content}\n")
                log.write(f"响应时间: {cost:.2f}s\n")
                log.write("=" * 50 + "\n\n")

                print(f"房间 {room_en_name} 生成完成，耗时 {cost:.2f}s")

        # 保存结果到 JSON
        datas["roomList"] = new_room_list
        result_file = RESULT_DIR / f"result_{json_id}.json"
        with result_file.open("w", encoding="utf-8") as f:
            json.dump(datas, f, ensure_ascii=False, indent=4)

        print(f"[Done] {json_id} 结果写入 {result_file}")


# ===============================================================
# 8. CLI 入口
# ===============================================================
if __name__ == "__main__":
    main()