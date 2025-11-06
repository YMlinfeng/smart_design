from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List
from volcenginesdkarkruntime import Ark
from volcenginesdkarkruntime.types.images.images import SequentialImageGenerationOptions
import os

PROMPT = "请为我严格按照语义分割图中的语义分割结果和主要家具图（如有）中的家具信息，在不改变原家装效果图任何一种家具的材质颜色和位置，也不改变原图空间结构的情况下，改善室内的环境光为明亮且柔和的光效。也即，除了改变室内光线为明亮，柔和光之外，不改变图片中的任何原有细节（颜色，空间位置等）"

# 初始化 Ark 客户端
client = Ark(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key=os.getenv("ARK_API_KEY")
    # api_key="4eb3bdb5-c394-4e38-a98a-c54af0648d38"
)

app = FastAPI()

# 定义输入参数格式
class GenerateRequest(BaseModel):
    # prompt: str                  # 文本提示词
    image_urls: List[str]        # 输入图片的 URL 列表
    # max_images: int = 4          # 最多生成几张图（默认是 4）
    size: str = "2K"             # 图片尺寸（默认是 2K） #todo

# 定义返回格式
class GenerateResponse(BaseModel):
    generated_images: List[str]

@app.post("/generate-image", response_model=GenerateResponse)
async def generate_image(req: GenerateRequest):
    # 调用火山平台
    imagesResponse = client.images.generate(
        model="doubao-seedream-4-0-250828",
        prompt=PROMPT,
        image=req.image_urls,
        size=req.size,
        sequential_image_generation="auto",
        sequential_image_generation_options=SequentialImageGenerationOptions(
            max_images=req.max_images
        ),
        response_format="url",
        watermark=False
    )

    # 提取图片 URL
    urls = [img.url for img in imagesResponse.data]

    # 返回给后端
    return {"generated_images": urls}


# uvicorn main:app --host 0.0.0.0 --port 8000


# curl -X POST http://172.17.0.3:8000/generate-image \
#   -H "Content-Type: application/json" \
#   -d '{
#     "image_urls": [
#       "https://img2video.tos-cn-beijing.volces.com/test_img2img/8/2de3795ede3c85727ba6ac6ccc0e0457-1%E9%A4%90%E5%8E%85.jpg",
#       "https://img2video.tos-cn-beijing.volces.com/test_img2img/8/2de3795ede3c85727ba6ac6ccc0e0457-1%E9%A4%90%E5%8E%85channel.jpg",
#       "https://img2video.tos-cn-beijing.volces.com/test_img2img/8/image(1).png"
#     ]
#   }'