from huggingface_hub import snapshot_download
import time

sql_lora_path = "lora/ckpt/08-04-11-29_eval_epoch3-p"

from vllm import LLM, SamplingParams
from vllm.lora.request import LoRARequest
from vllm import EngineArgs, LLMEngine, RequestOutput

llm = LLM(model="/root/autodl-tmp/models/qwen3_8b", enable_lora=True,max_lora_rank = 64)

sampling_params = SamplingParams(
    temperature=0,
    max_tokens=10000,
    stop=["[/assistant]"]
)


prompts = [
     """\n
---\n
\n
## **面向用户户型的设计方案JSON生成（JSON格式输出）任务说明书**\n
### **任务背景**：\n
假设你是一个家装领域的整屋设计专家，能够根据用户给出的户型JSON数据和具体要求来进行家装设计，在用户提供的户型数据的基础上为其添加家具数据，并生成回复。**所有响应需以JSON格式返回**\n
---\n
###用户输入说明###\n
1. 用户输入包含两部分：完整的户型JSON数据和具体需求。\n
2. 完整的户型JSON数据包括了户型、房间、门窗等基本信息。\n
3. 用户的具体要求将会指示你具体需要在哪个房间添加家具信息。\n
\n
#### **户型JSON数据字段说明**：\n
1. **`conversation_id`**：  \n
   - 必填参数，需与用户输入的`conversation_id`保持一致。 \n
   \n
1. **`wallHeight`**：  \n
   - 户型墙高。  \n
   \n
2. **`centerPos`**：  \n
   - 整个户型图的中心点的坐标。\n
   
3. **`totalArea`**：  \n
   - 户型总面积（该字段单位为平方米）。\n
   \n
4. **`windowList`**：  \n
   - 窗户信息列表，此后的5-11共7个字段均为此字段的子字段。\n
   \n
5. **`windowType`**：  \n
   - 窗户类型，此字段为窗户信息列表的子字段。\n
   \n
6. **`heightToFloor`**：  \n
   - 窗户的离地高度，此字段为窗户信息列表的子字段。\n
   \n
7. **`length`**：  \n
   - 窗户的长度，此字段为窗户信息列表的子字段，*请注意，其他物品的列表字段可能也包含此子字段，请注意辨别*。\n
   \n
8. **`width`**：  \n
   - 窗户的宽度，此字段为窗户信息列表的子字段，*请注意，其他物品的列表字段可能也包含此子字段，请注意辨别*。\n
   \n
9. **`height`**：  \n
   - 窗户的高度，此字段为窗户信息列表的子字段，*请注意，其他物品的列表字段可能也包含此子字段，请注意辨别*。\n
   \n
10. **`pos`**：  \n
   - 窗户的坐标，实际为窗户中心点的坐标，此字段为窗户信息列表的子字段，*请注意，其他物品的列表字段可能也包含此子字段，请注意辨别*。\n
   \n
11. **`direction`**：  \n
   - 窗户的摆放方向，此字段为窗户信息列表的子字段，*请注意，其他物品的列表字段可能也包含此子字段，请注意辨别*。\n
   \n
12. **`doorList`**：  \n
   - 门信息列表，此后的13-19共7个字段均为此字段的子字段。\n
   \n
13. **`doorType`**：  \n
   - 门类型，此字段为门信息列表的子字段。\n
   \n
14. **`heightToFloor`**：  \n
   - 门的离地高度，此字段为门信息列表的子字段。\n
   \n
15. **`length`**：  \n
   - 门的长度，此字段为门信息列表的子字段，*请注意，其他物品的列表字段可能也包含此子字段，请注意辨别*。\n
   \n
16. **`width`**：  \n
   - 门的宽度，此字段为门信息列表的子字段，*请注意，其他物品的列表字段可能也包含此子字段，请注意辨别*。\n
   \n
17. **`height`**：  \n
   - 门的高度，此字段为门信息列表的子字段，*请注意，其他物品的列表字段可能也包含此子字段，请注意辨别*。\n
   \n
18. **`pos`**：  \n
   - 门的坐标，实际为门中心点的坐标，此字段为窗户信息列表的子字段，*请注意，其他物品的列表字段可能也包含此子字段，请注意辨别*。\n
   \n
19. **`direction`**：  \n
   - 窗户的摆放方向，此字段为门信息列表的子字段，*请注意，其他物品的列表字段可能也包含此子字段，请注意辨别*。\n
\n
20. **`roomList`**：  \n
   - 房间信息列表，此后的21-26共6个字段均为此字段的子字段。\n
   \n
21. **`name`**：  \n
   - 房间的类型名字，此字段为房间信息列表的子字段。   \n
   \n
22. **`englishName`**：  \n
   - 房间的英文类型名字，此字段为房间信息列表的子字段。 \n
   \n
23. **`"modelInfos"`**：\n
    - 房间中包含的家具信息列表，此字段为房间信息列表的子字段。\n
24. **`points`**：  \n
   - 房间的几个角的点位坐标，此字段为房间信息列表的子字段。 \n
   \n
25. **`centerPos`**：  \n
   - 房间的中心点，此字段为房间信息列表的子字段。 \n
   \n

26. **`rectangles`**：  \n
   - 该房间下吊顶生成的区域大小，包含min和max两个子字段，此字段为房间信息列表的子字段。 \n
   \n

27. **`area`**：  \n
   - 房间的面积，此字段为房间信息列表的子字段，单位为平方米。 \n
   \n
28. **`outerPoints`**：  \n
   - 全屋的外墙点位坐标数组。   \n
   \n
29. **`yDList`**：  \n
   - 烟道的坐标数组。 \n
   \n
30. **`baseInfo`**：  \n
   - 房屋的基本信息。 \n
   \n
31. **`inside_area`**：  \n
   - 房屋的套内面积。  \n
   \n
---\n
\n
#### **家具JSON数据字段说明**：\n
1. **`iD`**：  \n
   - 家具的iD号。 \n
   \n
2. **`type`**：  \n
   - 家具的类型。 \n
   \n
3. **`box`** \n
   - 家具的包围盒大小，包含"min"和"max"属性，分表表示家具包围盒的最小xyz坐标和最大xyz坐标，在坐标轴上按照这六个坐标画六条线的相交区域即为家居的包围盒。
   \n
4. **`location`**：  \n
   - 家具的坐标，实际为该家具中心点的坐标，包含x,y和z三个子字段。 \n
   \n
5. **`rotator`**：  \n
   - 家具的旋转指数，此字段包含Pitch（围绕X轴旋转，也叫做俯仰角）,Yaw（围绕Y轴旋转，也叫偏航角）和Roll（围绕Z轴旋转，也叫翻滚角）三个子字段。\n
\n
6. **`scale`**：  \n
   - 家具的缩放指数。\n
   \n
---\n
### **模型逻辑推理步骤**：\n
**1.户型JSON分析**：\n
- 分析用户提供的完整户型JSON格式，重点关注以下内容：\n
    - 户型的整体布局，房间数量以及种类。\n
    - 每个房间各自的布局与大小\n
    
**2.用户指令分析**:\n
- 分析用户用户的具体指令，重点关注以下内容：\n
    - 提取用户的指令操作对象，如“厨房”，“主卧”等。\n
    - 提取用户的具体操作指令，如“整体设计”，“添加一张椅子”等。\n
    
**3.家具类型选择**:\n
- 根据用户的具体需求，选择对应的家具：\n
    - 如果用户的指令中明确指出了要添加的家具类型，如“添加一张床”，则直接从相关类型的家具中选择即可。\n
    - 如果用户的指令中没有明确指出家具类型，如“帮我整体设计一下厨房”，则需要根据用户的户型选取合适的家具。\n
    - 家具的具体类型请从给定的家具类型表FurnitureType中选择，禁止选择不在家具类型表中的家具\n
    
**4.家具JSON生成**:\n
- 根据用户的房间户型信息，计算家具的相关JSON数据：\n
    - 确保家具的包围盒大小与用户的户型JSON适配，禁止出现家具的大小超出房间范围、与房间其他物品产生冲突等“穿模”现象。\n
    - 适当调整scale、location、box等数据以使家具的包围盒满足上述条件。\n
    - 确保家具的包围盒大小与现实中的该类型家具大小相当。\n
    \n
**5.家具JSON插入**:\n
- 根据用户的指令操作对象，将生成的JSON数据添加到户型JSON数据中与之对应的房间子字段modelInfos中：\n
    - 如果用户的指令中明确指出了要添加的家具类型，如“添加一张床”，则直接生成对应的家具JSON即可。\n
    - 如果用户的指令中没有明确指出家具类型，如“帮我整体设计一下厨房”，则需要根据用户的户型选取合适的家具并生成JSON数据。\n
    
**6.最终JSON输出**:\n
- 根据先前的操作结果，输出JSON格式：\n
    - **请注意，你只需要输出用户指令操作对象所对应的部分JSON**，如用户的指令为“帮我整体设计一下厨房”，则只需要输出该房间的JSON数据。\n 
---\n
###模型输出格式要求###\n
1. 禁止在输出中添加任何 `json` 标记、代码块符号（如 ```）或额外说明文本\n
2. 只需要设计用户指令中所需求的房间家具即可，禁止在回复中添加任何别的房间的家具或JSON数据。\n
---\n
###特别注意###\n
1. JSON中的数据坐标以三维世界原点（0，0，0）作为三维原点，可能会在户型图以外的位置\n
2. 户型图JSON中各个点的三维坐标（X，Y，Z）单位为cm；\n
---\n
#### **模型输入输出示例**：\n
**用户输入**：
户型JSON:\n
{
	"wallHeight": 270,
	"centerPos": "X=1031.115 Y=773.336 Z=0.000",
	"totalArea": "94.00",
	"windowList": [
		{
			"windowType": "OT_Ground_Window",
			"heightToFloor": 10,
			"length": 630,
			"width": 24,
			"height": 230,
			"pos": "X=863.559 Y=1300.923 Z=0.000",
			"direction": "X=1.000 Y=0.000 Z=0.000"
		},
		{
			"windowType": "OT_Window",
			"heightToFloor": 90,
			"length": 87,
			"width": 24,
			"height": 150,
			"pos": "X=1579.325 Y=746.699 Z=0.000",
			"direction": "X=0.000 Y=1.000 Z=0.000"
		},
		{
			"windowType": "OT_Window",
			"heightToFloor": 90,
			"length": 87,
			"width": 24,
			"height": 150,
			"pos": "X=989.011 Y=336.831 Z=0.000",
			"direction": "X=1.000 Y=0.000 Z=0.000"
		},
		{
			"windowType": "OT_Window",
			"heightToFloor": 90,
			"length": 159,
			"width": 24,
			"height": 150,
			"pos": "X=1148.834 Y=335.112 Z=0.000",
			"direction": "X=1.000 Y=0.000 Z=0.000"
		},
		{
			"windowType": "OT_Window",
			"heightToFloor": 90,
			"length": 185,
			"width": 24,
			"height": 150,
			"pos": "X=1424.657 Y=247.468 Z=0.000",
			"direction": "X=1.000 Y=0.000 Z=0.000"
		},
		{
			"windowType": "OT_Window",
			"heightToFloor": 90,
			"length": 135,
			"width": 24,
			"height": 150,
			"pos": "X=805.129 Y=125.452 Z=0.000",
			"direction": "X=1.000 Y=0.000 Z=0.000"
		},
		{
			"windowType": "OT_RectBayWindow",
			"heightToFloor": 45,
			"length": 328.23828125,
			"width": 24,
			"height": 195,
			"pos": "X=1408.331 Y=1244.212 Z=0.000",
			"direction": "X=0.000 Y=-1.000 Z=0.000"
		}
	],
	"doorList": [
		{
			"heightToFloor": 0,
			"length": 79,
			"width": 50,
			"height": 220,
			"pos": "X=984.506 Y=613.546 Z=0.000",
			"direction": "X=0.000 Y=-1.000 Z=0.000"
		},
		{
			"heightToFloor": 0,
			"length": 59,
			"width": 50,
			"height": 220,
			"pos": "X=1426.341 Y=822.619 Z=0.000",
			"direction": "X=1.000 Y=0.000 Z=0.000"
		},
		{
			"heightToFloor": 0,
			"length": 84,
			"width": 50,
			"height": 220,
			"pos": "X=1343.027 Y=618.679 Z=0.000",
			"direction": "X=0.000 Y=-1.000 Z=0.000"
		},
		{
			"heightToFloor": 0,
			"length": 89,
			"width": 50,
			"height": 220,
			"pos": "X=1111.695 Y=622.112 Z=0.000",
			"direction": "X=0.000 Y=-1.000 Z=0.000"
		},
		{
			"heightToFloor": 0,
			"length": 79,
			"width": 50,
			"height": 220,
			"pos": "X=969.699 Y=780.187 Z=0.000",
			"direction": "X=0.000 Y=1.000 Z=0.000"
		},
		{
			"heightToFloor": 0,
			"length": 79,
			"width": 50,
			"height": 220,
			"pos": "X=1331.763 Y=781.896 Z=0.000",
			"direction": "X=0.000 Y=1.000 Z=0.000"
		},
		{
			"heightToFloor": 0,
			"length": 114,
			"width": 50,
			"height": 210,
			"pos": "X=589.047 Y=316.224 Z=0.000",
			"direction": "X=0.000 Y=-1.000 Z=0.000"
		},
		{
			"heightToFloor": 0,
			"length": 230,
			"width": 50,
			"height": 220,
			"pos": "X=712.329 Y=1141.101 Z=0.000",
			"direction": "X=0.000 Y=1.000 Z=0.000"
		},
		{
			"heightToFloor": 0,
			"length": 150,
			"width": 50,
			"height": 220,
			"pos": "X=769.040 Y=390.105 Z=0.000",
			"direction": "X=0.000 Y=1.000 Z=0.000"
		},
		{
			"heightToFloor": 0,
			"length": 200,
			"width": 50,
			"height": 220,
			"pos": "X=1052.597 Y=1141.101 Z=0.000",
			"direction": "X=0.000 Y=1.000 Z=0.000"
		}
	],
	"roomList": [
		{
			"name": "阳台",
			"englishName": "Balcony",
			"points": [
				"X=529.306 Y=1170.316 Z=0.000",
				"X=1197.812 Y=1170.316 Z=0.000",
				"X=1197.812 Y=1297.486 Z=0.000",
				"X=529.306 Y=1297.486 Z=0.000"
			],
			"rectangles": [],
			"windowList": [
				{
					"windowType": "",
					"heightToFloor": 10,
					"length": 630,
					"width": 22.341064453125,
					"height": 230,
					"pos": "X=863.559 Y=1297.486 Z=10.000",
					"direction": "X=-1.000 Y=0.000 Z=0.000"
				}
			],
			"doorList": [
				{
					"heightToFloor": 0,
					"length": 230,
					"width": 36.0889892578125,
					"height": 220,
					"pos": "X=712.329 Y=1170.316 Z=0.000",
					"direction": "X=1.000 Y=0.000 Z=0.000"
				},
				{
					"heightToFloor": 0,
					"length": 200,
					"width": 36.0889892578125,
					"height": 220,
					"pos": "X=1052.597 Y=1170.316 Z=0.000",
					"direction": "X=1.000 Y=0.000 Z=0.000"
				}
			],
			"modelInfos": [],
			"views": [],
			"area": 8.5
		},
		{
			"name": "主卧",
			"englishName": "MasterBedroom",
			"points": [
				"X=1228.745 Y=783.647 Z=0.000",
				"X=1393.724 Y=783.647 Z=0.000",
				"X=1393.724 Y=890.196 Z=0.000",
				"X=1575.887 Y=890.196 Z=0.000",
				"X=1575.887 Y=1221.871 Z=0.000",
				"X=1228.745 Y=1221.871 Z=0.000"
			],
			"rectangles": [],
			"windowList": [
				{
					"windowType": "",
					"heightToFloor": 45,
					"length": 328.23828125,
					"width": 22.341064453125,
					"height": 195,
					"pos": "X=1408.331 Y=1221.871 Z=45.000",
					"direction": "X=-1.000 Y=0.000 Z=0.000"
				}
			],
			"doorList": [
				{
					"heightToFloor": 0,
					"length": 79,
					"width": 18.9029541015625,
					"height": 220,
					"pos": "X=1331.763 Y=783.647 Z=0.000",
					"direction": "X=1.000 Y=0.000 Z=0.000"
				},
				{
					"heightToFloor": 0,
					"length": 59,
					"width": 34.3699951171875,
					"height": 220,
					"pos": "X=1393.724 Y=822.619 Z=0.000",
					"direction": "X=0.000 Y=1.000 Z=0.000"
				}
			],
			"modelInfos": [],
			"views": [],
			"area": 13.270000457763672
		},
		{
			"name": "次卧",
			"englishName": "SecondBedroom",
			"points": [
				"X=919.411 Y=781.929 Z=0.000",
				"X=1197.812 Y=781.929 Z=0.000",
				"X=1197.812 Y=1134.227 Z=0.000",
				"X=919.411 Y=1134.227 Z=0.000"
			],
			"rectangles": [],
			"windowList": [],
			"doorList": [
				{
					"heightToFloor": 0,
					"length": 79,
					"width": 17.18499755859375,
					"height": 220,
					"pos": "X=969.699 Y=781.929 Z=0.000",
					"direction": "X=1.000 Y=0.000 Z=0.000"
				},
				{
					"heightToFloor": 0,
					"length": 200,
					"width": 36.0889892578125,
					"height": 220,
					"pos": "X=1052.597 Y=1134.227 Z=0.000",
					"direction": "X=-1.000 Y=0.000 Z=0.000"
				}
			],
			"modelInfos": [],
			"views": [],
			"area": 9.8100004196166992
		},
		{
			"name": "卫生间",
			"englishName": "Bathroom",
			"points": [
				"X=1428.094 Y=604.921 Z=0.000",
				"X=1575.887 Y=604.921 Z=0.000",
				"X=1575.887 Y=860.981 Z=0.000",
				"X=1428.094 Y=860.981 Z=0.000"
			],
			"rectangles": [],
			"windowList": [
				{
					"windowType": "",
					"heightToFloor": 90,
					"length": 87,
					"width": 22.341064453125,
					"height": 150,
					"pos": "X=1575.887 Y=746.699 Z=90.000",
					"direction": "X=0.000 Y=1.000 Z=0.000"
				}
			],
			"doorList": [
				{
					"heightToFloor": 0,
					"length": 59,
					"width": 34.3699951171875,
					"height": 220,
					"pos": "X=1428.094 Y=822.619 Z=0.000",
					"direction": "X=0.000 Y=-1.000 Z=0.000"
				}
			],
			"modelInfos": [],
			"views": [],
			"area": 3.7799999713897705
		},
		{
			"name": "卫生间2",
			"englishName": "Bathroom2",
			"points": [
				"X=876.448 Y=340.268 Z=0.000",
				"X=1037.989 Y=340.268 Z=0.000",
				"X=1037.989 Y=611.795 Z=0.000",
				"X=876.448 Y=611.795 Z=0.000"
			],
			"rectangles": [],
			"windowList": [
				{
					"windowType": "",
					"heightToFloor": 90,
					"length": 87,
					"width": 24.058990478515625,
					"height": 150,
					"pos": "X=989.011 Y=340.268 Z=90.000",
					"direction": "X=1.000 Y=0.000 Z=0.000"
				}
			],
			"doorList": [
				{
					"heightToFloor": 0,
					"length": 79,
					"width": 27.49603271484375,
					"height": 220,
					"pos": "X=984.506 Y=611.795 Z=0.000",
					"direction": "X=-1.000 Y=0.000 Z=0.000"
				}
			],
			"modelInfos": [],
			"views": [],
			"area": 4.3899998664855957
		},
		{
			"name": "书房",
			"englishName": "Study",
			"points": [
				"X=1056.893 Y=338.549 Z=0.000",
				"X=1271.709 Y=338.549 Z=0.000",
				"X=1271.709 Y=620.388 Z=0.000",
				"X=1056.893 Y=620.388 Z=0.000"
			],
			"rectangles": [],
			"windowList": [
				{
					"windowType": "",
					"heightToFloor": 90,
					"length": 159,
					"width": 24.05902099609375,
					"height": 150,
					"pos": "X=1148.834 Y=338.549 Z=90.000",
					"direction": "X=1.000 Y=0.000 Z=0.000"
				}
			],
			"doorList": [
				{
					"heightToFloor": 0,
					"length": 89,
					"width": 18.90301513671875,
					"height": 220,
					"pos": "X=1111.695 Y=620.388 Z=0.000",
					"direction": "X=-1.000 Y=0.000 Z=0.000"
				}
			],
			"modelInfos": [],
			"views": [],
			"area": 6.0500001907348633
		},
		{
			"name": "客餐厅",
			"englishName": "LivingRoom",
			"points": [
				"X=488.061 Y=314.490 Z=0.000",
				"X=654.758 Y=314.490 Z=0.000",
				"X=654.758 Y=417.602 Z=0.000",
				"X=845.514 Y=417.602 Z=0.000",
				"X=845.514 Y=639.291 Z=0.000",
				"X=1395.442 Y=639.291 Z=0.000",
				"X=1395.442 Y=764.744 Z=0.000",
				"X=888.477 Y=764.744 Z=0.000",
				"X=888.477 Y=1134.227 Z=0.000",
				"X=529.306 Y=1134.227 Z=0.000",
				"X=529.306 Y=476.031 Z=0.000",
				"X=488.061 Y=476.031 Z=0.000"
			],
			"rectangles": [],
			"windowList": [],
			"doorList": [
				{
					"heightToFloor": 0,
					"length": 114,
					"width": 24.058990478515625,
					"height": 210,
					"pos": "X=589.047 Y=314.490 Z=0.000",
					"direction": "X=1.000 Y=0.000 Z=0.000"
				},
				{
					"heightToFloor": 0,
					"length": 150,
					"width": 34.371002197265625,
					"height": 220,
					"pos": "X=769.040 Y=417.602 Z=0.000",
					"direction": "X=1.000 Y=0.000 Z=0.000"
				},
				{
					"heightToFloor": 0,
					"length": 79,
					"width": 27.49603271484375,
					"height": 220,
					"pos": "X=984.506 Y=639.291 Z=0.000",
					"direction": "X=1.000 Y=0.000 Z=0.000"
				},
				{
					"heightToFloor": 0,
					"length": 89,
					"width": 18.90301513671875,
					"height": 220,
					"pos": "X=1111.695 Y=639.291 Z=0.000",
					"direction": "X=1.000 Y=0.000 Z=0.000"
				},
				{
					"heightToFloor": 0,
					"length": 84,
					"width": 22.34002685546875,
					"height": 220,
					"pos": "X=1343.027 Y=639.291 Z=0.000",
					"direction": "X=1.000 Y=0.000 Z=0.000"
				},
				{
					"heightToFloor": 0,
					"length": 79,
					"width": 18.9029541015625,
					"height": 220,
					"pos": "X=1331.763 Y=764.744 Z=0.000",
					"direction": "X=-1.000 Y=0.000 Z=0.000"
				},
				{
					"heightToFloor": 0,
					"length": 79,
					"width": 17.18499755859375,
					"height": 220,
					"pos": "X=969.699 Y=764.744 Z=0.000",
					"direction": "X=-1.000 Y=0.000 Z=0.000"
				},
				{
					"heightToFloor": 0,
					"length": 230,
					"width": 36.0889892578125,
					"height": 220,
					"pos": "X=712.329 Y=1134.227 Z=0.000",
					"direction": "X=-1.000 Y=0.000 Z=0.000"
				}
			],
			"modelInfos": [],
			"views": [],
			"area": 33.110000610351562
		},
		{
			"name": "次卧2",
			"englishName": "SecondBedroom2",
			"points": [
				"X=1290.612 Y=250.905 Z=0.000",
				"X=1575.887 Y=250.905 Z=0.000",
				"X=1575.887 Y=575.706 Z=0.000",
				"X=1395.442 Y=575.706 Z=0.000",
				"X=1395.442 Y=616.951 Z=0.000",
				"X=1290.612 Y=616.951 Z=0.000"
			],
			"rectangles": [],
			"windowList": [
				{
					"windowType": "",
					"heightToFloor": 90,
					"length": 185,
					"width": 24.05999755859375,
					"height": 150,
					"pos": "X=1424.657 Y=250.905 Z=90.000",
					"direction": "X=1.000 Y=0.000 Z=0.000"
				}
			],
			"doorList": [
				{
					"heightToFloor": 0,
					"length": 84,
					"width": 22.34002685546875,
					"height": 220,
					"pos": "X=1343.027 Y=616.951 Z=0.000",
					"direction": "X=-1.000 Y=0.000 Z=0.000"
				}
			],
			"modelInfos": [],
			"views": [],
			"area": 9.6999998092651367
		},
		{
			"name": "厨房",
			"englishName": "Kitchen",
			"points": [
				"X=687.410 Y=128.889 Z=0.000",
				"X=921.129 Y=128.889 Z=0.000",
				"X=921.129 Y=307.616 Z=0.000",
				"X=847.233 Y=307.616 Z=0.000",
				"X=847.233 Y=383.231 Z=0.000",
				"X=687.410 Y=383.231 Z=0.000"
			],
			"rectangles": [],
			"windowList": [
				{
					"windowType": "",
					"heightToFloor": 90,
					"length": 135,
					"width": 24.059005737304688,
					"height": 150,
					"pos": "X=805.129 Y=128.889 Z=90.000",
					"direction": "X=1.000 Y=0.000 Z=0.000"
				}
			],
			"doorList": [
				{
					"heightToFloor": 0,
					"length": 150,
					"width": 34.371002197265625,
					"height": 220,
					"pos": "X=769.040 Y=383.231 Z=0.000",
					"direction": "X=-1.000 Y=0.000 Z=0.000"
				}
			],
			"modelInfos": [],
			"views": [],
			"area": 5.3899998664855957
		}
	],
	"outerPoints": [
		"X=1598.228 Y=580.861 Z=0.000",
		"X=1598.228 Y=226.845 Z=0.000",
		"X=1266.553 Y=226.845 Z=0.000",
		"X=1266.553 Y=314.490 Z=0.000",
		"X=1032.834 Y=314.490 Z=0.000",
		"X=1032.834 Y=316.209 Z=0.000",
		"X=943.470 Y=316.209 Z=0.000",
		"X=943.470 Y=104.830 Z=0.000",
		"X=663.351 Y=104.830 Z=0.000",
		"X=663.351 Y=290.431 Z=0.000",
		"X=464.002 Y=290.431 Z=0.000",
		"X=464.002 Y=498.372 Z=0.000",
		"X=505.246 Y=498.372 Z=0.000",
		"X=505.246 Y=1146.256 Z=0.000",
		"X=505.246 Y=1156.567 Z=0.000",
		"X=505.246 Y=1319.827 Z=0.000",
		"X=1220.153 Y=1319.827 Z=0.000",
		"X=1220.153 Y=1244.212 Z=0.000",
		"X=1598.228 Y=1244.212 Z=0.000",
		"X=1598.228 Y=883.322 Z=0.000",
		"X=1598.228 Y=866.137 Z=0.000",
		"X=1598.228 Y=598.047 Z=0.000",
		"X=1598.228 Y=580.861 Z=0.000"
	],
	"yDList": [],
	"baseInfo":
	{
		"inside_area": 105.978271484375
	}
}
用户需求指令：\n
帮我整体设计一下阳台。\n

**模型输出**：
{
			"name": "阳台",
			"englishName": "Balcony",
			"points": [
				"X=529.306 Y=1170.316 Z=0.000",
				"X=1197.812 Y=1170.316 Z=0.000",
				"X=1197.812 Y=1297.486 Z=0.000",
				"X=529.306 Y=1297.486 Z=0.000"
			],
			"rectangles": [
				{
					"min":
					{
						"x": 537,
						"y": 1178,
						"z": 0
					},
					"max":
					{
						"x": 1167,
						"y": 1288,
						"z": 0
					},
					"isValid": true
				}
			],
			"windowList": [
				{
					"windowType": "",
					"heightToFloor": 10,
					"length": 630,
					"width": 22.341064453125,
					"height": 230,
					"pos": "X=863.559 Y=1297.486 Z=10.000",
					"direction": "X=-1.000 Y=0.000 Z=0.000"
				}
			],
			"doorList": [
				{
					"heightToFloor": 0,
					"length": 230,
					"width": 36.0889892578125,
					"height": 220,
					"pos": "X=712.329 Y=1170.316 Z=0.000",
					"direction": "X=1.000 Y=0.000 Z=0.000"
				},
				{
					"heightToFloor": 0,
					"length": 200,
					"width": 36.0889892578125,
					"height": 220,
					"pos": "X=1052.597 Y=1170.316 Z=0.000",
					"direction": "X=1.000 Y=0.000 Z=0.000"
				}
			],
			"modelInfos": [
				{
					"iD": "22706",
					"type": "BalconyCabinets",
					"box":
					{
						"min":
						{
							"x": 1137.8120803833008,
							"y": 1170.3160701818329,
							"z": -1.0001373291015625
						},
						"max":
						{
							"x": 1197.8120269775391,
							"y": 1297.485996453282,
							"z": 238.99986267089844
						},
						"isValid": true
					},
					"location":
					{
						"x": 1167.8120384216309,
						"y": 1233.9010009765625,
						"z": -1
					},
					"rotator":
					{
						"pitch": 0,
						"yaw": 89.999999999999986,
						"roll": -0
					},
					"scale":
					{
						"x": 1.0597497224807739,
						"y": 1,
						"z": 1
					}
				},
				{
					"iD": "4506",
					"type": "DownLightd",
					"box":
					{
						"min":
						{
							"x": 858.55902099609375,
							"y": 1228.9010009765625,
							"z": 239.45158714056015
						},
						"max":
						{
							"x": 868.55902099609375,
							"y": 1238.9010009765625,
							"z": 240.50000077486038
						},
						"isValid": true
					},
					"location":
					{
						"x": 863.55902099609375,
						"y": 1233.9010009765625,
						"z": 240
					},
					"rotator":
					{
						"pitch": 0,
						"yaw": 0,
						"roll": 0
					},
					"scale":
					{
						"x": 1,
						"y": 1,
						"z": 1
					}
				},
				{
					"iD": "4506",
					"type": "DownLightd",
					"box":
					{
						"min":
						{
							"x": 1102.8120651245117,
							"y": 1228.9010009765625,
							"z": 239.45158714056015
						},
						"max":
						{
							"x": 1112.8120651245117,
							"y": 1238.9010009765625,
							"z": 240.50000077486038
						},
						"isValid": true
					},
					"location":
					{
						"x": 1107.8120651245117,
						"y": 1233.9010009765625,
						"z": 240
					},
					"rotator":
					{
						"pitch": 0,
						"yaw": 0,
						"roll": 0
					},
					"scale":
					{
						"x": 1,
						"y": 1,
						"z": 1
					}
				},
				{
					"iD": "4506",
					"type": "DownLightd",
					"box":
					{
						"min":
						{
							"x": 554.3060302734375,
							"y": 1228.9010009765625,
							"z": 239.45158714056015
						},
						"max":
						{
							"x": 564.3060302734375,
							"y": 1238.9010009765625,
							"z": 240.50000077486038
						},
						"isValid": true
					},
					"location":
					{
						"x": 559.3060302734375,
						"y": 1233.9010009765625,
						"z": 240
					},
					"rotator":
					{
						"pitch": 0,
						"yaw": 0,
						"roll": 0
					},
					"scale":
					{
						"x": 1,
						"y": 1,
						"z": 1
					}
				}
			],
			"area": 8.5
		}
---\n

### **家具类型表FurnitureType**
{
	Lamp                 //灯

	SingleBed 			 //单人床
	DoubleBed		 //双人床
	Bed,				 //床
	Armoire 			 //衣柜

	Cabinets		 //柜

	ShoeCabinets

	Sofa				 //沙发
	MultiSofa				 //多人沙发
	TurnSofa

	BedsideTable        //床头柜
	DressingTable       //梳妆台
	DecorativeCabinets	//装饰柜

	HalfTVCabinets   //电视柜（小）
	TVCabinets      //电视柜	

	LiquorCabinets 	//酒柜

	HighCabinets //装饰高柜

	ProjectionScreen //投影幕布

	FrontDoor //玄关柜

	WaterChannel  //水槽

	CookingPench  //灶台
	IceBoxCabinet   //冰箱柜

	WritingDesk  //书桌
	Desk  //桌子

	DeskWall // 壁挂式桌子

	Chair  //椅
	SingleSofa //单人沙发

	LoungeChair /沙发椅
	Deckchair 		 //躺椅、休闲椅

	StoolsChair     //凳子


	BookCabinet //书柜
	BookCase//书架
	Floor 				 //地板

	Dresserplus // 带柜梳妆桌
	Dresser //梳妆台
	DresserChair //梳妆椅

	TeaTable //茶几
	ChineseChair //中式椅子

	CoffeeTable //茶几组合
	SquareTable //圆茶几
	RoundTable //方茶几
	SideTable //边几
	FloorLamp //落地灯

	Statue //雕像
	Japanese DeckChair //日式休闲椅
	 
	RoomTVCabinets //电视柜

	RootCabinet //书房柜

	StudyDesk // 书房桌子
	RootChair // 书房椅子

	Playtool // 玩具
	Greenery  // 桌面绿植
	Book // 书
	KitchenetteCutlery //餐具

	//餐厅
	CircularTable //圆餐桌
	DiningTable //方餐桌
	DiningChair //方餐桌椅
	IslandTable 	//连体岛台
	SingleIslandTable 	//独立岛台

	Curtain           //窗帘
	ClothCurtain  //布窗帘
	DreamCurtain 	//梦幻帘
	GauzeCurtain 	//纱帘
	RollerShutter // 卷帘
	ShangriCurtain  //香格里拉帘

	OrbitalLight //轨道灯

	BackWall0 //普通背景墙
	BackWall1  //客厅不带电视的背景墙
	BackCabinet1 //客厅带电视的背景墙
	BackCabinet2  //客厅沙发背柜
	BackWall2 //客厅沙发背景墙
	BackWall3 	//餐厅背景墙
	SofaBackWall ,//沙发背景墙
	BedBackWall ,//

	Ceiling Ceiling"),
	FloorMaterial FloorMaterial"),
	CeilingMaterial CeilingMaterial"),
	WallMaterial WallMaterial"),
	ThresholdMaterial  ThresholdMaterial"),

	// 厨房
	Cupboard Cupboard"),//高冰箱单柜
	CnormalA CnormalA"),//吊柜普通A
	CnormalB CnormalB"),//吊柜普通B
	CnormalC CnormalC"),//吊柜普通C
	CnormalSole CnormalSole"),//吊柜单独
	Crangehoods Crangehoods"),//吊柜油烟机

	FNormalA FNormalA"),//地柜普通A
	FNormalB FNormalB"),//地柜普通B
	FNormalC FNormalC"),//地柜普通C
	FNormalSole FNormalSole"),//地柜单独
	FStove FStove"),//地柜灶台

	HFreezerSole HFreezerSole"),//高冰箱单柜
	HFreezerTwo HFreezerTwo"),//高冰箱双柜

	FWashbasin FWashbasin"),//地柜水池
	HElectric HElectric"),//高电器烤箱柜
	

	//卫生间
	WashbasinCabinetsA WashbasinCabinetsA"),//洗脸池
	WashbasinCabinetsB BathRoomWashbasinCabinetsB"),
	WashbasinCabinetsC WashbasinCabinetsC"),//洗脸池
	WashbasinCabinetsD BathRoomWashbasinCabinetsD"),
	Toilets Toilets"),//马桶
	NToilets NToilets"),
	RootToilet RootToilet"),

	Sprinkler Sprinkler"),
	Nsprinkler Nsprinkler"),
	ShowerRooms ShowerRooms"),//淋浴间
	ShortShowerRooms ShowerRooms"),
	LongShowerRooms ShowerRooms"),
	NshowerRooms NshowerRooms"),
	BathMirror BathMirror"),
	BathTub BathTub"),//浴缸
	Niche Niche"), // 壁龛
	DownLightd DownLightd"),		//筒灯

	BalconyCabinets BalconyCabinets"),	//阳台柜
	DecorateCabinets DecorateCabinets"),
	PetRoom PetRoom"),	//宠物屋
	PetFrame PetFrame"), //宠物爬架
	Sports Sports"), //健身器材
		
	SkirtingLine SkirtingLine"),
	ChildrenDoor ChildrenDoor"),
	Door Door"),
	InapparentDoor InapparentDoor"),
	Window Window"),
	MoveDoor MoveDoor"),
	BayWindow BayWindow"),
	FrenchWindow FrenchWindow"),
	StoneLacquer StoneLacquer"),
	DoorPocket DoorPocket"),

	Rug Rug"),				 //地毯
	BedUpLight BedUpLight"),			 //床头灯
	WallLamp WallLamp"),				//壁灯

	BedChair BedChair"),	//床尾凳
	TV TV"),					 //电视

	Paintings Paintings"),
	Painting Painting"),
	PhotoWall PhotoWall"),		//照片墙
	Pendant Pendant"),		//挂件

	MainLight MainLight"),        //主灯
	CeilingLight CeilingLight"),                //吸顶灯
	NoFurnitureType NoFurnitureType")
};

```\n

```
""",
]


def initialize_engine() -> LLMEngine:
    """Initialize the LLMEngine."""
    # max_loras:控制可以在同一批中使用的 LoRA 的数量。
    # 较大的值将导致更高的内存使用情况
    # 因为每个 LoRA 插槽需要其自己的前置张量。
    # max_lora_rank:控制所有 LoRA 的最大支持 rank 。
    # 更大的值将导致更高的内存使用。如果您知道所有 LoRA 都会
    # 使用相同的 rank ，建议将其设置为尽可能低。
    # max_cpu_loras:控制 CPU LORA 缓存的大小。
    engine_args = EngineArgs(model="/root/autodl-tmp/models/qwen3_8b",
                             enable_lora=True,
                             max_loras=1,
                             max_lora_rank=8,
                             max_cpu_loras=2,
                             max_num_seqs=256)
    return LLMEngine.from_engine_args(engine_args)
# engine = initialize_engine()
print(f"实验开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
start_time = time.time()
outputs = llm.generate(
    prompts,
    sampling_params,
    lora_request=LoRARequest("sql_adapter", 1, sql_lora_path)
)
# engine.add_request(0,
#             prompts,
#             sampling_params,
#             lora_request = LoRARequest("sql_adapter", 1, sql_lora_path))
#             # request_id += 1

# request_outputs: list[RequestOutput] = engine.step()

# for request_output in request_outputs:
#     if request_output.finished:
#         print(request_output)
end_time = time.time()
log_file.write(f"响应时间: {end_time - start_time:.2f}秒\n")