from moviepy.editor import VideoFileClip, vfx

# 输入与输出文件名
input_file = "/root/autodl-tmp/video_generation/output_looped.mp4"       # 你要慢放的视频
output_file = "output_slowed.mp4"      # 输出慢放后的视频

# 加载视频
clip = VideoFileClip(input_file)

# 调整为原速度的 0.5 倍
slowed_clip = clip.fx(vfx.speedx, 0.5)

# 导出结果
slowed_clip.write_videofile(output_file, codec="libx264", audio_codec="aac")