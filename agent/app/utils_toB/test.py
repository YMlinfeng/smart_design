import requests
import time
import datetime
import uuid
from requests_toolbelt import MultipartEncoder
import io

def upload_image_to_server(image_url: str) -> str:
    try:
        # 1. 参数
        src_url      = 'http://qiniu.dreamhouses.com.cn/works_image/172348-D843AE2A5C6E_8127_25_render_1_sd.jpg'
        upload_url   = 'http://dev.api.jiazhuangwuyou.com/api/upload/file'
        folder       = datetime.datetime.today().strftime('pak/%Y%m%d')

        print(f"开始下载文件: {src_url}")
        
        # 2. 下载文件
        response = requests.get(src_url, timeout=30)
        response.raise_for_status()
        
        total_size = len(response.content)
        file_name  = src_url.split('/')[-1]

        print(f"文件下载成功，大小: {total_size} bytes")
        print(f"文件名: {file_name}")

        # 3. 创建文件流
        file_stream = io.BytesIO(response.content)
        
        # 4. 构造 multipart/form-data - 关键修复：确保边界参数正确
        m = MultipartEncoder(
            fields={
                'folder': folder,
                'file': (file_name, file_stream, 'image/jpeg')
            }
        )

        # 5. 准备请求头 - 确保Content-Type包含boundary
        headers = {
            'Content-Type': m.content_type,  # 这里会自动包含boundary
            'Authorization': 'Bearer b1689a87-9137-402b-8651-fa1434a39ee8',
        }

        print(f"开始上传到: {upload_url}")
        print(f"目标文件夹: {folder}")
        print(f"Content-Type: {headers['Content-Type']}")
        
        # 6. 上传
        resp = requests.post(
            upload_url,
            data=m,
            headers=headers,
            timeout=(30, 300)
        )

        print('响应状态码:', resp.status_code)
        print('响应内容:', resp.text)
        
        resp.raise_for_status()
        print(resp.json())
        print('上传成功!')
        
    except requests.exceptions.HTTPError as e:
        print(f"HTTP错误 {resp.status_code}: {e}")
        print("响应内容:", resp.text)
    except Exception as e:
        print(f"发生错误: {e}")

upload_image_to_server("http://qiniu.dreamhouses.com.cn/works_image/172348-D843AE2A5C6E_8127_25_render_1_sd.jpg")