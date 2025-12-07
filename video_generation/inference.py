import os
import time
import requests
# 安装依赖：pip install 'volcengine-python-sdk[ark]' requests
from volcenginesdkarkruntime import Ark

# -------------------------- 配置参数（根据你的需求修改）--------------------------
os.environ['ARK_API_KEY'] = '13435882-85a3-4a62-8655-670ff4242ec8'  # 你的真实API密钥，注意不要泄漏，该API已失效
SAVE_FOLDER = "./生成的视频"  # 本地保存路径
POLL_INTERVAL = 10  # 轮询间隔（教程用10秒，保持一致）
TIMEOUT = 300  # 超时时间（5分钟）
# --------------------------------------------------------------------------------

# 初始化客户端
client = Ark(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key=os.getenv('ARK_API_KEY'),
)

# 创建保存文件夹
os.makedirs(SAVE_FOLDER, exist_ok=True)

def create_video_task():
    """创建视频生成任务"""
    print("----- 开始创建视频生成任务 -----")
    try:
        create_result = client.content_generation.tasks.create(
            model="doubao-seedance-1-0-pro-250528",
            content=[
                {
                    "type": "text",
                    # "text": "让参考图像中的黄色河流沿着轨迹向屋内流动，幅度不要太大，除了黄色河流的流动外视频中的其他家具均不要产生移动。注意只是黄色河流十分缓慢地向屋内流动，不要产生夸张的黄色团块等违反物理常识的不明物体。我将来要循环播放这段视频，所以首尾是相同的，但是你要为我生成不相同的中间帧，并且帧间的连接和过渡要平滑和自然。千万注意：我的参考图像的首尾帧是相同的，但是你一定要给我做出动态效果，千万不要生成静止的视频，你可以先变化过去再变化回来，但是一定要动态，不要因为首尾帧相同就生成静态视频  --resolution 480p  --duration 5 --camerafixed true --watermark false"
                    "text": "让参考图像中的黄色河流沿着轨迹向屋内缓慢流动，除了黄色河流的流动外视频中的其他家具均不要产生移动，画面中也不要出现新的元素。  --resolution 480p  --duration 5 --camerafixed true --watermark false"
                },
                {
                    "type": "image_url",
                    "image_url": {"url": "https://img2video.tos-cn-beijing.volces.com/%E5%8A%A0%E8%BD%BD%E9%A1%B5.png"},
                    "role": "first_frame"
                },
                {
                    "type": "image_url",
                    "image_url": {"url": "https://img2video.tos-cn-beijing.volces.com/%E5%8A%A0%E8%BD%BD%E9%A1%B5.png"},
                    "role": "last_frame"
                }
            ]
        )
        print(f"任务创建成功！任务ID：{create_result.id}")
        return create_result.id
    except Exception as e:
        print(f"任务创建失败：{e}")
        exit(1)

def wait_for_task_complete(task_id):
    """轮询等待任务完成，从 content.video_url 提取下载链接（按教程结构修正）"""
    print(f"\n----- 等待任务 {task_id} 生成完成（超时时间：{TIMEOUT}秒）-----")
    start_time = time.time()
    
    while True:
        if time.time() - start_time > TIMEOUT:
            print(f"任务超时（超过{TIMEOUT}秒）")
            return None
        
        try:
            task_result = client.content_generation.tasks.get(task_id=task_id)
            status = task_result.status
            print(f"当前任务状态：{status}")
            
            if status == "succeeded":
                print("----- 任务成功，提取视频链接 -----")
                # 关键修正：按教程结构，视频URL在 task_result.content.video_url
                if hasattr(task_result, 'content') and hasattr(task_result.content, 'video_url'):
                    video_url = task_result.content.video_url
                    print(f"获取到视频URL：{video_url}")
                    return video_url
                else:
                    # 若结构不一致，打印完整结果供调试
                    print("警告：未找到 content.video_url，完整任务结果如下：")
                    print(task_result)
                    return None
            
            elif status in ["failed", "cancelled"]:
                # 按教程结构，错误信息在 task_result.error
                error_msg = task_result.error if hasattr(task_result, 'error') else "未知错误"
                print(f"任务失败/取消，原因：{error_msg}")
                return None
            
            else:
                time.sleep(POLL_INTERVAL)
        
        except Exception as e:
            print(f"查询任务状态失败：{e}")
            time.sleep(POLL_INTERVAL)

def download_video(video_url, save_path):
    """下载视频到本地（不变）"""
    print(f"\n----- 开始下载视频：{video_url} -----")
    try:
        response = requests.get(video_url, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        print(f"视频下载成功！保存路径：{save_path}")
        return True
    except Exception as e:
        print(f"视频下载失败：{e}")
        return False

if __name__ == "__main__":
    # 1. 创建任务
    task_id = create_video_task()
    
    # 2. 等待完成并获取URL（核心修正部分）
    video_url = wait_for_task_complete(task_id)
    if not video_url:
        exit(1)
    
    # 3. 下载保存
    video_filename = f"video_{task_id}.mp4"
    save_path = os.path.join(SAVE_FOLDER, video_filename)
    download_video(video_url, save_path)
