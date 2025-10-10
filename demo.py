
from openai import OpenAI
import base64
import os
from pathlib import Path
import csv
# llm部分需要调用第三方的或者自己部署的多模态模型
import shutil
import json
import time
import random
from sys_prompt import *
from house_prompt import *
import torch
import os
import random
import sys
# from vllm import LLM
sys.setrecursionlimit(8000)
import math
from sys_prompt import *

from importlib.machinery import SourcelessFileLoader
import json
from copy import deepcopy
from transformers.modeling_outputs import (
    BaseModelOutputWithPast,
    CausalLMOutputWithPast,
    QuestionAnsweringModelOutput,
    SequenceClassifierOutputWithPast,
    TokenClassifierOutput,
)
from liger_kernel.transformers import LigerFusedLinearCrossEntropyLoss
import time
from liger_kernel.transformers.model.loss_utils import LigerForCausalLMLoss
os.environ["HF_HUB_OFFLINE"] = '1'
os.environ['CUDA_VISIBLE_DEVICES'] = '0'
from accelerate import Accelerator
from datasets import load_dataset, concatenate_datasets
from dataclasses import dataclass, field
from typing import Optional, List, Union, Tuple
import os
from transformers import GenerationConfig
from datetime import datetime
import datetime as DT
from peft import (
    LoraConfig, get_peft_model, PeftModel,
)
from transformers import Qwen3ForCausalLM, AutoTokenizer,AutoModelForCausalLM
from tqdm.auto import tqdm
import torch.nn.functional as F
print(torch.version.cuda)
compute_capability = torch.cuda.get_device_capability()
print(f"显卡的计算等级为: {compute_capability}")
import jsonlines
from torch.autograd import grad_mode

model_path = "/root/autodl-tmp/models/qwen3_32b"

# ==================================


from liger_kernel.transformers import LigerFusedLinearCrossEntropyLoss,apply_liger_kernel_to_qwen3

apply_liger_kernel_to_qwen3(
    #rope=False,
    swiglu=True,
    cross_entropy=False,
    fused_linear_cross_entropy=False,
    rms_norm=True
)

class HyperParameters:
    epoch: Optional[int] = field(default=5)
    train_batch_size: Optional[int] = field(default=1)
    eval_batch_size: Optional[int] = field(default=2)
    gradient_accumulation_steps: Optional[int] = field(default=4)
    lr: Optional[float] = field(default=2e-5)
    weight_decay: Optional[float] = field(default=1e-2)
    gradient_checkpointing: Optional[bool] = field(default=True)
    lora_r: Optional[int] = field(default=64)
    lora_alpha: Optional[int] = field(default=512)
    max_grad_norm: Optional[float] = field(default=1.0)
    output_dir: Optional[str] = field(default="lora2.5/senti_new")
    log_step: Optional[int] = field(default=5)
    eval_step: Optional[int] = field(default=20)
    nef_tune: Optional[bool] = field(default=False)
    noise_alpha: Optional[int] = field(default=2)
    bf16: Optional[bool] = field(default=True)
    save_log: Optional[bool] = field(default=False)
    unsloth: Optional[bool] = field(default=False)
    max_pixels: Optional[int] = field(default=2000 * 28 * 28)


config = HyperParameters()
class Qwen3_with_fused_CE(Qwen3ForCausalLM):
    def forward(
            self,
            input_ids: Optional[torch.LongTensor] = None,
            attention_mask: Optional[torch.Tensor] = None,
            position_ids: Optional[torch.LongTensor] = None,
            past_key_values: Optional[List[torch.FloatTensor]] = None,
            inputs_embeds: Optional[torch.FloatTensor] = None,
            labels: Optional[torch.LongTensor] = None,
            use_cache: Optional[bool] = None,
            output_attentions: Optional[bool] = None,
            output_hidden_states: Optional[bool] = None,
            cache_position: Optional[torch.LongTensor] = None,
            logits_to_keep: Union[int, torch.Tensor] = 0,
            skip_logits: Optional[bool] = None,
            **kwargs,
        ) -> CausalLMOutputWithPast:
            r"""
                labels (`torch.LongTensor` of shape `(batch_size, sequence_length)`, *optional*):
                    Labels for computing the masked language modeling loss. Indices should either be in `[0, ...,
                    config.vocab_size]` or -100 (see `input_ids` docstring). Tokens with indices set to `-100` are ignored
                    (masked), the loss is only computed for the tokens with labels in `[0, ..., config.vocab_size]`.
        
                logits_to_keep (`int` or `torch.Tensor`, *optional*):
                    If an `int`, compute logits for the last `logits_to_keep` tokens. If `0`, calculate logits for all
                    `input_ids` (special case). Only last token logits are needed for generation, and calculating them only for that
                    token can save memory, which becomes pretty significant for long sequences or large vocabulary size.
                    If a `torch.Tensor`, must be 1D corresponding to the indices to keep in the sequence length dimension.
                    This is useful when using packed tensor format (single dimension for batch and sequence length).
        
            Returns:
        
            Example:
        
            ```python
            >>> from transformers import AutoTokenizer, Qwen3ForCausalLM
        
            >>> model = Qwen3ForCausalLM.from_pretrained("Qwen/Qwen3-8B")
            >>> tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-8B")
        
            >>> prompt = "Hey, are you conscious? Can you talk to me?"
            >>> inputs = tokenizer(prompt, return_tensors="pt")
        
            >>> # Generate
            >>> generate_ids = model.generate(inputs.input_ids, max_length=30)
            >>> tokenizer.batch_decode(generate_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]
            "Hey, are you conscious? Can you talk to me?\nI'm not conscious, but I can talk to you."
            ```"""
            output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
            output_hidden_states = (
                output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
            )
        
            # decoder outputs consists of (dec_features, layer_state, dec_hidden, dec_attn)
            outputs = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                position_ids=position_ids,
                past_key_values=past_key_values,
                inputs_embeds=inputs_embeds,
                use_cache=use_cache,
                output_attentions=output_attentions,
                output_hidden_states=output_hidden_states,
                cache_position=cache_position,
                **kwargs,
            )
        
            hidden_states = outputs[0]
            # Only compute necessary logits, and do not upcast them to float if we are not computing the loss
            slice_indices = slice(-logits_to_keep, None) if isinstance(logits_to_keep, int) else logits_to_keep
            kept_hidden_states = hidden_states[:, slice_indices, :]
        
            shift_labels = kwargs.pop("shift_labels", None)
            logits = None
            loss = None
        
            if skip_logits and labels is None and shift_labels is None:
                raise ValueError("skip_logits is True, but labels and shift_labels are None")
        
            if skip_logits is None:
                # By default, if in training mode, don't materialize logits
                skip_logits = self.training and (labels is not None or shift_labels is not None)
        
            if skip_logits:
                loss = LigerForCausalLMLoss(
                    hidden_states=kept_hidden_states,
                    lm_head_weight=self.lm_head.weight,
                    labels=labels,
                    shift_labels=shift_labels,
                    hidden_size=self.config.hidden_size,
                    **kwargs,
                )
        
            else:
                logits = self.lm_head(kept_hidden_states)
                if labels is not None:
                    loss = self.loss_function(
                        logits=logits,
                        labels=labels,
                        vocab_size=self.config.vocab_size,
                        **kwargs,
                    )
        
            return CausalLMOutputWithPast(
                loss=loss,
                logits=logits,
                past_key_values=outputs.past_key_values,
                hidden_states=outputs.hidden_states,
                attentions=outputs.attentions,
            )


def getModel(lora_r, lora_alpha,model_path):

    model = Qwen3_with_fused_CE.from_pretrained(model_path,
                                                        trust_remote_code=True,
                                                        torch_dtype=torch.bfloat16,
                                                        attn_implementation="flash_attention_2",
                                                        device_map = "auto")


       

    model.enable_input_require_grads()
    if not config.unsloth:
        lora_config = LoraConfig(
            r=lora_r,
            lora_alpha=lora_alpha,
            lora_dropout=0.1,
            # use_rslora=True,
            #modules_to_save=['merger'],
            # inference_mode=False,
            bias="none",
            # target_modules="all-linear",
            target_modules=['down_proj', 'gate_proj', 'o_proj', 'up_proj', 'q_proj', 'k_proj', 'v_proj'],
            task_type="CAUSAL_LM",
        )
        # model=get_peft_model(model, lora_config,autocast_adapter_dtype=False)
        

    

    LORA_WEIGHTS = "/root/autodl-tmp/smart_design/lora/2.0/ckpt/09-18-23-32_eval_epoch4-p"
    model = PeftModel.from_pretrained(
        model,
        LORA_WEIGHTS,
        autocast_adapter_dtype=False
    )
    model = model.merge_and_unload()

    return model



    

def testFn(tokenizer,messages,device):
    texts = []


    message = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False
        )
            
    texts.append(message)
    # print(message)

    messages =tokenizer(
        text=texts, return_tensors="pt", padding=True
    ).to(device)
        
    return messages

def get_response(model,tokenizer,messages,device):
    def get_original_text(inputs) -> List[str]:
        inputs[inputs==-100]=self.tokenizer.pad_token_id
        return self.tokenizer.batch_decode(inputs, skip_special_tokens=True)
    print(os.environ['CUDA_VISIBLE_DEVICES'])
     

    accelerator = Accelerator()
    
    messages = testFn(tokenizer,messages,device)
    print(messages)
    model= accelerator.prepare(
        model
    )

    torch.cuda.empty_cache()
    model = accelerator.prepare(
            model
        )
    model.eval()
    model.config.use_cache = True
    generation_config = GenerationConfig(
        do_sample=True,
        temperature=0.3,
        max_new_tokens=20000,
    )
    with grad_mode.inference_mode():
        generate_ids = model.generate(**messages, generation_config=generation_config)

        generated_ids = [
            output_ids[len(input_ids):] for input_ids, output_ids in zip(messages.input_ids, generate_ids)
        ]
        output = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)
        print(output)
        return output[0]

import ast


def safe_literal_eval(data_str):
    # 尝试直接解析
    try:
        return ast.literal_eval(data_str)
    except SyntaxError:
        pass
    
    # 修复常见问题
    fixed = data_str
    
    # 修复缺失逗号
    fixed = re.sub(r'\}\s*\{', '},{', fixed)
    
    # 添加缺失的逗号在属性之间
    fixed = re.sub(r"('isValid': True)\s*('location':)", r"\1, \2", fixed)
    fixed = re.sub(r"('isValid': True)\s*('rotator':)", r"\1, \2", fixed)
    fixed = re.sub(r"('isValid': True)\s*('scale':)", r"\1, \2", fixed)
    
    # 移除重复元素（示例）
    # fixed = re.sub(r"{'iD': '11987', 'type': 'Niche'.*?},", "", fixed, count=1)
    
    # 确保所有大括号匹配
    open_braces = fixed.count('{')
    close_braces = fixed.count('}')
    if open_braces > close_braces:
        fixed += '}' * (open_braces - close_braces)
    
    return ast.literal_eval(fixed)

# 确保experiments目录存在
experiment_dir = "experiments"
os.makedirs(experiment_dir, exist_ok=True)


def del_key(obj, key):
    """递归删除字典/列表中的指定 key"""
    if isinstance(obj, dict):
        # 先删除顶层的 key
        obj.pop(key, None)
        # 再递归处理 value
        for k, v in list(obj.items()):
            obj[k] = del_key(v, key)
    elif isinstance(obj, list):
        # 递归处理 list 中的每个元素
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
    
    # 处理类似 "X=681.792 Y=511.344 Z=0.000" 的坐标
    if coord_str.startswith("X=") and " Z=" in coord_str:
        parts = coord_str.split()
        if len(parts) >= 3:
            # 保留X和Y部分
            return f"{parts[0]} {parts[1]}"
    
    return coord_str

def transform_data(data):
    """转换数据：格式化数字并移除Z坐标"""
    if isinstance(data, dict):
        # 处理字典
        new_dict = {}
        for key, value in data.items():
            if key in ["isValid","views","rectangles","heightToFloor","height"]:
                continue
            # 特殊处理坐标字段
            if key in ["pos", "points", "centerPos", "clipLocations","direction"]:
                if isinstance(value, list):
                    new_dict[key] = [remove_z_coordinate(format_number(item)) for item in value]
                else:
                    new_dict[key] = remove_z_coordinate(format_number(value))
            # 特殊处理包含坐标的对象
            elif key == "rotator" and isinstance(value, dict):
                # 保留旋转器但删除Z分量
                new_value = {k: format_number(v) for k, v in value.items() if k != "roll"}
                new_dict[key] = new_value
            elif key in[ "box", "location","scale","min","max"] and isinstance(value, dict) :
                # 处理边界框，删除Z坐标
                new_box = {}
                for box_key, box_value in value.items():
                    if isinstance(box_value, dict):
                        new_box[box_key] = {k: format_number(v) for k, v in box_value.items() if k != "z"}
                    elif box_key not in ["z","isValid"]:
                        new_box[box_key] = format_number(box_value)
                new_dict[key] = new_box
            else:
                new_dict[key] = transform_data(value)
        return new_dict
    
    elif isinstance(data, list):
        # 处理列表
        return [transform_data(item) for item in data]
    
    elif isinstance(data, (int, float)):
        # 格式化数字
        return format_number(data)
    
    else:
        return data

from tqdm import tqdm
if __name__ == '__main__':
    model_path = "/root/autodl-tmp/models/qwen3_32b"
    model = getModel(config.lora_r, config.lora_alpha,model_path)
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    # 打开JSON文件并读取内容
    json_path = 'data/户型训练json集-7.30/不带家具的户型json/'
    json_list = ['6524','7143','8362','9485','13130','18009','20177','21989','23435','25175']
    for json_id in json_list:
        # 生成带时间戳的实验文件名
        json_file = json_path + json_id + ".json"
        experiment_filename = f"qwen_experiment_{time.strftime('%Y%m%d_%H%M%S')}.txt"
        experiment_filepath = os.path.join(experiment_dir, experiment_filename)
        image_list = []
        new_room_list = []
        with open(json_file, 'r', encoding='utf-8') as json_file:
            datas = json.load(json_file)
            sub_datas = deepcopy(datas)
    
            del_list = ["isValid","views","rectangles","heightToFloor","height", "clipLocations","views", "lightParams", "lightInfos", "yDList", "baseInfo","wallHeight","totalArea","taskId"]
            for del_item in del_list:
                sub_datas = del_key(sub_datas,del_item)
    
            # print(sub_datas)
    
            sub_datas = transform_data(sub_datas)
            for data in datas["roomList"]:
                messages = []
                messages.append({
                    "role": "system",
                    "content": DESIGN_INSTRUCT_V4
                })
                room = data["englishName"]
                # print(room)
                if room.startswith("LivingRoom"):
                    instruction = living_canteen_room
                elif room.startswith("SecondBedroom") or room.startswith("MasterBedroom"):
                    instruction = bedroom
                elif room.startswith("Balcony"):
                    instruction = balcony
                elif room.startswith("Bathroom"):
                    instruction = toilet
                elif room.startswith("Study"):
                    instruction = study_room
                elif room.startswith("Kitchen"):
                    instruction = Kitchen
                else:
                    instruction = general_prompt
                # print("-"*20)
                # print(data["name"])
                # 打开实验记录文件（追加模式）
                with open(experiment_filepath, 'a', encoding='utf-8') as log_file:
                    # 写入初始信息
                    log_file.write(f"实验开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    # log_file.write(f"模型: {model}\n")
                    log_file.write(f"数据文件: {json_file}\n")
                    log_file.write("-" * 50 + "\n\n")
    
                    user_input = f"\n用户需求指令：请帮我整体设计一下{room}"
                    # print(user_input)
                    # 记录用户输入
                    # print(sub_datas)
                    messages.append(
                        {
                            "role": "user",
                            "content":"\n通用规则"+ general_prompt + "\n房间JSON:" + str(data) + "\n用户生成指南：" + instruction,
                        })
                    log_file.write(f"[用户] {messages}\n")
                    # print(messages)
                    # history_messages.append({"role": "user", "content": user_input})
    
                    start_time = time.time()
                    assistant_output = get_response(model,tokenizer,messages,model.device)
                    end_time = time.time()
                    try:
                        parsed_data = ast.literal_eval(assistant_output)
                        data["modelInfos"] = parsed_data
                        new_room_list.append(data)
                    except SyntaxError as e:
                        print(f"解析错误: {e},存储字符串")
                        data["modelInfos"] = assistant_output
                        new_room_list.append(data)
                        # 这里可以添加更详细的错误处理
                    # new_room_list.append(assistant_output)
                    # 记录模型回答
                    log_file.write(f"[模型] {assistant_output}\n")
                    log_file.write(f"响应时间: {end_time - start_time:.2f}秒\n")
                    log_file.write("-" * 50 + "\n\n")
    
                    # 控制台输出保持不变
                    print("\n消耗时间为：{}".format(end_time - start_time))
                    print("\n")
            datas["roomList"] = new_room_list
            # 将字典保存为JSON文件
            with open(f'results/result_{json_id}.json', 'w', encoding='utf-8') as f:
                json.dump(datas, f, ensure_ascii=False, indent=4)






