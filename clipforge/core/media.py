"""FFmpeg media processing utilities for ClipForge."""

from dataclasses import dataclass
import json
from pathlib import Path
import shutil
import subprocess
from typing import Optional


@dataclass
class VideoMetadata:
    """Metadata for an input video file."""
    path: Path
    duration: float
    width: int
    height: int
    fps: float
    has_audio: bool


class MediaProcessor:
    """Handles low-level video and audio manipulation via FFmpeg."""

    def __init__(self, ffmpeg_bin: Optional[str] = None):
        self.ffmpeg_bin = ffmpeg_bin or shutil.which("ffmpeg") or "ffmpeg"
        self.ffprobe_bin = shutil.which("ffprobe") or "ffprobe"

    def probe(self, video_path: Path) -> VideoMetadata:
        """Inspect video dimensions, duration, and stream properties."""
        cmd = [
            self.ffprobe_bin,
            "-v", "error",
            "-show_entries", "format=duration:stream=width,height,r_frame_rate,codec_type",
            "-of", "json",
            str(video_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)

        duration = float(data.get("format", {}).get("duration", 0.0))
        streams = data.get("streams", [])

        width, height, fps = 1920, 1080, 30.0
        has_audio = False

        for stream in streams:
            if stream.get("codec_type") == "video":
                width = int(stream.get("width", 1920))
                height = int(stream.get("height", 1080))
                fps_str = stream.get("r_frame_rate", "30/1")
                if "/" in fps_str:
                    num, den = fps_str.split("/")
                    fps = float(num) / max(float(den), 1.0)
                else:
                    fps = float(fps_str)
            elif stream.get("codec_type") == "audio":
                has_audio = True

        return VideoMetadata(
            path=video_path,
            duration=duration,
            width=width,
            height=height,
            fps=fps,
            has_audio=has_audio,
        )

    def extract_audio(self, video_path: Path, output_audio: Path) -> Path:
        """Extract high-quality 16kHz mono audio optimized for speech recognition."""
        output_audio.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            self.ffmpeg_bin,
            "-y",
            "-i", str(video_path),
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            str(output_audio),
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        return output_audio

    def cut_and_crop_916(
        self,
        video_path: Path,
        start_time: float,
        end_time: float,
        crop_x: int,
        output_video: Path,
        subtitle_file: Optional[Path] = None,
    ) -> Path:
        """Cut a segment and reframe to 9:16 vertical (1080x1920) with optional subtitle burning."""
        output_video.parent.mkdir(parents=True, exist_ok=True)
        duration = end_time - start_time

        # Calculate 9:16 target dimensions based on source height
        # Typically for 1080p source: width 1080, height 1920
        # If cropping from 16:9 (1920x1080): target width is (1080 * 9 / 16) = 607.5 -> rounded to 608
        filter_complex = f"crop=ih*(9/16):ih:{crop_x}:0,scale=1080:1920"

        if subtitle_file and subtitle_file.exists():
            # Escape path for FFmpeg filter syntax
            escaped_sub = str(subtitle_file).replace("\\", "/").replace(":", "\\:")
            filter_complex += f",subtitles='{escaped_sub}'"

        cmd = [
            self.ffmpeg_bin,
            "-y",
            "-ss", f"{start_time:.3f}",
            "-t", f"{duration:.3f}",
            "-i", str(video_path),
            "-vf", filter_complex,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "19",
            "-c:a", "aac",
            "-b:a", "192k",
            str(output_video),
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        return output_video
