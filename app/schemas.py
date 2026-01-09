from pydantic import BaseModel, HttpUrl, Field, model_validator

from app.core.config import settings


class SpeechText(BaseModel):
    text: str
    voice: str


class MediaRequest(BaseModel):
    task_name: str = Field(..., pattern=r"^[a-zA-Z0-9_-]+$")
    video_blocks: dict[str, list[HttpUrl]] = Field(..., min_length=1)
    audio_blocks: dict[str, list[HttpUrl]] = Field(..., min_length=1)
    text_to_speech: list[SpeechText] = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_blocks(self):
        combinations = 1
        for block_name, urls in self.video_blocks.items():
            if not urls:
                raise ValueError(f"Video block {block_name} is empty")

            combinations *= len(urls)

        if combinations > settings.MAX_COMBINATIONS:
            raise ValueError(
                f"Too many combinations of videos: {combinations}. Max is {settings.MAX_COMBINATIONS}"
            )

        for block_name, urls in self.audio_blocks.items():
            if not urls:
                raise ValueError(f"Audio block {block_name} is empty")

        return self
