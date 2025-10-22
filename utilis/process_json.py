'''
定义各种数据处理工具函数

'''
# ===============================================================
# 1. 标准库
# ===============================================================
import os
import sys
import re
import ast
import json
import time
import datetime as DT
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Tuple

# 避免深层 JSON 递归报错
sys.setrecursionlimit(8000)

# ===============================================================
# 2. 第三方库（仅保留必要依赖）
# ===============================================================
import torch
from tqdm.auto import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer

# ===============================================================
# 3. 项目本地依赖（提示词）
# ===============================================================
from prompt.sys_prompt import *   
from prompt.house_prompt import * # 包含各房型的 instruction 片段

import json
import re


def safe_literal_eval(data_str: str) -> Any:
    """
    安全将字符串解析为 Python 对象，并对常见格式错误做修复。
    """
    # 提取 modelInfos 对应的数组部分
    match = re.search(r'"modelInfos"\s*:\s*(\[[\s\S]*\])', data_str)
    if match:
        data_str = match.group(1)
        try:
            return ast.literal_eval(data_str)
        except (SyntaxError, ValueError):
            pass

    fixed = data_str
    # 常见错误修复
    fixed = re.sub(r"\}\s*\{", "}, {", fixed)
    for field in ["location", "rotator", "scale"]:
        fixed = re.sub(
            fr"('isValid': True)\s*('{field}':)",
            r"\1, \2",
            fixed,
        )
    if fixed.count("{") > fixed.count("}"):
        fixed += "}" * (fixed.count("{") - fixed.count("}"))

    return ast.literal_eval(fixed)

def del_key(obj: Any, key: str) -> Any:
    """
    递归删除 dict / list 中指定键。
    """
    if isinstance(obj, dict):
        obj.pop(key, None)
        for k, v in list(obj.items()):
            obj[k] = del_key(v, key)
    elif isinstance(obj, list):
        obj = [del_key(item, key) for item in obj]
    return obj


def format_number(value: Any) -> Any:
    """
    数值保留 1 位小数，其余原样返回。
    """
    if isinstance(value, (int, float)):
        return round(float(value), 1)
    return value


def remove_z_coordinate(coord_str: Any) -> Any:
    """
    从 "X=xxx Y=xxx Z=xxx" 字符串移除 Z 坐标。
    """
    if not isinstance(coord_str, str):
        return coord_str
    if coord_str.startswith("X=") and " Z=" in coord_str:
        parts = coord_str.split()
        return " ".join(parts[:2])  # 仅 X Y
    return coord_str


def transform_data(data: Any) -> Any:
    """
    清洗 JSON：
    1) 去掉无用键；2) 坐标去 Z；3) 数值保留 1 位小数。
    """
    if isinstance(data, dict):
        new_dict = {}
        for key, value in data.items():
            if key in {
                "isValid", "views", "rectangles", "heightToFloor", "height",
            }:
                continue
            if key in {"pos", "points", "centerPos", "clipLocations", "direction"}:
                if isinstance(value, list):
                    new_dict[key] = [
                        remove_z_coordinate(format_number(v)) for v in value
                    ]
                else:
                    new_dict[key] = remove_z_coordinate(format_number(value))
            elif key == "rotator" and isinstance(value, dict):
                new_dict[key] = {
                    k: format_number(v) for k, v in value.items() if k != "roll"
                }
            elif key in {"box", "location", "scale", "min", "max"} and isinstance(value, dict):
                new_box = {}
                for box_k, box_v in value.items():
                    if isinstance(box_v, dict):
                        new_box[box_k] = {
                            kk: format_number(vv) for kk, vv in box_v.items() if kk != "z"
                        }
                    elif box_k != "z":
                        new_box[box_k] = format_number(box_v)
                new_dict[key] = new_box
            else:
                new_dict[key] = transform_data(value)
        return new_dict
    if isinstance(data, list):
        return [transform_data(item) for item in data]
    if isinstance(data, (int, float)):
        return format_number(data)
    return data




