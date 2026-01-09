import hashlib
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app.core.config import settings
from elevenlabs import ElevenLabs, save

logger = logging.getLogger(__name__)


class TTS:
    voices = {}
    _client = None

    def __init__(self, task_id: str):
        self.tts_dir = settings.TEMP_DIR.joinpath(f"task_{task_id}", "tts")
        self.tts_dir.mkdir(parents=True, exist_ok=True)

    @property
    def client(self):
        if not TTS._client:
            TTS._client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
        return TTS._client

    def _refresh_voice_map(self):
        if TTS.voices:
            logger.info("Using cached voice map")
            return
        try:
            response = self.client.voices.get_all()
            new_voices = {}
            for voice in response.voices:
                short_name = voice.name.split()[0].lower()

                if short_name not in new_voices:
                    new_voices[short_name] = voice.voice_id

                new_voices[voice.name.lower()] = voice.voice_id

            TTS.voices = new_voices

            logger.info("Voice map refreshed, loaded %s voices", len(self.voices))
        except Exception as e:
            logger.error("Failed to refresh voice map: %s", str(e))
            raise

    def generate_voiceover(self, text: str, voice_name: str) -> Path:
        voice_id = TTS.voices.get(voice_name.lower())

        if not voice_id:
            raise ValueError(f"Voice '{voice_name}' is not available")

        start_time = time.perf_counter()
        voiceover_hash = hashlib.md5(f"{text}|{voice_id}".encode()).hexdigest()
        local_path = self.tts_dir.joinpath(f"{voiceover_hash}.mp3")

        if local_path.exists():
            logger.info("Using cached voiceover")
            return local_path

        try:
            audio = self.client.text_to_speech.convert(
                text=text, voice_id=voice_id, model_id="eleven_multilingual_v2"
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

        logger.info("Updating voice map...")
        self._refresh_voice_map()

        with ThreadPoolExecutor(max_workers=settings.MAX_WORKERS_FOR_TTS) as executor:
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
