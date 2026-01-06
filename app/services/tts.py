import hashlib
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app.core.config import settings
from elevenlabs import ElevenLabs, save

logger = logging.getLogger(__name__)


class TTS:
    def __init__(self, task_id: str):
        self.client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
        self.tts_dir = Path(settings.TEMP_DIR).joinpath(f"task_{task_id}", "tts")
        self.tts_dir.mkdir(parents=True, exist_ok=True)
        self.voices = {}

    def _refresh_voice_map(self):
        try:
            response = self.client.voices.get_all()
            self.voices = {voice.name: voice.voice_id for voice in response.voices}
            logger.info("Voice map refreshed, loaded %s voices", len(self.voices))
        except Exception as e:
            logger.error("Failed to refresh voice map: %s", str(e))
            raise

    def generate_voiceover(self, text: str, voice_name: str) -> Path:
        voice_id = self.voices.get(voice_name)
        if not voice_id:
            logger.info("Voice '%s' not in cache, retrying...", voice_name)
            self._refresh_voice_map()
            voice_id = self.voices.get(voice_name)

        if not voice_id:
            raise ValueError(f"Voice '{voice_name}' is not available")

        start_time = time.perf_counter()
        voiceover_hash = hashlib.md5(f"{text}|{voice_id}".encode()).hexdigest()
        local_path = self.tts_dir.joinpath(f"{voiceover_hash}.mp3")

        if local_path.exists():
            return local_path

        try:
            audio = self.client.text_to_speech(
                text=text, voice_id=voice_id, model="eleven_multilingual_v1"
            )
            save(audio, str(local_path))

            logger.info(
                "Voiceover for %s generated in %.2fs",
                voice_name,
                time.perf_counter() - start_time,
            )
            return local_path
        except Exception as e:
            logger.error("Failed to generate voiceover: %s", str(e))
            if local_path.exists():
                local_path.unlink()
            raise

    def prepare_voiceovers(self, tts_items: list[dict]):
        start_time = time.perf_counter()

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(self.generate_voiceover, item["text"], item["voice"])
                for item in tts_items
            ]
            local_tts = [f.result() for f in futures]

        logger.info(
            "Generated %s voiceovers in %.2fs",
            len(local_tts),
            time.perf_counter() - start_time,
        )
        return local_tts
