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

    def render(self, video_lst: list[Path], music: Path, voiceover: Path, index: int) -> Path:
        local_path = self.output_dir.joinpath(f"result_{index}.mp4")
        start_time = time.perf_counter()

        inputs = []
        for video in video_lst:
            inputs.extend(["-i", str(video)])
        inputs.extend(["-stream_loop", "-1", "-i", str(music)])
        inputs.extend(["-i", str(voiceover)])

        n = len(video_lst)
        video_map = "".join([f"[{i}:v]" for i in range(n)])

        filter_str = (
            f"{video_map}concat=n={n}:v=1:a=0[v];"
            f"[{n}:a]volume=0.2[m];"
            f"[{n+1}:a]volume=1.0[vo];"
            f"[m][vo]amix=inputs=2:duration=shortest[a]"
        )

        command = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            *inputs,
            "-filter_complex", filter_str,
            "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-crf", "23",
            "-c:a", "aac", "-preset", "fast",
            "-shortest", str(local_path)
        ]

        try:
            subprocess.run(command, capture_output=True, text=True, check=True)
            logger.info("Finished rendering %s in %.2fs", index, time.perf_counter() - start_time)
            return local_path
        except subprocess.CalledProcessError as e:
            logger.error("Failed to render %s: %s", index, e.stderr)
            raise
