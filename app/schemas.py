from pydantic import BaseModel, HttpUrl, Field, model_validator


class SpeechText(BaseModel):
    text: str
    voice: str


class MediaRequest(BaseModel):
    task_name: str
    video_blocks: dict[str, list[HttpUrl]] = Field(..., min_length=1)
    audio_blocks: dict[str, list[HttpUrl]] = Field(..., min_length=1)
    text_to_speech: list[SpeechText] = Field(..., min_length=1)

    @model_validator(mode="after")
    def check_blocks(self):
        for block, urls in self.video_blocks.items():
            if not urls:
                raise ValueError(f"Video block {block} is empty")

        for block, urls in self.audio_blocks.items():
            if not urls:
                raise ValueError(f"Audio block {block} is empty")

        return self
