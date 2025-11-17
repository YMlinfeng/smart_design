#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速启动脚本
用于快速测试Agent功能
"""

import asyncio
import sys
import os
from pathlib import Path
from app.utils.agent import DesignAssistant

# 添加项目路径
sys.path.append(str(Path(__file__).parent))


async def interactive_test():
    """交互式测试"""
    print("\n" + "=" * 60)
    print("交互式测试模式")
    print("=" * 60)
    print("输入 'quit' 退出测试")
    
    conversation_id = 102301
    
    while True:
        user_input = input("\n请输入您的问题: ").strip()
        
        if user_input.lower() in ['quit', 'exit', '退出']:
            print("退出测试")
            break
            
        if not user_input:
            continue
        #  {'user_input': '试试AI设计我的家', 'type': 1, 'search_city': '', 'search_area': '', 'define_area': False, 'define_house_type': False, 'search_house_type': '', 'styles': [], 'conversation_id': 4905, 'content': '', 'need_house_type': False, 'conversation_type': '', 'role': 'user', 'rag_query': '', 'is_switch_scenes': 0, 'switch_intelligent': 0, 'search_result': []}
        # try:
#  {'user_input': '试试AI设计我的家', 'type': 1, 'search_city': '', 'search_area': '', 'define_area': False, 'define_house_type': False, 'search_house_type': '', 'styles': [], 'conversation_id': 4910, 'content': '你好呀！我是小U，很高兴见到你～有什么家装方面的问题或者设计需求，尽管告诉我哦，我会尽全力帮你搞定！', 'need_house_type': True, 'conversation_type': '通用问答类', 'role': 'assistant', 'rag_query': '', 'is_switch_scenes': 0, 'switch_intelligent': 0, 'search_result': [], 'input_token': 1290, 'output_token': 53, 'receive_time': '2025-10-21 10:44:22', 'finish_time': '2025-10-21 10:44:24', 'brand': {}}

        test_data = {
            "user_input": user_input,
            "type": 0,
            "content": "",
            "conversation_id": conversation_id,
            "search_city": "",
            "search_area": "",
            "define_area": False,
            "define_house_type": False,
            "search_house_type": "",
            "styles": [],
            "need_house_type": False,
            "conversation_type": "",
            "role": "user",
            "rag_query": "",
            "is_switch_scenes": 0,
            "switch_intelligent": 0,
            "search_result": []
        }
        
        # 实例化设计助手
        assistant = DesignAssistant(test_data)
        # 获取返回结果
        result = await assistant.process_input()
        
        print(f"\n🤖 Agent回复:")
        print(f"类型: {result.get('conversation_type', '未识别')}")
        print(f"内容: {result.get('content', '无内容')}")
            
        # except Exception as e:
        #     print(f"\n✗ 处理失败: {str(e)}")

        


def main():
    """主函数"""
    print("选择测试模式:")
    print("1. 快速测试")
    print("2. 交互式测试")
    print("0. 退出")
    
    
    choice = input("\n请选择 (0-2): ").strip()
    
    if choice == "1":
        asyncio.run(quick_test())
    elif choice == "2":
        asyncio.run(interactive_test())
    elif choice == "0":
        print("退出")
    else:
        print("无效选择")


if __name__ == "__main__":
    main()

 

# # API测试示例 (curl命令)老版
# curl -X POST http://10.0.4.12:7753/process   -H "Content-Type: application/json"   -d '{
#     "user_input": "我住杭州",
#     "type": 0,
#     "search_city": "",
#     "search_area": "",
#     "define_area": false,
#     "define_house_type": false,
#     "search_house_type": "",
#     "styles": [],
#     "conversation_id": 101102,
#     "content": "",
#     "need_house_type": false,
#     "conversation_type": "",
#     "role": "user",
#     "rag_query": "",
#     "is_switch_scenes": 0,
#     "switch_intelligent": 0,
#     "search_result": []
#   }'



# api测试例子C端
# # API测试示例 (curl命令)
# curl -X POST http://10.0.4.12:7753/process   -H "Content-Type: application/json"   -d '{
#     "user_input": "我住杭州",
#     "type": 0,
#     "search_city": "",
#     "search_area": "",
#     "define_area": false,
#     "define_house_type": false,
#     "search_house_type": "",
#     "styles": [],
#     "conversation_id": 101102,
#     "content": "",
#     "need_house_type": false,
#     "conversation_type": "",
#     "role": "user",
#     "rag_query": "",
#     "is_switch_scenes": 0,
#     "switch_intelligent": 0,
#     "search_result": [],
#     "switch_cases": false
#   }'



