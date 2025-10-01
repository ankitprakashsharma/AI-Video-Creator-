# modules/video_composer_music.py
from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    concatenate_videoclips,
    CompositeAudioClip,
    TextClip,
    CompositeVideoClip,
)
from moviepy.audio.fx.volumex import volumex as audio_volumex
import os
import re

def compose_video_with_music(
    video_path: str,
    timestamps_dict: dict,
    music_path: str | None,
    script_text: str,
    output_name: str | None = None,
) -> str:
    video = VideoFileClip(video_path)
    clips = []

    # Clip video according to timestamps
    for pid, pairs in timestamps_dict.items():
        for s, e in pairs:
            s = max(0, s)
            e = min(e, video.duration)
            if e - s <= 0.15:
                continue
            try:
                sub = video.subclip(s, e)
                clips.append(sub)
            except Exception:
                continue

    if not clips:
        clips = [video.subclip(0, min(5, video.duration))]

    video_clip = concatenate_videoclips(clips, method="compose")
    music = None
    text_clips = []

    try:
        # Add music
        if music_path and os.path.exists(music_path):
            music = audio_volumex(AudioFileClip(music_path), 0.2)
            if music.duration < video_clip.duration:
                from moviepy.video.fx.all import loop as vfx_loop
                music = music.fx(vfx_loop, duration=video_clip.duration)
            video_clip.audio = music.set_duration(video_clip.duration)

        # Add text overlays
        if script_text:
            # Clean and split script into lines
            lines = [line.strip() for line in re.split('[\n.!?]', script_text) if line.strip()]
            if lines:
                duration_per_line = video_clip.duration / len(lines)
                start_time = 0
                for line in lines:
                    txt_clip = (
                        TextClip(
                            line,
                            fontsize=24,
                            color='white',
                            font='Arial-Bold',
                            stroke_color='black',
                            stroke_width=1,
                        )
                        .set_position(("center", "bottom"))
                        .set_duration(duration_per_line)
                        .set_start(start_time)
                    )
                    text_clips.append(txt_clip)
                    start_time += duration_per_line

        # Composite video with text
        final_clip = CompositeVideoClip([video_clip] + text_clips)
        final_clip.audio = video_clip.audio

        output_name = output_name or f"final_{os.path.basename(video_path).split('.')[0]}.mp4"
        out_path = os.path.join("static/uploads", output_name)
        final_clip.write_videofile(
            out_path,
            codec="libx264",
            audio_codec="aac",
            threads=2,
            logger=None,
            remove_temp=True,
        )
        return out_path
    finally:
        # Clean up moviepy resources
        video.close()
        video_clip.close()
        if music:
            music.close()
        if final_clip:
            final_clip.close()
