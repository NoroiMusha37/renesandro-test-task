import pytest
from app.services.media_manager import MediaManager


def test_download_file_success(mocker):
    mm = MediaManager("test_task")

    mock_client = mocker.MagicMock()

    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "video/mp4"}
    mock_response.iter_bytes.return_value = [b"video_chunk_1", b"video_chunk_2"]

    mock_client.stream.return_value.__enter__.return_value = mock_response

    url = "https://example.com/video.mp4"
    _, local_path, size = mm.download_file(
        url, mm.video_dir, "video/mp4", mock_client
    )

    assert local_path.exists()
    assert local_path.suffix == ".mp4"
    assert size > 0
    mock_client.stream.assert_called_once_with("GET", url, follow_redirects=True)
