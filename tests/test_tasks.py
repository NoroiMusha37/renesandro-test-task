import pytest
from pathlib import Path
from app.tasks import render_task, upload_task, cleanup_task


def test_render_task_logic(mocker):
    mock_vp = mocker.patch("app.tasks.VideoProcessor")
    mock_instance = mock_vp.return_value
    expected_path = Path("/tmp/result.mp4")
    mock_instance.render.return_value = expected_path

    params = {
        "task_id": "123",
        "video_lst": ["v1.mp4"],
        "music": "m.mp3",
        "voiceover": "vo.mp3",
        "index": 0,
        "total_videos": 10,
    }

    result = render_task(params)
    assert Path(result).as_posix() == expected_path.as_posix()


def test_upload_task_logic(mocker):
    mock_storage = mocker.patch("app.tasks.StorageService")
    mock_instance = mock_storage.return_value
    mock_instance.upload_file.return_value = "remote/path.mp4"

    fake_path = Path("test_video.mp4")
    fake_path.touch()

    result = upload_task(str(fake_path), "test_task", 1)

    assert result == "remote/path.mp4"
    assert not fake_path.exists()


def test_cleanup_task(mocker, tmp_path):
    mock_settings = mocker.patch("app.tasks.settings")
    mock_settings.TEMP_DIR = tmp_path

    task_dir = tmp_path / "task_123"
    task_dir.mkdir(parents=True, exist_ok=True)

    cleanup_task(None, "123", 0)
    assert not task_dir.exists()
