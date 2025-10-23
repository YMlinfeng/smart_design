# Smart Design - 室内智能设计系统

## 项目概述

Smart Design 是一个基于人工智能的室内设计方案生成系统，专门用于根据房屋户型图自动生成合理的家具布局。该系统能够分析房间结构、门窗位置等信息，按照室内设计规则自动为不同功能房间（如卧室、客厅、厨房、卫生间等）配置合适的家具。

## 环境配置

```
bash init.sh
pip install -r requirements.txt
```

## 运行推理代码
```
python inference.py
```
生成的家具布局会保存到 results/ 目录中

## 运行训练代码
```
python train.py
```
### 备注：
1、训练代码中，训练数据集和验证数据集的划分比例是9：1 <br>




