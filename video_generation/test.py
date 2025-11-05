import os
# Install SDK:  pip install 'volcengine-python-sdk[ark]' .
from volcenginesdkarkruntime import Ark 

os.environ['ARK_API_KEY'] = '13435882-85a3-4a62-8655-670ff4242ec8'

# 初始化Ark客户端
client = Ark(
    # The base URL for model invocation .
    base_url="https://ark.cn-beijing.volces.com/api/v3", 
    # Get API Key：https://console.volcengine.com/ark/region:ark+cn-beijing/apikey
    api_key=os.getenv('ARK_API_KEY'), 
)

print("----- create request -----")
# 创建视频生成任务
create_result = client.content_generation.tasks.create(
    # Replace with Model ID .
    model="doubao-seedance-1-0-pro-250528", 
    content=[
        {
            # 文本提示词与参数组合
            "type": "text",
            "text": "让参考图像中的黄色河流沿着轨迹向屋内流动，幅度不要太大，我将来要循环播放这段视频，所以首尾是相同的，但是你要为我生成不相同的中间帧，并且帧间的连接和过渡要平滑和自然。千万注意：我的参考图像的首尾帧是相同的，但是你一定要给我做出动态效果，千万不要生成静止的视频，你可以先变化过去再变化回来，但是一定要动态，不要因为首尾帧相同就生成静态视频  --resolution 480p  --duration 3 --camerafixed true --watermark false"
        },
        {
            # 首帧图片URL
            "type": "image_url",
            "image_url": {
                "url": "https://img2video.tos-cn-beijing.volces.com/%E5%8A%A0%E8%BD%BD%E9%A1%B5.png"
            },
            "role": "first_frame"
        },
        {
            # 尾帧图片URL
            "type": "image_url",
            "image_url": {
                "url": "https://img2video.tos-cn-beijing.volces.com/%E5%8A%A0%E8%BD%BD%E9%A1%B5.png"
            },
            "role": "last_frame"
        }
    ]
)
print(create_result)


print("----- get request -----")
# 获取任务详情
get_result = client.content_generation.tasks.get(task_id=create_result.id)
print(get_result)


print("----- list request -----")
# 列出符合特定条件的任务
list_result = client.content_generation.tasks.list(
    page_num=1,
    page_size=10,
    status="queued",  # 按状态筛选, e.g succeeded, failed, running, cancelled
    # model="<YOUR_MODEL_EP>", # 按 ep 筛选
    # task_ids=["test-id-1", "test-id-2"] # 按 task_id 筛选
)
print(list_result)


print("----- delete request -----")
# 通过任务 id 删除任务
try:
    client.content_generation.tasks.delete(task_id=create_result.id)
    print(create_result.id)
except Exception as e:
    print(f"failed to delete task: {e}")