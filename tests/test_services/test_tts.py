import pytest
import hashlib
from app.services.tts import TTS


@pytest.fixture(autouse=True)
def reset_tts_state():
    TTS.voices = {}
    TTS._client = None
    yield


def test_refresh_voice_map(mocker):
    mock_el = mocker.patch("app.services.tts.ElevenLabs")

    mock_voice = mocker.MagicMock()
    mock_voice.name = "Rachel - calm & quiet"
    mock_voice.voice_id = "rachel_id"

    mock_el.return_value.voices.get_all.return_value.voices = [mock_voice]

    tts = TTS("test")
    tts._refresh_voice_map()

    assert TTS.voices["rachel - calm & quiet"] == "rachel_id"
    assert TTS.voices["rachel"] == "rachel_id"


def test_generate_voiceover_cache(mocker):
    TTS.voices = {"rachel": "rachel_id"}
    tts = TTS("test_cache")

    v_hash = hashlib.md5(b"Hello|rachel_id").hexdigest()
    fake_file = tts.tts_dir / f"{v_hash}.mp3"
    fake_file.write_text("audio content")

    mock_convert = mocker.patch.object(tts.client.text_to_speech, "convert")

    path = tts.generate_voiceover("Hello", "rachel")

    assert path == fake_file
    mock_convert.assert_not_called()


def test_generate_voiceover_success(mocker):
    TTS.voices = {"adam": "adam_id"}
    tts = TTS("test_gen")

    mock_convert = mocker.patch.object(tts.client.text_to_speech, "convert", return_value=b"audio_data")
    mock_save = mocker.patch("app.services.tts.save")

    path = tts.generate_voiceover("Hi", "adam")

    assert path.suffix == ".mp3"
    mock_convert.assert_called_once()
    mock_save.assert_called_once()
