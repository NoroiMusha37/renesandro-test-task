import itertools
import logging
import random
import shutil
import time
from pathlib import Path

from celery import shared_task, chain, chord

from app.core.config import settings
from app.services.media_manager import MediaManager
from app.services.storage_service import StorageService
from app.services.tts import TTS
from app.services.video_processor import VideoProcessor

logger = logging.getLogger(__name__)


@shared_task
def render_task(params: dict):
    video_processor = VideoProcessor(params["task_id"])
    local_path = video_processor.render(
        video_lst=[Path(video) for video in params["video_lst"]],
        music=Path(params["music"]),
        voiceover=Path(params["voiceover"]),
        index=params["index"],
    )

    return str(local_path)


@shared_task
def upload_task(video_path: str, task_name: str, index: int):
    gcs = StorageService()
    remote_path = f"{task_name}/video_{index}.mp4"
    local_path = Path(video_path)

    try:
        gcs_url = gcs.upload_file(local_path, remote_path)
        if local_path.exists():
            local_path.unlink()
        return gcs_url
    except Exception as e:
        logger.error("Upload failed: %s", e)
        raise


@shared_task
def cleanup_task(results, task_id: str, start_time):
    work_dir = Path(settings.TEMP_DIR).joinpath(f"task_{task_id}")
    if work_dir.exists():
        shutil.rmtree(work_dir)
    logger.info("Task ended in %.2fs", time.time() - start_time)


@shared_task(bind=True)
def orchestrator(self, data: dict):
    task_id = self.request.id
    task_name = data["task_name"]

    logger.info("Starting processing media: %s", task_name)
    start_time = time.time()

    try:
        media_manager = MediaManager(task_id)
        video_blocks, audio_list = media_manager.prepare_media(
            video_blocks=data["video_blocks"], audio_blocks=data["audio_blocks"]
        )
        video_combinations = list(itertools.product(*video_blocks.values()))

        tts = TTS(task_id)
        voiceover_list = tts.prepare_voiceovers(data["text_to_speech"])

        job_chains = []
        for i, comb in enumerate(video_combinations):
            render_params = {
                "task_id": task_id,
                "video_lst": [str(path) for path in comb],
                "music": str(random.choice(audio_list)),
                "voiceover": str(random.choice(voiceover_list)),
                "index": i,
            }

            c = chain(
                render_task.s(render_params).set(queue="heavy"),
                upload_task.s(task_name, i).set(queue="light"),
            )
            job_chains.append(c)

        workflow = chord(job_chains)(
            cleanup_task.s(task_id, start_time).set(queue="light")
        )

        return {
            "task_id": task_id,
            "status": "processing",
            "total_combinations": len(video_combinations),
        }
    except Exception:
        cleanup_task.delay(None, task_id, start_time).set(queue="light")
        raise
