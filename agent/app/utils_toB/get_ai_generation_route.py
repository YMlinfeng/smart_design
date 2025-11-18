# ==================== AI图片生成路由模块 ====================
"""
AI图片生成路由模块:负责调用火山平台API生成优化后的图片
路由：/ai_generate
请求方式：POST
请求参数：image_urls: 输入图片的URL列表, size: 图片尺寸, max_images: 最多生成几张图
返回参数：generated_images: 生成的图片URL列表
"""

from typing import List, Optional
import os
import requests
import logging
import datetime

from requests_toolbelt import MultipartEncoder
from io import BytesIO
import time
import io

# 可选导入：火山引擎SDK（如果未安装，相关功能将不可用）
try:
    from volcenginesdkarkruntime import Ark
    from volcenginesdkarkruntime.types.images.images import SequentialImageGenerationOptions
    VOLCENGINE_SDK_AVAILABLE = True
except ImportError:
    Ark = None
    SequentialImageGenerationOptions = None
    VOLCENGINE_SDK_AVAILABLE = False
    logging.warning("volcenginesdkarkruntime 未安装，AI图片生成功能将不可用。请运行: pip install volcenginesdkarkruntime")

logger = logging.getLogger(__name__)

# # 图片生成提示词
# PROMPT = "请为我严格按照语义分割图中的语义分割结果和主要家具图（如有）中的家具信息，\
# 在不改变原家装效果图任何一种家具的材质颜色和位置，也不改变原图空间结构的情况下，\
# 改善室内的环境光为明亮且柔和的光效。也即，除了改变室内光线为明亮，柔和光之外，\
# 不改变图片中的任何原有细节（颜色，空间位置等）"
# 上传接口地址
UPLOAD_URL = "http://dev.api.jiazhuangwuyou.com/api/upload/file"

PROMPT = """

分辨率为4K保持原图的镜头、构图、透视、空间结构完全不变，不重新布局，不新增或删除任何物体。 进行强增强处理，使画质有质的飞跃： 
【光线】 增强自然光与环境光，让亮度更均匀通透，整体明亮但不过曝。 增强全局光反射，让空间更立体、有空气感。 阴影更柔顺自然，亮部细节保留、暗部更干净。 
【材质】 强化材质真实度达到照片级： 木纹 → 清晰、细腻、有真实粗糙度 石材 → 明显纹理、真实微凹凸 布料 → 有织物纤维感 金属 → 反射准确、清晰高光 纱帘 → 提升折射率、透光率、微表面散射效果，使透明度、模糊度与光衍射更真实；高光更准确、边缘更干净；呈现真实摄影中半透明物体的厚度感、层次感与光线穿透感。 大幅提升反射/粗糙度细节，使画面更逼真。 
【清晰度】 提升画面锐度与精细度 30~60%。 边缘清晰但不产生硬边。 去除噪点、模糊、AI伪影与瑕疵。 
【色彩】 白平衡校正为自然日光感。 色彩干净、纯净、无灰蒙雾感。 增强对比度与动态范围，使高光、暗部更有层次。 
【整体效果】 输出结果需达到 真实摄影棚级别的室内实拍照片： 光线自然 色彩真实 材质高级 半透明材质呈现真实光学效果 极强的空间通透感 画质明显提升 风格基准：真实摄影、3DMAX V-Ray/Corona 级真实感、商业级家装摄影、电影级光线质感


"""

# PROMPT = """

# You are given:
#   1. The original interior‐design image.
#   2. A pixel-accurate semantic-segmentation map.
#   3. (Optional) Furniture-only images.

# TASK  
# Enhance the image so it looks like a commercial-grade, studio-quality interior photograph while *strictly* preserving every object’s material, color, position, and the room’s geometry.

# MANDATORY CONSTRAINTS  
# • Never modify—even slightly—the material, color, scale, orientation, or placement of any furniture or architectural element.  
# • If an enhancement would violate the above, skip that enhancement and leave the affected pixels unchanged.

# DESIRED IMPROVEMENTS  
# 1. Lighting  
#    – Obey real-world optics: natural, even, and clean illumination.  
#    – No blown highlights; retain shadow detail.  
#    – If needed, raise global exposure for a soft, balanced look (no gray or milkiness).  
#    – Subtly emphasize the directionality of daylight from windows while keeping existing artificial-light characteristics.  
#    – Strengthen global light bounce to give the space an airy, open feel.

# 2. Micro-detail realism  
#    – Refine edge sharpness, water ripples, seams, and structural lines already present.  
#    – Remove noise, banding, stretching, warping, or any AI repaint artifacts.

# 3. Color fidelity  
#    – Apply a neutral daylight white balance; keep tones fresh and clean.  
#    – Absolutely no hue or saturation shift on furniture, finishes, or fixed elements.

# OUTPUT  
# Return only the enhanced image (no text, borders, or metadata changes).

# PRIORITY  
# Image integrity first, beautification second. If you cannot enhance without breaking the rules, output the original image unchanged.

# """



# PROMPT = "请为我严格按照语义分割图中的语义分割结果和主要家具图（如有）中的家具信息，\
# 在不改变原家装效果图任何一种家具的材质颜色和位置，也不改变原图空间结构的情况下，\
# 对我的原始家装图进行视觉效果的润色，使整体呈现更加自然。 \
# 输出效果需符合真实摄影的物理光照规律，光线自然、均匀、干净；亮部不过曝、暗部保留细节；\
# 必要时提升全局照度，让室内光线柔和，不偏灰或泛白；\
# 增强自然光方向性（窗外光柔和进入室内），并保留原场景光源特征；\
# 强化全局光照反射，让空间更通透；\
# 增强微小细节的真实感（边缘锐度、水纹、缝隙、结构线条）；\
# 优化色彩：白平衡偏自然日光色温，色调清爽干净；\
# 去除任何噪点、伪影、拉伸、变形或 AI 重绘痕迹；\
# 整体呈现专业设计摄影棚级别的真实成片效果，视觉质量达到商业级家装摄影标准。\
# 最后一定注意：这些改动都要以不改变图片中的任何家具材质细节为前提。  \
# 如果你的任何美化可能涉及到改变原图家具材质颜色或者空间位置，那么请放弃这个美化  \
# 保留原图不变第一，进行美化第二！\
# "


# PROMPT = """保持原图的镜头、构图、透视、空间结构完全不变，不重新布局，不新增或删除任何物体。
# 进行强增强处理，使画质有质的飞跃：

# 【光线】

# 增强自然光与环境光，让亮度更均匀通透，整体明亮但不过曝。
# 增强全局光反射，让空间更立体、有空气感。
# 阴影更柔顺自然，亮部细节保留、暗部更干净。

# 【材质】

# 强化材质真实度达到照片级：

# 木纹 → 清晰、细腻、有真实粗糙度

# 石材 → 明显纹理、真实微凹凸

# 布料 → 有织物纤维感

# 金属 → 反射准确、清晰高光

# 纱帘 → 提升折射率、透光率、微表面散射效果，使透明度、模糊度与光衍射更真实；高光更准确、边缘更干净；呈现真实摄影中半透明物体的厚度感、层次感与光线穿透感。

# 大幅提升反射/粗糙度细节，使画面更逼真。

# 【清晰度】

# 提升画面锐度与精细度 30~60%。
# 边缘清晰但不产生硬边。
# 去除噪点、模糊、AI伪影与瑕疵。

# 【色彩】

# 白平衡校正为自然日光感。
# 色彩干净、纯净、无灰蒙雾感。
# 增强对比度与动态范围，使高光、暗部更有层次。

# 【整体效果】

# 输出结果需达到 真实摄影棚级别的室内实拍照片：

# 光线自然

# 色彩真实

# 材质高级

# 半透明材质呈现真实光学效果

# 极强的空间通透感

# 画质明显提升

# 风格基准：真实摄影、3DMAX V-Ray/Corona 级真实感、商业级家装摄影、电影级光线质感。"""

# 初始化 Ark 客户端
_client = None



import re
from requests_toolbelt.multipart.encoder import MultipartEncoder
from urllib.parse import urlparse

def clean_file_extension(url: str) -> str:
    """从URL中提取干净的文件扩展名"""
    # 解析URL

    print(f'开始上传图片到七牛云服务器: {url}')
    parsed = urlparse(url)
    path = parsed.path
    
    # 获取文件名和扩展名
    filename = path.split('/')[-1]
    
    # 使用正则表达式提取扩展名
    match = re.search(r'\.([a-zA-Z0-9]+)(?:$|[?#])', filename)
    if match:
        return match.group(1).lower()
    return ""

def upload_image_to_server(image_url: str) -> str:
    try:
        # 1. 参数
        src_url = image_url
        upload_url = 'http://dev.api.jiazhuangwuyou.com/api/upload/file'
        folder = datetime.datetime.today().strftime('aiImage/%Y%m%d')

        print(f"开始下载文件: {src_url}")
        
        # 2. 下载 下载文件
        response = requests.get(src_url, timeout=30)
        response.raise_for_status()
        
        total_size = len(response.content)
        
        # 修复：从URL中URL中提取干净的文件名（去除查询参数）
        def get_clean_filename(url: str) -> str:
            """从URL中提取干净的文件名"""
            parsed = urlparse(url)
            path = parsed.path
            filename = path.split('/')[-1]
            
            # 如果文件名为空，生成一个默认名称
            if not filename:
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"image_{timestamp}.jpeg"
            
            return filename
        
        file_name = get_clean_filename(src_url)
        print(f"文件下载成功，大小: {total_size} bytes")
        print(f"处理后文件名: {file_name}")

        # 3. 创建 创建文件流
        file_stream = io.BytesIO(response.content)
        
        # 4. 确定 确定MIME类型
        def get_mime_type(filename: str) -> str:
            """根据文件扩展名确定MIME类型"""
            ext = filename.lower().split('.')[-1] if '.' in filename else ''
            mime_types = {
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'gif': 'image/gif',
                'webp': 'image/webp',
                'pdf': 'application/pdf',
                'json': 'application/json'
            }
            return mime_types.get(ext, 'application/octet-stream')
        
        mime_type = get_mime_type(file_name)
        
        # 5. 构造 构造 multipart/form-data
        m = MultipartEncoder(
            fields={
                'folder': folder,
                'file': (file_name, file_stream, mime_type)
            }
        )

        # 6. 准备请求头
        headers = {
            'Content-Type': m.content_type,
            'Authorization': 'Bearer b1689a87-9137-402b-8651-fa1434a39ee8',
        }
        
        print(f"开始上传到: {upload_url}")
        print(f"目标文件夹: {folder}")
        print(f"文件名: {file_name}")
        print(f"MIME类型: {mime_type}")
        
        # 7. 上传
        resp = requests.post(
            upload_url,
            data=m,
            headers=headers,
            timeout=(30, 300)
        )

        print('响应状态码:', resp.status_code)
        print('响应内容:', resp.text)
        
        resp.raise_for_status()
        
        # 8. 解析响应
        response_data = resp.json()
        print(f'七牛云服务器返回数据: {response_data}')
        if 'data' in response_data and resp.status_code == 200:
            uploaded_url = response_data['data']['url']
            print(f'上传成功!: {uploaded_url}')
            return uploaded_url
        else:
            error_msg = response_data.get('message', '未知错误')
            print(f'上传失败: {error_msg}')
            raise Exception(f"上传失败: {error_msg}")
            return None
        
    except requests.exceptions.HTTPError as e:
        status_code = getattr(e.response, 'status_code', '未知')
        print(f"HTTP错误 {status_code}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print("响应内容:", e.response.text)
    except Exception as e:
        print(f"发生错误: {e}")
        raise


def get_ark_client():
    """获取Ark客户端实例（单例模式）"""
    if not VOLCENGINE_SDK_AVAILABLE:
        raise ImportError("volcenginesdkarkruntime 未安装，无法使用AI图片生成功能。请运行: pip install volcenginesdkarkruntime")
    
    global _client
    if _client is None:
        _client = Ark(
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            api_key="4eb3bdb5-c394-4e38-a98a-c54af0648d38"
        )
    return _client


async def generate_images(
    image_urls: List[str],
    size: str = "2K",
    max_images: int = 4
) -> dict:
    """
    调用火山平台API生成图片
    
    Args:
        image_urls: 输入图片的URL列表
        size: 图片尺寸，默认"2K"
        max_images: 最多生成几张图，默认4
        
    Returns:
        dict: 包含生成的图片URL列表的字典，格式为 {"generated_images": ["url1", "url2", ...]}
        
    Raises:
        ImportError: 当volcenginesdkarkruntime未安装时
        ValueError: 当参数无效时
        Exception: 当API调用失败时
    """
    if not VOLCENGINE_SDK_AVAILABLE:
        raise ImportError("volcenginesdkarkruntime 未安装，无法使用AI图片生成功能。请运行: pip install volcenginesdkarkruntime")
    try:
        # 参数验证
        if not image_urls:
            raise ValueError("image_urls不能为空")
        
        if not isinstance(image_urls, list):
            raise ValueError("image_urls必须是列表类型")
        
        logger.info(f"开始生成图片，输入图片数量: {len(image_urls)}, 尺寸: {size}, 最大生成数: {max_images}")
        
        # 获取客户端并调用API
        client = get_ark_client()
        images_response = client.images.generate(
            model="doubao-seedream-4-0-250828",
            prompt=PROMPT,
            image=image_urls,
            size=size,
            sequential_image_generation="auto",
            sequential_image_generation_options=SequentialImageGenerationOptions(
                max_images=max_images
            ),
            response_format="url",
            watermark=False
        )
        


        # 提取图片URL
        urls = [img.url for img in images_response.data]
        

        # 提取火山返回的图片 URL
        volc_image_urls = urls
        print(f'火山返回图片数：{len(volc_image_urls)}')

        # 下载并上传到你自己的服务器
        uploaded_urls = []
        for url in volc_image_urls:
            uploaded_url = upload_image_to_server(url)
            print(f'上传到服务器图片URL：{uploaded_url}')
            uploaded_urls.append(uploaded_url)

        logger.info(f"图片生成成功，生成图片数量: {len(urls)}")
        logger.info(f'上传到服务器图片数：{len(uploaded_urls)}')
        return {"generated_images": uploaded_urls}
        
    except Exception as e:
        logger.error(f"图片生成失败: {e}", exc_info=True)
        raise


# curl -X POST http://10.0.4.12:7753/ai_generate \
#   -H "Content-Type: application/json" \
#   -d '{
#     "image_urls": [
#       "https://img2video.tos-cn-beijing.volces.com/test_img2img/8/2de3795ede3c85727ba6ac6ccc0e0457-1%E9%A4%90%E5%8E%85.jpg",
#       "https://img2video.tos-cn-beijing.volces.com/test_img2img/8/2de3795ede3c85727ba6ac6ccc0e0457-1%E9%A4%90%E5%8E%85channel.jpg",
#       "https://img2video.tos-cn-beijing.volces.com/test_img2img/8/image(1).png"
#     ]
#   }'