
from transformers import AutoModelForCausalLM, AutoTokenizer

model_path = "/root/autodl-tmp/models/qwen3_32b"  # 本地模型路径
# model_path = "Qwen/Qwen3-30B-A3B-Thinking-2507"

tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    torch_dtype="auto",
    device_map="auto"
)

prompt = "Give me a short introduction to large language model.Please reason step by step./no_think"
prompt = "给我用一段话介绍一下LLM和LMM"

# enable_thinking=False 时，软切换无效
# user_input_1 = "How many r's in strawberries?"
# user_input_2 = "Then, how many r's in blueberries? /no_think"
# user_input_3 = "Really? /think"

messages = [{"role": "user", "content": prompt}]

text = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True,
    enable_thinking=True  # 默认启用思维模式 # !2507版本中注释该行
)
model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

generated_ids = model.generate(**model_inputs, max_new_tokens=32768)
output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist()

try:
    index = len(output_ids) - output_ids[::-1].index(151668)  # 查找 </think>
except ValueError:
    index = 0

thinking_content = tokenizer.decode(output_ids[:index], skip_special_tokens=True).strip("\n")
content = tokenizer.decode(output_ids[index:], skip_special_tokens=True).strip("\n")

print("thinking content:", thinking_content)
print("content:", content)




