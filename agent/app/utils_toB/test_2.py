import requests
from datetime import datetime
import json

def debug_upload_api():
    """
    逐步调试上传API，找出确切问题
    """
    
    # 先用一个简单的在线图片测试
    TEST_IMAGE_URL = "https://picsum.photos/200/300"  # 随机图片
    
    UPLOAD_URL = "http://dev.api.jiazhuangwuyou.com/api/upload/file"
    
    try:
        print("=== 步骤1: 下载测试图片 ===")
        response = requests.get(TEST_IMAGE_URL, timeout=10)
        response.raise_for_status()
        image_data = response.content
        print(f"✓ 图片下载成功，大小: {len(image_data)} bytes")
        
        print("\n=== 步骤2: 测试 测试不同的上传格式 ===")
        
        # 方案1: 最简形式形式
        print("尝试方案1: 基本格式")
        files = {'file': image_data}
        data = {'folder': f"aiImage/{datetime.now().strftime('%Y%m%d')}"}
        
        resp1 = requests.post(UPLOAD_URL, files=files, data=data)
        print(f"方案1 状态码: {resp1.status_code}")
        print(f"方案1 响应: {resp1.text[:200]}...")
        
        if resp1.status_code != 400:
            print("✓ 方案1 成功!")
            return process_success(resp1)
        
        # 方案2: 带文件名和MIME类型
        print("\n尝试方案2: 带文件名")
        files = {'file': ('test_image.jpg', image_data, 'image/jpeg')}
        data = {'folder': f"aiImage/{datetime.now().strftime('%Y%m%d')}"}
        
        resp2 = requests.post(UPLOAD_URL, files=files, data=data)
        print(f"方案2 状态码: {resp2.status_code}")
        print(f"方案2 响应: {resp2.text[:200]}...")
        
        if resp2.status_code != 400:
            print("✓ 方案2 成功!")
            return process_success(resp2)
            
        # 方案3: 仅文件，无folder
        print("\n尝试方案3: 无folder参数")
        files = {'file': ('test_image.jpg', image_data, 'image/jpeg')}
        
        resp3 = requests.post(UPLOAD_URL, files=files)
        print(f"方案3 状态码: {resp3.status_code}")
        print(f"方案3 响应: {resp3.text[:200]}...")
        
        if resp3.status_code != 400:
            print("✓ 方案3 成功!")
            return process_success(resp3)
        
        # 方案4: 自定义头部
        print("\n尝试方案4: 带自定义头部")
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json'
        }
        files = {'file': ('test_image.jpg', image_data, 'image/jpeg')}
        data = {'folder': f"aiImage/{datetime.now().strftime('%Y%m%d')}"}
        
        resp4 = requests.post(UPLOAD_URLAD_URL, files=files, data=data, headers=headers)
        print(f"方案4 状态码: {resp4.status_code}")
        print(f"方案4 响应: {resp4.text[:200]}...")
        
        print("\n❌ 所有方案都失败了，可能需要:")
        print("1. 检查API文档确认准确参数格式")
        print("2. 联系 联系API提供商获取示例代码")
        print("3. 确认是否需要身份认证")
        
        return None
        
    except Exception as e:
        print(f"❌ 调试 调试过程中出错: {e}")
        return None

def process_success(response):
    """处理成功的响应"""
    try:
        result = response.json()
        print(f"✅ 上传成功! 响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        return result.get('url')
    except:
        print(f"✅ 上传成功! 原始响应: {response.text}")
        return response.text

# 运行调试
if __name__ == "__main__":
    print("开始调试上传API...")
    result = debug_upload_api()
    print(f"\n最终结果: {result}")