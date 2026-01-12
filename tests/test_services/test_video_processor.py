import pytest
import subprocess
from pathlib import Path
from app.services.video_processor import VideoProcessor


def test_render_command_construction(mocker):
    vp = VideoProcessor("test_render")

    mock_run = mocker.patch("subprocess.run")

    video_list = [Path("v1.mp4"), Path("v2.mp4")]
    music = Path("music.mp3")
    voiceover = Path("vo.mp3")
    index = 0
    total_videos = 10

    vp.render(video_list, music, voiceover, index, total_videos)

    args, kwargs = mock_run.call_args
    command = args[0]

    assert command[0] == "ffmpeg"
    assert "-filter_complex" in command
    assert "-shortest" in command
    assert str(vp.output_dir.joinpath("result_1.mp4")) in command

    for video in video_list:
        assert str(video) in command
    assert str(music) in command
    assert str(voiceover) in command


def test_render_success_return_path(mocker):
    vp = VideoProcessor("test_path")
    mocker.patch("subprocess.run")

    result_path = vp.render([Path("v.mp4")], Path("m.mp3"), Path("vo.mp3"), 5, 10)

    assert result_path.name == "result_6.mp4"
    assert isinstance(result_path, Path)


def test_render_error_handling(mocker):
    vp = VideoProcessor("test_fail")

    mock_run = mocker.patch("subprocess.run")
    mock_run.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd="ffmpeg", stderr="FFmpeg configuration error"
    )

    with pytest.raises(subprocess.CalledProcessError):
        vp.render([Path("v.mp4")], Path("m.mp3"), Path("vo.mp3"), 0, 10)
