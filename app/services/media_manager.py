import logging
import re
import time
import hashlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class MediaManager:
    MIME_TO_EXT = {
        "video/mp4": ".mp4",
        "audio/mpeg": ".mp3",
    }

    def __init__(self, task_id: str):
        self.task_id = task_id

        self.base_dir = settings.TEMP_DIR.joinpath(f"task_{task_id}")
        self.video_dir = self.base_dir.joinpath("videos")
        self.audio_dir = self.base_dir.joinpath("audio")

        self.video_dir.mkdir(parents=True, exist_ok=True)
        self.audio_dir.mkdir(parents=True, exist_ok=True)

    def download_file(
        self, url: str, folder: Path, expected_mime: str
    ) -> tuple[str, Path]:

        start_time = time.perf_counter()
        file_hash = hashlib.md5(url.encode()).hexdigest()

        try:
            ext = self.MIME_TO_EXT[expected_mime]
        except KeyError:
            logger.error("Unsupported mime type %s", expected_mime)
            raise ValueError(f"No extension mapping for {expected_mime}")

        local_path = folder.joinpath(file_hash + ext)

        if local_path.exists():
            logger.info("%s already cached", local_path.name)
            return url, local_path

        try:
            with httpx.Client(timeout=60, follow_redirects=True) as client:
                with client.stream("GET", url) as response:
                    response.raise_for_status()

                    content_type = response.headers.get("Content-Type", "").lower()
                    if expected_mime not in content_type:
                        raise ValueError(
                            f"Expected mime type "
                            f"'{expected_mime}' but got "
                            f"'{content_type}'"
                        )

                    with open(local_path, "wb") as f:
                        for chunk in response.iter_bytes(
                            chunk_size=settings.CHUNK_SIZE
                        ):
                            f.write(chunk)

            logger.info(
                "Downloaded %s in %.2fs",
                local_path.name,
                time.perf_counter() - start_time,
            )
            return url, local_path

        except Exception as e:
            logger.error(f"Failed to download %s: %s", url, str(e))
            if local_path.exists():
                local_path.unlink()
            raise

    def prepare_media(
        self, video_blocks: dict[str, list[str]], audio_blocks: dict[str, list[str]]
    ) -> tuple[dict[str, list], list[str]]:
        start_time = time.perf_counter()
        unique_videos = {str(url) for block in video_blocks.values() for url in block}
        unique_audio = {str(url) for block in audio_blocks.values() for url in block}

        with ThreadPoolExecutor(max_workers=settings.MAX_DOWNLOAD_WORKERS) as executor:
            video_tasks = [
                executor.submit(self.download_file, url, self.video_dir, "video/mp4")
                for url in unique_videos
            ]
            audio_tasks = [
                executor.submit(self.download_file, url, self.audio_dir, "audio/mpeg")
                for url in unique_audio
            ]
            all_results = [f.result() for f in video_tasks + audio_tasks]

        mapping = dict(all_results)

        local_video = {
            name: [mapping[str(url)] for url in video_blocks[name]]
            for name in sorted(
                video_blocks.keys(), key=lambda x: int(re.search(r"\d+", x).group())
            )
        }
        local_audio = [mapping[str(url)] for url in unique_audio]

        logger.info(
            "Videos and audio for %s downloaded in %.2fs",
            self.task_id,
            time.perf_counter() - start_time,
        )
        return local_video, local_audio
