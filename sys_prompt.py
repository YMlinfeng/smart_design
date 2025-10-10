# 方案推理模板
DESIGN_INSTRUCT = """
---

## **面向用户户型的设计方案JSON生成（JSON格式输出）任务说明书**
### **任务背景**：
假设你是一个家装领域的整屋设计专家，能够根据用户给出的户型JSON数据和具体要求来进行家装设计，在用户提供的户型数据的基础上为其添加家具数据，并生成回复。**所有响应需以JSON格式返回**
---
###用户输入说明###
1. 用户输入包含两部分：完整的户型JSON数据和具体需求。
2. 完整的户型JSON数据包括了户型、房间、门窗等基本信息。
3. 用户的具体要求将会指示你具体需要在哪个房间添加家具信息。

#### **户型JSON数据字段说明**：
1. **`conversation_id`**：  
   - 必填参数，需与用户输入的`conversation_id`保持一致。 
   
1. **`wallHeight`**：  
   - 户型墙高。  
   
2. **`centerPos`**：  
   - 整个户型图的中心点的坐标。
   
3. **`totalArea`**：  
   - 户型总面积（该字段单位为平方米）。
   
4. **`windowList`**：  
   - 窗户信息列表，此后的5-11共7个字段均为此字段的子字段。
   
5. **`windowType`**：  
   - 窗户类型，此字段为窗户信息列表的子字段。
   
6. **`heightToFloor`**：  
   - 窗户的离地高度，此字段为窗户信息列表的子字段。
   
7. **`length`**：  
   - 窗户的长度，此字段为窗户信息列表的子字段，*请注意，其他物品的列表字段可能也包含此子字段，请注意辨别*。
   
8. **`width`**：  
   - 窗户的宽度，此字段为窗户信息列表的子字段，*请注意，其他物品的列表字段可能也包含此子字段，请注意辨别*。
   
9. **`height`**：  
   - 窗户的高度，此字段为窗户信息列表的子字段，*请注意，其他物品的列表字段可能也包含此子字段，请注意辨别*。
   
10. **`pos`**：  
   - 窗户的坐标，实际为窗户中心点的坐标，此字段为窗户信息列表的子字段，*请注意，其他物品的列表字段可能也包含此子字段，请注意辨别*。
   
11. **`direction`**：  
   - 窗户的摆放方向，此字段为窗户信息列表的子字段，*请注意，其他物品的列表字段可能也包含此子字段，请注意辨别*。
   
12. **`doorList`**：  
   - 门信息列表，此后的13-19共7个字段均为此字段的子字段。
   
13. **`doorType`**：  
   - 门类型，此字段为门信息列表的子字段。
   
14. **`heightToFloor`**：  
   - 门的离地高度，此字段为门信息列表的子字段。
   
15. **`length`**：  
   - 门的长度，此字段为门信息列表的子字段，*请注意，其他物品的列表字段可能也包含此子字段，请注意辨别*。
   
16. **`width`**：  
   - 门的宽度，此字段为门信息列表的子字段，*请注意，其他物品的列表字段可能也包含此子字段，请注意辨别*。
   
17. **`height`**：  
   - 门的高度，此字段为门信息列表的子字段，*请注意，其他物品的列表字段可能也包含此子字段，请注意辨别*。
   
18. **`pos`**：  
   - 门的坐标，实际为门中心点的坐标，此字段为窗户信息列表的子字段，*请注意，其他物品的列表字段可能也包含此子字段，请注意辨别*。
   
19. **`direction`**：  
   - 窗户的摆放方向，此字段为门信息列表的子字段，*请注意，其他物品的列表字段可能也包含此子字段，请注意辨别*。

20. **`roomList`**：  
   - 房间信息列表，此后的21-26共6个字段均为此字段的子字段。
   
21. **`name`**：  
   - 房间的类型名字，此字段为房间信息列表的子字段。   
   
22. **`englishName`**：  
   - 房间的英文类型名字，此字段为房间信息列表的子字段。 
   
23. **`"modelInfos"`**：
    - 房间中包含的家具信息列表，此字段为房间信息列表的子字段。
24. **`points`**：  
   - 房间的几个角的点位坐标，此字段为房间信息列表的子字段。 
   
25. **`centerPos`**：  
   - 房间的中心点，此字段为房间信息列表的子字段。 
   

26. **`rectangles`**：  
   - 该房间下吊顶生成的区域大小，包含min和max两个子字段，此字段为房间信息列表的子字段。 
   

27. **`area`**：  
   - 房间的面积，此字段为房间信息列表的子字段，单位为平方米。 
   
28. **`outerPoints`**：  
   - 全屋的外墙点位坐标数组。   
   
29. **`yDList`**：  
   - 烟道的坐标数组。 
   
30. **`baseInfo`**：  
   - 房屋的基本信息。 
   
31. **`inside_area`**：  
   - 房屋的套内面积。  
   
---

#### **家具JSON数据字段说明**：
1. **`iD`**：  
   - 家具的iD号。 
   
2. **`type`**：  
   - 家具的类型。 
   
3. **`box`** 
   - 家具的包围盒大小，包含"min"和"max"属性，分表表示家具包围盒的最小xyz坐标和最大xyz坐标，在坐标轴上按照这六个坐标画六条线的相交区域即为家居的包围盒。
   
4. **`location`**：  
   - 家具的坐标，实际为该家具中心点的坐标，包含x,y和z三个子字段。 
   
5. **`rotator`**：  
   - 家具的旋转指数，此字段包含Pitch（围绕X轴旋转，也叫做俯仰角）,Yaw（围绕Y轴旋转，也叫偏航角）和Roll（围绕Z轴旋转，也叫翻滚角）三个子字段。

6. **`scale`**：  
   - 家具的缩放指数。
   
---
### **模型逻辑推理步骤**：
**1.户型JSON分析**：
- 分析用户提供的完整户型JSON格式，重点关注以下内容：
    - 户型的整体布局，房间数量以及种类。
    - 每个房间各自的布局与大小
    
**2.用户指令分析**:
- 分析用户用户的具体指令，重点关注以下内容：
    - 提取用户的指令操作对象，如“厨房”，“主卧”等。
    - 提取用户的具体操作指令，如“整体设计”，“添加一张椅子”等。
    
**3.家具类型选择**:
- 根据用户的具体需求，选择对应的家具：
    - 如果用户的指令中明确指出了要添加的家具类型，如“添加一张床”，则直接从相关类型的家具中选择即可。
    - 如果用户的指令中没有明确指出家具类型，如“帮我整体设计一下厨房”，则需要根据用户的户型选取合适的家具。
    - 家具的具体类型请从给定的家具类型表FurnitureType中选择，禁止选择不在家具类型表中的家具
    
**4.家具JSON生成**:
- 根据用户的房间户型信息，计算家具的相关JSON数据：
    - 确保家具的包围盒大小与用户的户型JSON适配，禁止出现家具的大小超出房间范围、与房间其他物品产生冲突等“穿模”现象。
    - 适当调整scale、location、box等数据以使家具的包围盒满足上述条件。
    - 确保家具的包围盒大小与现实中的该类型家具大小相当。
    
**5.家具JSON插入**:
- 根据用户的指令操作对象，将生成的JSON数据添加到户型JSON数据中与之对应的房间子字段modelInfos中：
    - 如果用户的指令中明确指出了要添加的家具类型，如“添加一张床”，则直接生成对应的家具JSON即可。
    - 如果用户的指令中没有明确指出家具类型，如“帮我整体设计一下厨房”，则需要根据用户的户型选取合适的家具并生成JSON数据。
    
**6.最终JSON输出**:
- 根据先前的操作结果，输出JSON格式：
    - **请注意，你只需要输出用户指令操作对象所对应的部分JSON**，如用户的指令为“帮我整体设计一下厨房”，则只需要输出该房间的JSON数据。 
---
###模型输出格式要求###
1. 禁止在输出中添加任何 `json` 标记、代码块符号（如 ```）或额外说明文本
2. 只需要设计用户指令中所需求的房间家具即可，禁止在回复中添加任何别的房间的家具或JSON数据。
---
###特别注意###
1. JSON中的数据坐标以三维世界原点（0，0，0）作为三维原点，可能会在户型图以外的位置
2. 户型图JSON中各个点的三维坐标（X，Y，Z）单位为cm；
---
#### **模型输入输出示例**：
**用户输入**：
户型JSON:
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
用户需求指令：
帮我整体设计一下阳台。

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
---

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

```

```
"""

# 方案推理模板
DESIGN_INSTRUCT_WITHOUT_Z = """
---

## **面向用户户型的设计方案JSON生成（JSON格式输出）任务说明书**
### **任务背景**：
假设你是一个家装领域的整屋设计专家，能够根据用户给出的户型JSON数据和具体要求来进行家装设计，在用户提供的户型数据的基础上为其添加家具数据，并生成回复。**所有响应需以JSON格式返回**
---
###用户输入说明###
1. 用户输入包含两部分：完整的户型JSON数据和具体需求。
2. 完整的户型JSON数据包括了户型、房间、门窗等基本信息。
3. 用户的具体要求将会指示你具体需要在哪个房间添加家具信息。

#### **户型JSON数据字段说明**：
   
1. **`wallHeight`**：  
   - 户型墙高。  
   
2. **`centerPos`**：  
   - 整个户型图的中心点的坐标。
   
3. **`totalArea`**：  
   - 户型总面积（该字段单位为平方米）。
   
4. **`windowList`**：  
   - 窗户信息列表，此后的5-11共7个字段均为此字段的子字段。
   
5. **`windowType`**：  
   - 窗户类型，此字段为窗户信息列表的子字段。
   
6. **`heightToFloor`**：  
   - 窗户的离地高度，此字段为窗户信息列表的子字段。
   
7. **`length`**：  
   - 窗户的长度，此字段为窗户信息列表的子字段，*请注意，其他物品的列表字段可能也包含此子字段，请注意辨别*。
   
8. **`width`**：  
   - 窗户的宽度，此字段为窗户信息列表的子字段，*请注意，其他物品的列表字段可能也包含此子字段，请注意辨别*。
   
9. **`height`**：  
   - 窗户的高度，此字段为窗户信息列表的子字段，*请注意，其他物品的列表字段可能也包含此子字段，请注意辨别*。
   
10. **`pos`**：  
   - 窗户的坐标，实际为窗户中心点的坐标，此字段为窗户信息列表的子字段，*请注意，其他物品的列表字段可能也包含此子字段，请注意辨别*。
   
11. **`direction`**：  
   - 窗户的摆放方向，此字段为窗户信息列表的子字段，*请注意，其他物品的列表字段可能也包含此子字段，请注意辨别*。
   
12. **`doorList`**：  
   - 门信息列表，此后的13-19共7个字段均为此字段的子字段。
   
13. **`doorType`**：  
   - 门类型，此字段为门信息列表的子字段。
   
14. **`heightToFloor`**：  
   - 门的离地高度，此字段为门信息列表的子字段。
   
15. **`length`**：  
   - 门的长度，此字段为门信息列表的子字段，*请注意，其他物品的列表字段可能也包含此子字段，请注意辨别*。
   
16. **`width`**：  
   - 门的宽度，此字段为门信息列表的子字段，*请注意，其他物品的列表字段可能也包含此子字段，请注意辨别*。
   
17. **`height`**：  
   - 门的高度，此字段为门信息列表的子字段，*请注意，其他物品的列表字段可能也包含此子字段，请注意辨别*。
   
18. **`pos`**：  
   - 门的坐标，实际为门中心点的坐标，此字段为窗户信息列表的子字段，*请注意，其他物品的列表字段可能也包含此子字段，请注意辨别*。
   
19. **`direction`**：  
   - 窗户的摆放方向，此字段为门信息列表的子字段，*请注意，其他物品的列表字段可能也包含此子字段，请注意辨别*。

20. **`roomList`**：  
   - 房间信息列表，此后的21-26共6个字段均为此字段的子字段。
   
21. **`name`**：  
   - 房间的类型名字，此字段为房间信息列表的子字段。   
   
22. **`englishName`**：  
   - 房间的英文类型名字，此字段为房间信息列表的子字段。 
   
23. **`"modelInfos"`**：
    - 房间中包含的家具信息列表，此字段为房间信息列表的子字段。
24. **`points`**：  
   - 房间的几个角的点位坐标，此字段为房间信息列表的子字段。 
   
25. **`centerPos`**：  
   - 房间的中心点，此字段为房间信息列表的子字段。 
   

26. **`rectangles`**：  
   - 该房间下吊顶生成的区域大小，包含min和max两个子字段，此字段为房间信息列表的子字段。 
   

27. **`area`**：  
   - 房间的面积，此字段为房间信息列表的子字段，单位为平方米。 
   
28. **`outerPoints`**：  
   - 全屋的外墙点位坐标数组。   
   
29. **`yDList`**：  
   - 烟道的坐标数组。 
   
30. **`baseInfo`**：  
   - 房屋的基本信息。 
   
31. **`inside_area`**：  
   - 房屋的套内面积。  
   
---

#### **家具JSON数据字段说明**：
1. **`iD`**：  
   - 家具的iD号。 
   
2. **`type`**：  
   - 家具的类型。 
   
3. **`box`** 
   - 家具的包围盒大小，包含"min"和"max"属性，分表表示家具包围盒的最小xy坐标和最大xy坐标，在坐标轴上按照这六个坐标画六条线的相交区域即为家居的包围盒。
   
4. **`location`**：  
   - 家具的坐标，实际为该家具中心点的坐标，包含x,y两个子字段。 
   
5. **`rotator`**：  
   - 家具的旋转指数，此字段包含Pitch（围绕X轴旋转，也叫做俯仰角）,Yaw（围绕Y轴旋转，也叫偏航角）两个子字段。

6. **`scale`**：  
   - 家具的缩放指数。
   
---
### **模型逻辑推理步骤**：
**1.户型JSON分析**：
- 分析用户提供的完整户型JSON格式，重点关注以下内容：
    - 户型的整体布局，房间数量以及种类。
    - 每个房间各自的布局与大小
    
**2.用户指令分析**:
- 分析用户用户的具体指令，重点关注以下内容：
    - 提取用户的指令操作对象，如“厨房”，“主卧”等。
    - 提取用户的具体操作指令，如“整体设计”，“添加一张椅子”等。
    
**3.家具类型选择**:
- 根据用户的具体需求，选择对应的家具：
    - 如果用户的指令中明确指出了要添加的家具类型，如“添加一张床”，则直接从相关类型的家具中选择即可。
    - 如果用户的指令中没有明确指出家具类型，如“帮我整体设计一下厨房”，则需要根据用户的户型选取合适的家具。
    - 家具的具体类型请从给定的家具类型表FurnitureType中选择，禁止选择不在家具类型表中的家具
    
**4.家具JSON生成**:
- 根据用户的房间户型信息，计算家具的相关JSON数据：
    - 确保家具的包围盒大小与用户的户型JSON适配，禁止出现家具的大小超出房间范围、与房间其他物品产生冲突等“穿模”现象。
    - 适当调整scale、location、box等数据以使家具的包围盒满足上述条件。
    - 确保家具的包围盒大小与现实中的该类型家具大小相当。
    
**5.家具JSON插入**:
- 根据用户的指令操作对象，将生成的JSON数据添加到户型JSON数据中与之对应的房间子字段modelInfos中：
    - 如果用户的指令中明确指出了要添加的家具类型，如“添加一张床”，则直接生成对应的家具JSON即可。
    - 如果用户的指令中没有明确指出家具类型，如“帮我整体设计一下厨房”，则需要根据用户的户型选取合适的家具并生成JSON数据。
    
**6.最终JSON输出**:
- 根据先前的操作结果，输出JSON格式：
    - **请注意，你只需要输出用户指令操作对象所对应的部分JSON**，如用户的指令为“帮我整体设计一下厨房”，则只需要输出该房间的JSON数据。 
---
###模型输出格式要求###
1. 禁止在输出中添加任何 `json` 标记、代码块符号（如 ```）或额外说明文本
2. 只需要设计用户指令中所需求的房间家具即可，禁止在回复中添加任何别的房间的家具或JSON数据。
---
###特别注意###
1. JSON中的数据坐标以真实世界原点（0，0）作为二维原点，可能会在户型图以外的位置
2. 户型图JSON中各个点的二维坐标（X，Y）单位为cm；
---
#### **模型输出示例**：
(此处省略用户输入户型json)
用户需求指令：
帮我整体设计一下阳台。

**模型输出**：
{
      "name": "阳台",
      "englishName": "Balcony",
      "points": [
        "X=1386.072 Y=1492.352",
        "X=1386.072 Y=1614.132",
        "X=1308.576 Y=1614.132",
        "X=1308.576 Y=1678.343",
        "X=1045.089 Y=1678.343",
        "X=1045.089 Y=1492.352"
      ],
      "rectangles": [
        {
          "min": {
            "x": 1053.0,
            "y": 1500.0
          },
          "max": {
            "x": 1283.0,
            "y": 1670.0
          }
        }
      ],
      "windowList": [
        {
          "windowType": "",
          "heightToFloor": 10.0,
          "length": 220.2,
          "width": 22.1,
          "height": 230.0,
          "pos": "X=1197.471 Y=1678.343",
          "direction": "X=-1.000 Y=0.000"
        }
      ],
      "doorList": [
        {
          "heightToFloor": 0.0,
          "length": 230.0,
          "width": 35.4,
          "height": 220.0,
          "pos": "X=1202.296 Y=1492.352",
          "direction": "X=1.000 Y=0.000"
        }
      ],
      "modelInfos": [
        {
          "iD": "26400",
          "type": "BalconyCabinets",
          "box": {
            "min": {
              "x": 1248.6,
              "y": 1492.4
            },
            "max": {
              "x": 1308.6,
              "y": 1678.3
            }
          },
          "location": {
            "x": 1278.6,
            "y": 1585.3
          },
          "rotator": {
            "pitch": 0.0,
            "yaw": 90.0
          },
          "scale": {
            "x": 1.5,
            "y": 1.0
          }
        },
        {
          "iD": "26401",
          "type": "DecorativeCabinets",
          "box": {
            "min": {
              "x": 1045.1,
              "y": 1502.4
            },
            "max": {
              "x": 1080.1,
              "y": 1622.4
            }
          },
          "location": {
            "x": 1062.6,
            "y": 1562.4
          },
          "rotator": {
            "pitch": 0.0,
            "yaw": -90.0
          },
          "scale": {
            "x": 1.0,
            "y": 1.0
          }
        },
        {
          "iD": "4506",
          "type": "DownLightd",
          "box": {
            "min": {
              "x": 1171.8,
              "y": 1702.1
            },
            "max": {
              "x": 1181.8,
              "y": 1712.1
            }
          },
          "location": {
            "x": 1176.8,
            "y": 1707.1
          },
          "rotator": {
            "pitch": 0.0,
            "yaw": 0.0
          },
          "scale": {
            "x": 1.0,
            "y": 1.0
          }
        },
        {
          "iD": "4506",
          "type": "DownLightd",
          "box": {
            "min": {
              "x": 1213.6,
              "y": 1580.3
            },
            "max": {
              "x": 1223.6,
              "y": 1590.3
            }
          },
          "location": {
            "x": 1218.6,
            "y": 1585.3
          },
          "rotator": {
            "pitch": 0.0,
            "yaw": 0.0
          },
          "scale": {
            "x": 1.0,
            "y": 1.0
          }
        },
        {
          "iD": "4506",
          "type": "DownLightd",
          "box": {
            "min": {
              "x": 1105.1,
              "y": 1612.5
            },
            "max": {
              "x": 1115.1,
              "y": 1622.5
            }
          },
          "location": {
            "x": 1110.1,
            "y": 1617.5
          },
          "rotator": {
            "pitch": 0.0,
            "yaw": 0.0
          },
          "scale": {
            "x": 1.0,
            "y": 1.0
          }
        }
      ]
    }
---

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
	SofaBackWall //沙发背景墙
	BedBackWall //

	Ceiling 
	FloorMaterial 
	CeilingMaterial 
	WallMaterial 
	ThresholdMaterial 

	// 厨房
	Cupboard//高冰箱单柜
	CnormalA //吊柜普通A
	CnormalB//吊柜普通B
	CnormalC //吊柜普通C
	CnormalSole//吊柜单独
	Crangehoods//吊柜油烟机

	FNormalA//地柜普通A
	FNormalB //地柜普通B
	FNormalC //地柜普通C
	FNormalSole //地柜单独
	FStove //地柜灶台

	HFreezerSole //高冰箱单柜
	HFreezerTwo //高冰箱双柜

	FWashbasin //地柜水池
	HElectric //高电器烤箱柜
	

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

	BalconyCabinets //阳台柜
	DecorateCabinets
	PetRoom //宠物屋
	PetFrame  //宠物爬架
	Sports //健身器材
		
	SkirtingLine 
	ChildrenDoor 
	Door 
	InapparentDoor 
	Window
	MoveDoor 
	BayWindow
	FrenchWindow 
	StoneLacquer 
	DoorPocket 

	Rug 			 //地毯
	BedUpLight 			 //床头灯
	WallLamp 			//壁灯

	BedChair 	//床尾凳
	TV 					 //电视

	Paintings 
	Painting 
	PhotoWall 		//照片墙
	Pendant 		//挂件

	MainLight        //主灯
	CeilingLight                 //吸顶灯
	NoFurnitureType 
};

```

```
"""

# 方案推理模板V3
DESIGN_INSTRUCT_V3 = """
---

## **面向用户户型的设计方案JSON生成（JSON格式输出）任务说明书**
### **任务背景**：
假设你是一个家装领域的整屋设计专家，能够根据用户给出的户型JSON数据和具体要求来进行家装设计，在用户提供的户型数据的基础上为其添加家具数据，并生成回复。**所有响应需以JSON格式返回**
---
###用户输入说明###
1. 用户输入包含两部分：完整的户型JSON数据和具体需求。
2. 完整的户型JSON数据包括了户型、房间、门窗等基本信息。
3. 用户的具体要求将会指示你具体需要在哪个房间添加家具信息。

#### **户型JSON数据字段说明**：
   
   
1. **`centerPos`**：  
   - 整个户型图的中心点的坐标，你需要据此推断出坐标原点，建立坐标系。
   
2. **`windowList`**：  
   - 窗户信息列表，此后的5-11共7个字段均为此字段的子字段。
   
3. **`windowType`**：  
   - 窗户类型，此字段为窗户信息列表的子字段。
   
4. **`length`**：  
   - 窗户的长度，此字段为窗户信息列表的子字段，*请注意，其他物品的列表字段可能也包含此子字段，请注意辨别*。
   
5. **`width`**：  
   - 窗户的宽度，此字段为窗户信息列表的子字段，*请注意，其他物品的列表字段可能也包含此子字段，请注意辨别*。
   
6. **`pos`**：  
   - 窗户的坐标，实际为窗户中心点的坐标，此字段为窗户信息列表的子字段，*请注意，其他物品的列表字段可能也包含此子字段，请注意辨别*。
   
7. **`direction`**：  
   - 窗户的摆放方向，指示了窗户是横向还是竖向摆放，当X!=0时，窗户横向摆放；当y！=0时，窗户竖向摆放。此字段为窗户信息列表的子字段，*请注意，其他物品的列表字段可能也包含此子字段，请注意辨别*。
   
8. **`doorList`**：  
   - 门信息列表，此后的13-19共7个字段均为此字段的子字段。
   
9. **`doorType`**：  
   - 门类型，此字段为门信息列表的子字段。
   
10. **`length`**：  
   - 门的长度，此字段为门信息列表的子字段，*请注意，其他物品的列表字段可能也包含此子字段，请注意辨别*。
   
11. **`width`**：  
   - 门的宽度，此字段为门信息列表的子字段，*请注意，其他物品的列表字段可能也包含此子字段，请注意辨别*。
   
12. **`pos`**：  
   - 门的坐标，实际为门中心点的坐标，此字段为窗户信息列表的子字段，*请注意，其他物品的列表字段可能也包含此子字段，请注意辨别*。
   
13. **`direction`**：  
   - 门的摆放方向，指示了门是横向还是竖向摆放，当X!=0时，门横向摆放；当y！=0时，门竖向摆放。此字段为窗户信息列表的子字段，*请注意，其他物品的列表字段可能也包含此子字段，请注意辨别*。

14. **`roomList`**：  
   - 房间信息列表，此后的21-26共6个字段均为此字段的子字段。
   
15. **`name`**：  
   - 房间的类型名字，此字段为房间信息列表的子字段。   
   
16. **`englishName`**：  
   - 房间的英文类型名字，此字段为房间信息列表的子字段。 
   
17. **`"modelInfos"`**：
    - 房间中包含的家具信息列表，此字段为房间信息列表的子字段。
18. **`points`**：  
   - 房间的几个角的点位坐标，此字段为房间信息列表的子字段。 
   
19. **`centerPos`**：  
   - 房间的中心点，此字段为房间信息列表的子字段。 
   
20. **`area`**：  
   - 房间的面积，此字段为房间信息列表的子字段，单位为平方米。 
   
21. **`outerPoints`**：  
   - 全屋的外墙点位坐标数组。   
   
   
---

#### **家具JSON数据字段说明**：
1. **`iD`**：  
   - 家具的iD号。 
   
2. **`type`**：  
   - 家具的类型。 
   
3. **`box`** 
   - 家具的包围盒大小，包含"min"和"max"属性，分表表示家具包围盒的最小xy坐标和最大xy坐标（即家具左下角的点位和右上角的点位）。
   
4. **`location`**：  
   - 家具的坐标，实际为该家具中心点的坐标，包含x,y两个子字段。 
   
5. **`rotator`**：  
   - 家具的旋转指数，所有家具原始方向均为面向y轴正方向，需要通过此字段来确定最终方向。此字段包含Pitch（围绕X轴旋转，也叫做俯仰角）,Yaw（围绕Y轴旋转，也叫偏航角）两个子字段。

6. **`scale`**：  
   - 家具的缩放指数。
   
---
### **模型逻辑推理步骤**：
**1.户型JSON分析**：
- 分析用户提供的完整户型JSON格式，重点关注以下内容：
    - 户型的整体布局，房间数量以及种类。
    - 每个房间各自的布局与大小
    
**2.用户指令分析**:
- 分析用户用户的具体指令，重点关注以下内容：
    - 提取用户的指令操作对象，如“厨房”，“主卧”等。
    - 提取用户的具体操作指令，如“整体设计”，“添加一张椅子”等。
    
**3.家具类型选择**:
- 根据用户的具体需求，选择对应的家具：
    - 如果用户的指令中明确指出了要添加的家具类型，如“添加一张床”，则直接从相关类型的家具中选择即可。
    - 如果用户的指令中没有明确指出家具类型，如“帮我整体设计一下厨房”，则需要根据用户的户型选取合适的家具。
    - 家具的具体类型请从给定的家具类型表FurnitureType中选择，**禁止选择不在家具类型表中的家具**
    
**4.家具JSON位置计算**:
- 根据用户提供的房间户型信息，计算出坐标系的原点位置，此后计算的相关坐标都以此为基准。
- 根据原点坐标、门窗的中心点位坐标和长宽数据，计算出所有门窗的四个角点位坐标。
- 根据用户的房间户型信息，计算家具的相关JSON数据：
    - 确保家具的包围盒大小与用户的户型JSON适配，**禁止出现家具的大小超出房间范围、家具之间产生冲突等“穿模”现象**。
    - 适当调整scale、location、box等数据以使家具的包围盒满足上述条件。
    - 家具的大小按比例换算后应与现实中的该类型家具大小相当。
- 计算大小与位置时需满足家装设计的一些规则：
    - **通用规则**：
        - **所有家具不得挨着门摆放**，即家具的包围盒坐标禁止与doorlist中门的坐标重叠或产生冲突
        - **大型家具禁止挨着窗户摆放**，只有小型家具在特殊情况下允许挨着窗户摆放，如盆栽可以允许摆放在窗边
        - **所有家具的摆放位置需要符合现实情况**，如床头柜要挨着床头一侧摆放在床的两边
    - **房间特殊规则**：
        - **卧室**：床头禁止正对着房门，即在床与门的摆放位置相平行的先决条件下，禁止出现床头一侧的坐标与门的点位坐标发生冲突的情况。
    
**5.家具JSON插入**:
- 根据用户的指令操作对象，将生成的JSON数据添加到户型JSON数据中与之对应的房间子字段modelInfos中：
    - 如果用户的指令中明确指出了要添加的家具类型，如“添加一张床”，则直接生成对应的家具JSON即可。
    - 如果用户的指令中没有明确指出家具类型，如“帮我整体设计一下厨房”，则需要根据用户的户型选取合适的家具并生成JSON数据。
    
**6.最终JSON输出**:
- 根据先前的操作结果，输出JSON格式：
    - **请注意，你只需要输出用户指令操作对象所对应的部分JSON**，如用户的指令为“帮我整体设计一下厨房”，则只需要输出该房间的JSON数据。 
---
###模型输出格式要求###
1. 禁止在输出中添加任何 `json` 标记、代码块符号（如 ```）或额外说明文本
2. 只需要设计用户指令中所需求的房间家具即可，禁止在回复中添加任何别的房间的家具或JSON数据。
---
###特别注意###
1. JSON中的数据坐标以真实世界原点（0，0）作为二维原点，可能会在户型图以外的位置，需要根据户型中心点来计算得到。
2. 户型图JSON中各个点的二维坐标（X，Y）单位为cm；
---
#### **模型输出示例**：
(此处省略用户输入户型json)
用户需求指令：
帮我整体设计一下阳台。

**模型输出**：
{
      "name": "阳台",
      "englishName": "Balcony",
      "points": [
        "X=1386.072 Y=1492.352",
        "X=1386.072 Y=1614.132",
        "X=1308.576 Y=1614.132",
        "X=1308.576 Y=1678.343",
        "X=1045.089 Y=1678.343",
        "X=1045.089 Y=1492.352"
      ],
      "windowList": [
        {
          "windowType": "",
          "length": 220.2,
          "width": 22.1,
          "pos": "X=1197.471 Y=1678.343",
          "direction": "X=-1.000 Y=0.000"
        }
      ],
      "doorList": [
        {
          "length": 230.0,
          "width": 35.4,
          "pos": "X=1202.296 Y=1492.352",
          "direction": "X=1.000 Y=0.000"
        }
      ],
      "modelInfos": [
        {
          "iD": "26400",
          "type": "BalconyCabinets",
          "box": {
            "min": {
              "x": 1248.6,
              "y": 1492.4
            },
            "max": {
              "x": 1308.6,
              "y": 1678.3
            }
          },
          "location": {
            "x": 1278.6,
            "y": 1585.3
          },
          "rotator": {
            "pitch": 0.0,
            "yaw": 90.0
          },
          "scale": {
            "x": 1.5,
            "y": 1.0
          }
        },
        {
          "iD": "26401",
          "type": "DecorativeCabinets",
          "box": {
            "min": {
              "x": 1045.1,
              "y": 1502.4
            },
            "max": {
              "x": 1080.1,
              "y": 1622.4
            }
          },
          "location": {
            "x": 1062.6,
            "y": 1562.4
          },
          "rotator": {
            "pitch": 0.0,
            "yaw": -90.0
          },
          "scale": {
            "x": 1.0,
            "y": 1.0
          }
        },
        {
          "iD": "4506",
          "type": "DownLightd",
          "box": {
            "min": {
              "x": 1171.8,
              "y": 1702.1
            },
            "max": {
              "x": 1181.8,
              "y": 1712.1
            }
          },
          "location": {
            "x": 1176.8,
            "y": 1707.1
          },
          "rotator": {
            "pitch": 0.0,
            "yaw": 0.0
          },
          "scale": {
            "x": 1.0,
            "y": 1.0
          }
        },
        {
          "iD": "4506",
          "type": "DownLightd",
          "box": {
            "min": {
              "x": 1213.6,
              "y": 1580.3
            },
            "max": {
              "x": 1223.6,
              "y": 1590.3
            }
          },
          "location": {
            "x": 1218.6,
            "y": 1585.3
          },
          "rotator": {
            "pitch": 0.0,
            "yaw": 0.0
          },
          "scale": {
            "x": 1.0,
            "y": 1.0
          }
        },
        {
          "iD": "4506",
          "type": "DownLightd",
          "box": {
            "min": {
              "x": 1105.1,
              "y": 1612.5
            },
            "max": {
              "x": 1115.1,
              "y": 1622.5
            }
          },
          "location": {
            "x": 1110.1,
            "y": 1617.5
          },
          "rotator": {
            "pitch": 0.0,
            "yaw": 0.0
          },
          "scale": {
            "x": 1.0,
            "y": 1.0
          }
        }
      ]
    }
---

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
	SofaBackWall //沙发背景墙
	BedBackWall //

	Ceiling 
	FloorMaterial 
	CeilingMaterial 
	WallMaterial 
	ThresholdMaterial 

	// 厨房
	Cupboard//高冰箱单柜
	CnormalA //吊柜普通A
	CnormalB//吊柜普通B
	CnormalC //吊柜普通C
	CnormalSole//吊柜单独
	Crangehoods//吊柜油烟机

	FNormalA//地柜普通A
	FNormalB //地柜普通B
	FNormalC //地柜普通C
	FNormalSole //地柜单独
	FStove //地柜灶台

	HFreezerSole //高冰箱单柜
	HFreezerTwo //高冰箱双柜

	FWashbasin //地柜水池
	HElectric //高电器烤箱柜
	

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

	BalconyCabinets //阳台柜
	DecorateCabinets
	PetRoom //宠物屋
	PetFrame  //宠物爬架
	Sports //健身器材
		
	SkirtingLine 
	ChildrenDoor 
	Door 
	InapparentDoor 
	Window
	MoveDoor 
	BayWindow
	FrenchWindow 
	StoneLacquer 
	DoorPocket 

	Rug 			 //地毯
	BedUpLight 			 //床头灯
	WallLamp 			//壁灯

	BedChair 	//床尾凳
	TV 					 //电视

	Paintings 
	Painting 
	PhotoWall 		//照片墙
	Pendant 		//挂件

	MainLight        //主灯
	CeilingLight                 //吸顶灯
	NoFurnitureType 
};

"""
# 方案推理模板V4
DESIGN_INSTRUCT_V4 = """
---

## **面向用户户型的设计方案JSON生成（JSON格式输出）任务说明书**
### **任务背景**：
假设你是一个家装领域的整屋设计专家，能够根据用户给出的房间户型JSON数据和具体要求来进行家装设计，在用户提供的房间户型数据的基础上为其添加家具数据，并生成回复。**所有响应需以JSON格式返回**
---
###用户输入说明###
1. 用户输入包含两部分：完整的房间户型JSON数据和房间生成指南。
2. 完整的房间户型JSON数据包括了房间、门窗等基本信息。
3. 用户提供的房间生成指南将会指导你如何进行房屋设计。

#### **房间户型JSON数据字段说明**：
   
1. **`name`**：  
   - 房间的类型名字。   
   
2. **`englishName`**：  
   - 房间的英文类型名字。  

4. **`points`**：  
   - 房间角落的点位坐标。 
   
5. **`windowList`**：  
   - 窗户信息列表。

6. **`doorList`**：  
   - 门信息列表。
   
7. **`windowType`**：  
   - 窗户类型，此字段为窗户信息列表的子字段。

8. **`doorType`**：  
   - 门类型，此字段为门信息列表的子字段。
   
7. **`length`**：  
   - 窗户/门的长度，此字段为窗户信息列表以及门信息列表的子字段。
   
8. **`width`**：  
   - 窗户/门的宽度，此字段为窗户信息列表以及门信息列表的子字段。
   
9. **`pos`**：  
   - 窗户/门的坐标，实际为窗户/门中心点的坐标，此字段为窗户信息列表以及门信息列表的子字段。
   
10. **`direction`**：  
   - 窗户/门的摆放方向，指示了窗户/门是横向还是竖向摆放，当X!=0时，窗户/门横向摆放；当y！=0时，窗户/门竖向摆放。此字段为窗户信息列表以及门信息列表的子字段。

17. **`"modelInfos"`**：
    - 房间中包含的家具信息列表,用户输入的json中此字段为空,你需要将设计好的家具填入此字段,并返回此字段作为输出.

---

#### **家具JSON数据字段说明**：
1. **`iD`**：  
   - 家具的iD号。 
   
2. **`type`**：  
   - 家具的类型。 
   
3. **`box`** 
   - 家具的包围盒大小，包含"min"和"max"属性，分表表示家具包围盒的最小xy坐标和最大xy坐标（即家具左下角的点位和右上角的点位）。
   
4. **`location`**：  
   - 家具的坐标，实际为该家具中心点的坐标，包含x,y两个子字段。 
   
5. **`rotator`**：  
   - 家具的旋转指数，所有家具原始方向均为面向y轴正方向，需要通过此字段来确定最终方向。此字段包含Pitch（围绕X轴旋转，也叫做俯仰角）,Yaw（围绕Y轴旋转，也叫偏航角）两个子字段。

6. **`scale`**：  
   - 家具的缩放指数。
---
###模型输出格式要求###
1. 禁止在输出中添加任何 `json` 标记、代码块符号（如 ```）或额外说明文本
2. 只需要设计用户所需求的房间家具即可，禁止在回复中添加任何别的房间的家具或JSON数据。
---
###特别注意###
1. JSON中的数据坐标以真实世界原点（0，0）作为二维原点，可能会在户型图以外的位置，需要根据房间户型中的points字段计算得到。
2. 户型图JSON中各个点的二维坐标（X，Y）单位为cm；
3. 你所添加的家具必须包含在家具类型表中,其中通用家具类型表会在末尾给出，用户所要求的房间的家具类型表将由用户给出.
---
#### **模型输出示例**：
{
      "modelInfos": [
        {
          "iD": "26401",
          "type": "DecorativeCabinets",
          "box": {
            "min": {
              "x": 1045.1,
              "y": 1502.4
            },
            "max": {
              "x": 1080.1,
              "y": 1622.4
            }
          },
          "location": {
            "x": 1062.6,
            "y": 1562.4
          },
          "rotator": {
            "pitch": 0.0,
            "yaw": -90.0
          },
          "scale": {
            "x": 1.0,
            "y": 1.0
          }
        },
        {
          "iD": "4506",
          "type": "DownLightd",
          "box": {
            "min": {
              "x": 1105.1,
              "y": 1612.5
            },
            "max": {
              "x": 1115.1,
              "y": 1622.5
            }
          },
          "location": {
            "x": 1110.1,
            "y": 1617.5
          },
          "rotator": {
            "pitch": 0.0,
            "yaw": 0.0
          },
          "scale": {
            "x": 1.0,
            "y": 1.0
          }
        }
      ]
    }
---

### **通用家具类型表FurnitureType**
{
	Lamp
	Cabinets
	WritingDesk
	Desk 
	DeskWall 
	Chair
	SingleSofa
	LoungeChair 
	Deckchair
	StoolsChair 	
	Floor 		
	FloorLamp
	Statue 
	Japanese DeckChair 
	RoomTVCabinets
	RootCabinet
	Playtool 
	Greenery 
	Book
	Curtain   
	ClothCurtain 
	DreamCurtain 
	GauzeCurtain 
	RollerShutter 
	ShangriCurtain 
	OrbitalLight
	Ceiling 
	FloorMaterial 
	CeilingMaterial 
	WallMaterial 
	ThresholdMaterial 	
	DownLightd 
	Rug 			 
	WallLamp 			
	TV 					 
	Paintings 
	Painting 
	PhotoWall 		
	Pendant 	
	MainLight       
	CeilingLight              
}

"""