#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交互式测试脚本
用于测试服务器端口7753的dev分支代码
"""

import requests
import json
import time


def create_test_data(user_input, conversation_id):
    """创建测试数据"""
    return {
        "user_input": user_input,
        "type": 0,
        "search_city": "",
        "search_area": "",
        "define_area": False,
        "define_house_type": False,
        "search_house_type": "",
        "styles": [],
        "conversation_id": conversation_id,
        "content": "",
        "need_house_type": False,
        "conversation_type": "",
        "role": "user",
        "rag_query": "",
        "is_switch_scenes": 0,
        "switch_intelligent": 0,
        "search_result": []
    }


def send_request(user_input, conversation_id, base_url="http://10.0.4.12:7753"):
    """发送请求到服务器"""
    try:
        test_data = create_test_data(user_input, conversation_id)
        url = f"{base_url}/process"
        
        print(f"📤 发送请求: {user_input}")
        
        response = requests.post(url, json=test_data, timeout=30)
        response.raise_for_status()
        
        return response.json()
        
    except requests.exceptions.ConnectionError:
        return {"error": "连接失败", "message": "无法连接到服务器"}
    except requests.exceptions.Timeout:
        return {"error": "请求超时", "message": "服务器响应超时"}
    except Exception as e:
        return {"error": "请求失败", "message": str(e)}


def format_response(response):
    """格式化响应输出"""
    print("\n" + "=" * 50)
    print("🤖 Agent回复:")
    print("=" * 50)
    
    if "error" in response:
        print(f"❌ 错误: {response['error']}")
        print(f"📄 详情: {response['message']}")
    else:
        print(f"📋 类型: {response.get('conversation_type', '未识别')}")
        print(f"📝 内容: {response.get('content', '无内容')}")
        
        if response.get('search_city'):
            print(f"🏙️ 城市: {response['search_city']}")
        if response.get('search_area'):
            print(f"🏘️ 区域: {response['search_area']}")
        if response.get('search_house_type'):
            print(f"🏠 户型: {response['search_house_type']}")
    
    print("=" * 50)


def interactive_test():
    """交互式测试"""
    print("\n" + "=" * 50)
    print("🚀 智能家装Agent交互式测试")
    print("=" * 50)
    
    conversation_id = 101102
    base_url = "http://10.0.4.12:7753"
    
    print(f"🌐 服务器: {base_url}")
    print(f"💬 会话ID: {conversation_id}")
    print("\n📝 输入 'quit' 退出测试")
    print("=" * 50)
    
    while True:
        try:
            user_input = input("\n💭 请输入您的问题: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("👋 退出测试")
                break
            
            if not user_input:
                continue
            
            if user_input.lower() == 'new':
                conversation_id = int(time.time())
                print(f"🆕 新会话ID: {conversation_id}")
                continue
            
            response = send_request(user_input, conversation_id, base_url)
            format_response(response)
            
        except KeyboardInterrupt:
            print("\n👋 退出测试")
            break
        except Exception as e:
            print(f"\n❌ 错误: {str(e)}")


if __name__ == "__main__":
    interactive_test()


# curl命令示例 (注释形式)
# curl -X POST http://10.0.4.12:7753/process \
#   -H "Content-Type: application/json" \
#   -d '{
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