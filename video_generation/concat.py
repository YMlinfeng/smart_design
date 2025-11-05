from moviepy.editor import VideoFileClip, concatenate_videoclips

# 输入和输出文件路径
input_file = "/root/autodl-tmp/video_generation/生成的视频/video_cgt-20251105120728-r6bzh.mp4"     # 原始视频文件名
output_file = "output_looped1.mp4"  # 输出文件名

# 加载视频
clip = VideoFileClip(input_file)

# 将视频重复三次
looped_clip = concatenate_videoclips([clip] * 3)

# 导出视频
looped_clip.write_videofile(output_file, codec="libx264", audio_codec="aac")