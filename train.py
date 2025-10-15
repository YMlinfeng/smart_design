import torch
import os
import random
import sys
import unsloth
# from vllm import LLM
sys.setrecursionlimit(8000)
import math
from sys_prompt import *
from house_prompt import *

from importlib.machinery import SourcelessFileLoader
import json


from transformers.modeling_outputs import (
    BaseModelOutputWithPast,
    CausalLMOutputWithPast,
    QuestionAnsweringModelOutput,
    SequenceClassifierOutputWithPast,
    TokenClassifierOutput,
)
from liger_kernel.transformers import LigerFusedLinearCrossEntropyLoss
from unsloth import FastLanguageModel,FastModel
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

# 超参数
@dataclass
class HyperParameters:
    epoch: Optional[int] = field(default=5)
    train_batch_size: Optional[int] = field(default=1)
    eval_batch_size: Optional[int] = field(default=1)
    gradient_accumulation_steps: Optional[int] = field(default=4)
    lr: Optional[float] = field(default=2e-5)
    weight_decay: Optional[float] = field(default=1e-2)
    gradient_checkpointing: Optional[bool] = field(default=True)
    lora_r: Optional[int] = field(default=64)
    lora_alpha: Optional[int] = field(default=512)
    max_grad_norm: Optional[float] = field(default=1.0)
    output_dir: Optional[str] = field(default="lora/2.0/ckpt")
    log_step: Optional[int] = field(default=5)
    eval_step: Optional[int] = field(default=50)
    nef_tune: Optional[bool] = field(default=False)
    noise_alpha: Optional[int] = field(default=2)
    bf16: Optional[bool] = field(default=True)
    save_log: Optional[bool] = field(default=False)
    unsloth: Optional[bool] = field(default=True)



config = HyperParameters()




DATA_TRAIN = "data/dataset_2.0/train.json"
DATA_VAL = "data/dataset_2.0/val.json"
DATA_TEST = "data/dataset_2.0/test.json"

CUTOFF_LEN = 100000


# model_path = "models/qwen2.5_7b"
model_path = "/root/autodl-tmp/models/qwen3_32b"



tokenizer = AutoTokenizer.from_pretrained(model_path)

from liger_kernel.transformers import LigerFusedLinearCrossEntropyLoss,apply_liger_kernel_to_qwen3

apply_liger_kernel_to_qwen3(
    #rope=False,
    swiglu=True,
    cross_entropy=False,
    fused_linear_cross_entropy=False,
    rms_norm=True
)
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
    
def getModel(lora_r, lora_alpha):

    if not config.unsloth:
        model = Qwen3_with_fused_CE.from_pretrained(model_path,
                                                        trust_remote_code=True,
                                                        torch_dtype=torch.bfloat16,
                                                        attn_implementation="flash_attention_2",
                                                        device_map = "auto")
    else:
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=model_path,
            max_seq_length=CUTOFF_LEN,
            dtype=None,
            load_in_4bit=False,
            local_files_only=True,
            use_gradient_checkpointing="unsloth",
        )

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
        model=get_peft_model(model, lora_config,autocast_adapter_dtype=False)

    else:
        model = FastLanguageModel.get_peft_model(
            model,
            # finetune_vision_layers=False,  # False if not finetuning vision part
            # finetune_language_layers=True,  # False if not finetuning language part
            # finetune_attention_modules=True,  # False if not finetuning attention layers
            # finetune_mlp_modules=True,  # False if not finetuning MLP layers
            r=64,  # Choose any number > 0 ! Suggested 8, 16, 32, 64, 128
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                            "gate_proj", "up_proj", "down_proj", ],
            lora_alpha=512,
            lora_dropout=0.05,  # Supports any, but = 0 is optimized
            bias="none",  # Supports any, but = "none" is optimized
            # [NEW] "unsloth" uses 30% less VRAM, fits 2x larger batch sizes!
            use_gradient_checkpointing="unsloth",  # True or "unsloth" for very long context
            random_state=random.randint(0, 100000),
        )

    # LORA_WEIGHTS = "/root/autodl-tmp/smart_design/lora/ckpt/08-04-11-29_eval_epoch3-p"
    # model = PeftModel.from_pretrained(
    #     model,
    #     LORA_WEIGHTS,
    #     autocast_adapter_dtype=False
    # )
    # model = model.merge_and_unload()

    return model



class CustomCollateFn:
    def __init__(self, mode):
        self.mode = mode
        self.tokenizer = tokenizer
    
        if self.mode == "train":
            self._caller=self.trainFn
        elif self.mode == "eval":
            self._caller = self.evalFn
        elif self.mode == "test":
            self._caller = self.testFn

    def __call__(self, examples):
        return self._caller(examples)

    

    def trainFn(self, examples):
        texts = []
        batch_size = len(examples)
       
        def get_original_text(inputs) -> List[str]:
            inputs[inputs==-100]=self.tokenizer.pad_token_id
            return self.tokenizer.batch_decode(inputs, skip_special_tokens=True)
        def find_last_match_indices(row, target):
            # 从右到左查找目标片段的起始位置
            row_len = row.size(0)
            target_len = target.size(0)
            for i in range(row_len - target_len, -1, -1):
                if torch.equal(row[i:i + target_len], target):
                    return i
            return -1
        for example in examples:
            room = example["room_json"]["englishName"]
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
            messages = [
                {
                    "role": "system",
                    "content": DESIGN_INSTRUCT_V4,
                },
                {
                    "role": "user",
                    "content":"\n通用规则"+ general_prompt + "\n房间JSON:" + str(example["room_json"]) + "\n用户生成指南：" + instruction,
                },
                {
                    "role": "assistant",
                    "content":str(example["output"]),
                },
            ]
            message = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=False,
                enable_thinking=False
            ).rstrip("\n")
            # print(message)
            texts.append(message)
        batch = self.tokenizer(
            text=texts, return_tensors="pt", padding=True
        )

        labels = batch["input_ids"].clone()
        target = torch.tensor([151644, 77091, 198])
        # target = torch.tensor([151645, 198])
        # print(get_original_text(target))
        start_indices = []
        for i in range(batch_size):
            label = labels[i]
            start_idx = find_last_match_indices(label, target)
            start_indices.append(start_idx)

        # 创建mask并设置mask
        mask = torch.zeros_like(labels, dtype=torch.bool)
        for i in range(batch_size):
            start_idx = start_indices[i]
            if start_idx >= 0:
                end_idx = start_idx + len(target)
                mask[i, :end_idx] = True  # 包括target本身

        labels[mask] = -100
        # print(get_original_text(labels))
        batch["labels"] = labels
        assert len(batch["labels"][0]) == len(batch["input_ids"][0])
        return batch

    def evalFn(self, examples):
        texts = []
        labels = []
        for example in examples:
            room = example["room_json"]["englishName"]
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
            messages = [
                {
                    "role": "system",
                    "content": DESIGN_INSTRUCT_V4,
                },
                {
                    "role": "user",
                    "content":"\n通用规则"+ general_prompt + "\n房间JSON:" + str(example["room_json"]) + "\n用户生成指南：" + instruction,
                }
            ]
            message = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False
            )
            # print(message)
            texts.append(message)
        batch = self.tokenizer(
            text=texts, return_tensors="pt", padding=True
        )
        labels = [str(example['output']) for example in examples]
        batch["labels"] = self.tokenizer(labels, padding=True, return_tensors="pt",
                                         return_attention_mask=False).input_ids
    
        return batch

    def testFn(self, examples):
        texts = []

       
        for example in examples:
            room = example["room_json"]["englishName"]
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
            messages = [
                {
                    "role": "system",
                    "content": DESIGN_INSTRUCT_V4,
                },
                {
                    "role": "user",
                    "content":"\n通用规则"+ general_prompt + "\n房间JSON:" + str(example["room_json"]) + "\n用户生成指南：" + instruction,
                }
            ]
            message = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False
            )
            
            texts.append(message)


        batch = self.tokenizer(
            text=texts, return_tensors="pt", padding=True
        )
        ids =[str(example["id"]) for example in examples]
        house_ids = [str(example["house_id"]) for example in examples]
        batch["id"] = self.tokenizer(ids, padding=True, return_tensors="pt",
                                     return_attention_mask=False).input_ids
        batch["house_id"] = self.tokenizer(house_ids, padding=True, return_tensors="pt",
                                     return_attention_mask=False).input_ids
        
        return batch

    


def getDataLoader(train_batch_size, eval_batch_size):
    train_data = load_dataset("json", data_files=DATA_TRAIN, keep_in_memory=True)["train"]
    val_data = load_dataset("json", data_files=DATA_VAL, keep_in_memory=True)["train"]
    # print(type(train_data))

    


   
    train_collate_fn = CustomCollateFn(mode="train")
    val_collate_fn = CustomCollateFn(mode="eval")


    train_loader = torch.utils.data.DataLoader(dataset=train_data,
                                               batch_size=train_batch_size,
                                               collate_fn=train_collate_fn,
                                               shuffle=True,
                                               pin_memory=True,
                                               num_workers=4,
                                               drop_last=False)
    eval_loader = torch.utils.data.DataLoader(dataset=val_data,
                                              batch_size=eval_batch_size,
                                              collate_fn=val_collate_fn,
                                              shuffle=False,
                                              num_workers=4,
                                              pin_memory=True,
                                              drop_last=False)
    return train_loader, eval_loader


import csv
from torch.utils.tensorboard import SummaryWriter
from sklearn.metrics import f1_score
from collections import Counter
from torch.autograd import grad_mode
import re
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
import jieba



class smart_design_Trainer:
    def __init__(self, model, optimizer, tokenizer, dataloader, config):
        self.model = model
        self.optimizer, self.scheduler = optimizer
        self.train_loader, self.eval_loader = dataloader
        self.tokenizer = tokenizer
        self.config = config
        self.best_metric = 0.0
        self.eval_times = 0
        if self.config.save_log:
            self.writer = SummaryWriter("cail_log/instruction")

    from collections import Counter


    
    def weighted_average_accuracy(self, predictions, true_labels, classes):
        rsr_predictions = [p for p, c in zip(predictions, classes) if c == "rsr"]
        rse_predictions = [p for p, c in zip(predictions, classes) if c == "rse"]
        jsi_predictions = [p for p, c in zip(predictions, classes) if c == "jsi"]
        spr_en_predictions = [p for p, c in zip(predictions, classes) if c == "spr_en"]
        spr_zh_predictions = [p for p, c in zip(predictions, classes) if c == "spr_zh"]
        
        rsr_true_labels = [t for t, c in zip(true_labels, classes) if c == "rsr"]
        rse_true_labels = [t for t, c in zip(true_labels, classes) if c == "rse"]
        jsi_true_labels = [t for t, c in zip(true_labels, classes) if c == "jsi"]
        spr_en_true_labels = [p for p, c in zip(true_labels, classes) if c == "spr_en"]
        spr_zh_true_labels = [p for p, c in zip(true_labels, classes) if c == "spr_zh"]
        
        
        def calculate_accuracy(predictions, true_labels):
            """计算单个任务的accuracy"""
            correct = 0
            total = len(true_labels)
            for p, t in zip(predictions, true_labels):
                if p == t:
                    correct += 1
            return correct / total if total > 0 else 0
        
        # 计算每个任务的accuracy
        rsr_accuracy = calculate_accuracy(rsr_predictions, rsr_true_labels)
        rse_accuracy = calculate_accuracy(rse_predictions, rse_true_labels)
        jsi_accuracy = calculate_accuracy(jsi_predictions, jsi_true_labels)
        spr_en_accuracy = calculate_accuracy(spr_en_predictions, spr_en_true_labels)
        spr_zh_accuracy = calculate_accuracy(spr_zh_predictions, spr_zh_true_labels)
        
        # 返回两个任务accuracy的平均值
        return {
            "rsr_accuracy": round(rsr_accuracy,5),
            "rse_accuracy": round(rse_accuracy,5),
            "jsi_accuracy": round(jsi_accuracy,5),
            "spr_en_accuracy": round(spr_en_accuracy,5),
            "spr_zh_accuracy": round(spr_zh_accuracy,5),
            "score": round((rsr_accuracy + rse_accuracy + jsi_accuracy) / 3,5)
        }

    def evaluation(self, model, eval_loader):
        def get_original_text(inputs) -> List[str]:
            inputs[inputs==-100]=self.tokenizer.pad_token_id
            return self.tokenizer.batch_decode(inputs, skip_special_tokens=True)

        torch.cuda.empty_cache()
        if self.config.unsloth:
            FastLanguageModel.for_inference(model)
        model.eval()
        #model.config.pad_token_id = self.tokenizer.pad_token_id
        #model.config.eos_token_id = self.tokenizer.eos_token_id
        model.config.use_cache = True
        generation_config = GenerationConfig(
            do_sample=False,
            max_new_tokens=1000,
        )
        eval_bar = tqdm(colour="yellow", desc=f"Evaluation(eval_batch_size={config.eval_batch_size})",
                        total=len(eval_loader), dynamic_ncols=True)
        predictions = []
        true_labels = []
        start_time = time.time()
        for step, batch in enumerate(eval_loader):
            model.eval()

            labels = get_original_text(batch.pop("labels"))[0]
            


            true_labels.append(labels)

            with grad_mode.inference_mode():
                # if len(batch['input_ids']) > 1:
                generate_ids = model.generate(**batch, generation_config=generation_config,temperature=0.0,do_sample=False)
            generated_ids = [
                output_ids[len(input_ids):] for input_ids, output_ids in zip(batch.input_ids, generate_ids)
            ]
            output = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)
            # print(output)
            output,reason = extract_answer(output[0])
            # print(output)
            predictions.append(output)
            # print(predictions)
            # print(classes)
            eval_bar.update(1)
        end_time = time.time()
        elapsed_time = end_time - start_time
        tqdm.write(f"总时间:{elapsed_time}s,平均时间:{elapsed_time / len(eval_loader)}s")

        if self.config.unsloth:
            FastLanguageModel.for_training(model)
        model.config.use_cache = False

        eval_bar.close()
        metrics = self.weighted_average_accuracy(predictions, true_labels,classes)
        self.eval_times += 1
        if self.config.save_log:
            pass
        return metrics

    def _save(self, model, eval_rusult):
        current_time = datetime.now()
        formatted_time = current_time.strftime("%m-%d-%H-%M")

        file_name = formatted_time + "_eval_" + str(eval_rusult) + "-" + "p"
        output_dir = os.path.join(self.config.output_dir, file_name)
        print(output_dir)
        os.makedirs(output_dir, exist_ok=True)
        model.save_pretrained(
            output_dir, safe_serialization=False
        )
        tqdm.write(f"评估突破了阈值，lora权重保存至{output_dir}")

    def infer(self, model, batch_size=1,):
        def get_original_text(inputs) -> List[str]:
            inputs[inputs==-100]=self.tokenizer.pad_token_id
            return self.tokenizer.batch_decode(inputs, skip_special_tokens=True)
        print(os.environ['CUDA_VISIBLE_DEVICES'])
        data_test = load_dataset("json", data_files=DATA_TEST, keep_in_memory=True)["train"]
     


        accelerator = Accelerator()
        test_collate_fn = CustomCollateFn(mode="test")
        test_loader = torch.utils.data.DataLoader(dataset=data_test,
                                                  batch_size=batch_size,
                                                  collate_fn=test_collate_fn,
                                                  num_workers=4,
                                                  shuffle=False,
                                                  pin_memory=True,
                                                  drop_last=False)
        model, test_loader, eval_loader = accelerator.prepare(
            model, test_loader, self.eval_loader
        )
        # eval_rusult = self.evaluation(model, eval_loader)
        # tqdm.write(str(eval_rusult))

        torch.cuda.empty_cache()
        accelerator = Accelerator()
        model, test_loader = accelerator.prepare(
            model, test_loader
        )
        output_json = []
        if self.config.unsloth:
            FastLanguageModel.for_inference(model)
        model.eval()
        model.config.use_cache = True
        generation_config = GenerationConfig(
            do_sample=True,
            temperature=0.3,
            max_new_tokens=38912,
        )
        eval_bar = tqdm(colour="yellow", desc=f"Evaluation",
                        total=len(test_loader), dynamic_ncols=True)
        total = 0
        out = []
        for step, batch in enumerate(test_loader):
            eval_bar.update(1)
            id = batch.pop("id")
            house_id = batch.pop("house_id")
            id[id == -100] = self.tokenizer.pad_token_id
            house_id[house_id == -100] = self.tokenizer.pad_token_id
            ids = self.tokenizer.batch_decode(id, skip_special_tokens=True)
            house_ids = self.tokenizer.batch_decode(house_id, skip_special_tokens=True)
            with grad_mode.inference_mode():
                generate_ids = model.generate(**batch, generation_config=generation_config,temperature=0.5,do_sample=True)

            generated_ids = [
                output_ids[len(input_ids):] for input_ids, output_ids in zip(batch.input_ids, generate_ids)
            ]
            output = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)
            print(output[0])
            # output,reason = extract_answer(output[0])
            
            for data_id,house_id in  zip(ids,house_ids):
                submit_data = {
                    "id":data_id,
                    "house_id":house_id,
                    "output":output[0],
                }
                time = DT.date.today()
                out.append(submit_data)
            with open('output.json', 'w', encoding='utf-8') as f:
                json.dump(out, f, ensure_ascii=False, indent=4)
            torch.cuda.empty_cache()
            total += 1
            if total % 500 == 0:
                torch.cuda.empty_cache()
            
        eval_bar.close()

    def get_batch_samples(self, epoch_iterator, num_batches):
        batch_samples = []
        num_items_in_batch = None
        for _ in range(num_batches):
            try:
                batch_samples += [next(epoch_iterator)]
            except StopIteration:
                break

        if len(batch_samples) > 0 and "labels" in batch_samples[0]:
            try:
                num_items_in_batch = sum([(batch["labels"].ne(-100)).sum() for batch in batch_samples])
                # print(num_items_in_batch)
            except (TypeError, AttributeError):
                pass

        return batch_samples, num_items_in_batch

    def train(self):
        def get_original_text(inputs) -> List[str]:
            inputs[inputs==-100]=self.tokenizer.pad_token_id
            return self.tokenizer.batch_decode(inputs, skip_special_tokens=True)
        torch.cuda.empty_cache()

        
        accelerator = Accelerator()
        model, self.optimizer, train_loader, eval_loader = accelerator.prepare(
            self.model, self.optimizer, self.train_loader, self.eval_loader
        )

        if self.config.gradient_checkpointing:
           
            model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': True})

        if self.config.nef_tune:
            orig_embed = model.get_input_embeddings()
        total_batched_samples = 0
        total_length = len(train_loader) * self.config.epoch // self.config.gradient_accumulation_steps
        progress_bar = tqdm(colour="blue", desc=f"Training", total=total_length, dynamic_ncols=True)
        for epoch in range(self.config.epoch):
            total_loss = 0.0
            model.config.use_cache = False
            epoch_dataloader = train_loader
            epoch_iterator = iter(epoch_dataloader)
            remainder = len(train_loader.dataset) % self.config.gradient_accumulation_steps
            if remainder == 0:
                remainder = self.config.gradient_accumulation_steps
          
            update_step = -1
            total_updates = len(train_loader) // self.config.gradient_accumulation_steps + 1
            mini_step = 0
            for _ in range(total_updates):
                update_step += 1
                num_batches = self.config.gradient_accumulation_steps if update_step != (
                            total_updates - 1) else remainder
                batch_samples, num_items_in_batch = self.get_batch_samples(epoch_iterator, num_batches)
                for step, batch in enumerate(batch_samples):
                    mini_step += 1
                   
                    total_batched_samples += 1
                    model.train()
                    if self.config.nef_tune:
                        embed_init = orig_embed(batch.input_ids)
                        dims = torch.tensor(embed_init.size(1) * embed_init.size(2))
                        mag_norm = self.config.noise_alpha / torch.sqrt(dims)
                        batch['inputs_embeds'] = embed_init + torch.zeros_like(embed_init).uniform_(-mag_norm, mag_norm)
                        batch.pop('input_ids')

                    loss_kwargs={"num_items_in_batch": num_items_in_batch.item()}
                    batch = {**batch, **loss_kwargs}
                    # print(batch)
                    with torch.autocast("cuda", dtype=torch.bfloat16, enabled=self.config.bf16):
                        # print(model)
                        loss = model(**batch).loss
                        total_loss += loss.detach().item()
                        if self.config.save_log:
                            if total_batched_samples % 2 == 0:
                                self.writer.add_scalar('Loss/train', loss.detach().item(),
                                                       math.ceil(total_batched_samples / 2))
                    accelerator.backward(loss)
                    del batch
                    if total_batched_samples % self.config.gradient_accumulation_steps == 0:
                        # print(total_batched_samples)
                        accelerator.clip_grad_norm_(model.parameters(), self.config.max_grad_norm)
                        self.optimizer.step()
                        self.scheduler.step()
                        model.zero_grad()
                        progress_bar.update(1)

                    if total_batched_samples % (self.config.log_step * self.config.gradient_accumulation_steps) == 0:
                        log_loss = total_loss / self.config.log_step
                        total_loss -= total_loss
                        tqdm.write("%s loss；%f lr: %s, epoch: %f, step: %d" % (os.environ['CUDA_VISIBLE_DEVICES'],
                                                                               log_loss,
                                                                               format(self.scheduler.get_last_lr()[0],
                                                                                      'e'), epoch + mini_step / len(
                            epoch_dataloader), total_batched_samples // self.config.gradient_accumulation_steps))
                    if mini_step==len(epoch_dataloader)-1 and epoch<=6:
                        # eval_result = self.evaluation(model, eval_loader)
                        self._save(model,f"epoch{epoch+1}")
                    # 评估并保存检查点
                    # 可以通过设置total_batched_samples，训练超过一定步数后再开始评估，节约时间
                    # if total_batched_samples % (
                    #         self.config.eval_step * self.config.gradient_accumulation_steps) == 0 and total_batched_samples > 12000:
                    #     eval_result = self.evaluation(model, eval_loader)
                    #     tqdm.write("%s epoch: %f" % (
                    #         str(eval_result), epoch + mini_step / len(epoch_dataloader))
                    #                )
                    #     torch.cuda.empty_cache()
                    #     if  eval_result["score"]>= self.best_metric or eval_result["score"]>=0.70:
                    #         self.best_metric = eval_result["score"]
                    #         unwrap_model = accelerator.unwrap_model(model)
                    #         self._save(unwrap_model, eval_result)


from bitsandbytes.optim import AdamW8bit,PagedAdamW8bit


import traceback


try:
    model = getModel(config.lora_r, config.lora_alpha)

    optimizer = AdamW8bit(model.parameters(), lr=config.lr, weight_decay=config.weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, 3000, eta_min=0, last_epoch=-1)

    trainer = smart_design_Trainer(model=model,
                           optimizer=(optimizer, scheduler),
                           dataloader=getDataLoader(config.train_batch_size, config.eval_batch_size),
                           tokenizer=tokenizer,
                           config=config
                           )

    # trainer.infer(model)
    trainer.train()

    print("任务完成，即将关机...")
    
except Exception as e:
    # 记录错误信息到日志文件
    error_msg = f"程序执行出错: {str(e)}\n{traceback.format_exc()}"
    with open("error.log", "w") as f:
        f.write(error_msg)
    print("发生错误，已记录到 error.log，即将关机...")

finally:
    # 无论成功与否都执行关机
    time.sleep(2)  # 给一点时间显示消息
    os.system("shutdown now")


