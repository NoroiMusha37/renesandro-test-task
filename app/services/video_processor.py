import logging
import time
import subprocess
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


class VideoProcessor:
    def __init__(self, task_id: str):
        self.output_dir = settings.TEMP_DIR.joinpath(f"task_{task_id}", "results")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.video_width = settings.VIDEO_WIDTH
        self.video_height = settings.VIDEO_HEIGHT

    def render(
        self,
        video_lst: list[Path],
        music: Path,
        voiceover: Path,
        index: int,
        total_videos: int,
    ) -> Path:
        local_path = self.output_dir.joinpath(f"result_{index + 1}.mp4")
        start_time = time.perf_counter()

        inputs = []
        for video in video_lst:
            inputs.extend(["-i", str(video)])
        inputs.extend(["-stream_loop", "-1", "-i", str(music)])
        inputs.extend(["-i", str(voiceover)])

        n = len(video_lst)
        video_filters = ""
        concat_input = ""

        for i in range(n):
            video_filters += (
                f"[{i}:v]scale={self.video_width}:{self.video_height}:force_original_aspect_ratio=decrease,"
                f"pad={self.video_width}:{self.video_height}:(ow-iw)/2:(oh-ih)/2,"
                f"setsar=1,fps=30,format=yuv420p[v{i}];"
            )
            concat_input += f"[v{i}]"

        filter_str = (
            f"{video_filters}"
            f"{concat_input}concat=n={n}:v=1:a=0[v];"
            f"[{n}:a]aresample=44100,volume=0.2[m];"
            f"[{n+1}:a]aresample=44100,volume=1.0[vo];"
            f"[m][vo]amix=inputs=2:duration=first[a]"
        )

        command = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            *inputs,
            "-filter_complex",
            filter_str,
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-c:v",
            "libx264",
            "-crf",
            "28",
            "-c:a",
            "aac",
            "-preset",
            "veryfast",
            "-shortest",
            str(local_path),
        ]

        try:
            subprocess.run(command, capture_output=True, text=True, check=True)
            logger.info(
                "Finished rendering [%s/%s] video in %.2fs",
                index + 1,
                total_videos,
                time.perf_counter() - start_time,
            )
            return local_path
        except subprocess.CalledProcessError as e:
            logger.error("Failed to render %s: %s", index, e.stderr)
            raise
