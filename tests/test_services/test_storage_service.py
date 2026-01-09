import pytest
from pathlib import Path
from app.services.storage_service import StorageService


@pytest.fixture(autouse=True)
def reset_storage_state():
    StorageService._client = None
    yield


def test_upload_file_success(mocker, tmp_path):
    local_file = tmp_path / "video.mp4"
    local_file.write_text("fake video data")

    mock_client = mocker.patch.object(StorageService, "client")
    mock_bucket = mocker.MagicMock()
    mock_blob = mocker.MagicMock()

    mock_client.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob

    service = StorageService()
    remote_path = "uploads/video_1.mp4"

    result = service.upload_file(local_file, remote_path)

    assert result == remote_path
    mock_bucket.blob.assert_called_once_with(remote_path)
    mock_blob.upload_from_filename.assert_called_once_with(str(local_file))

    assert not local_file.exists()


def test_upload_file_error(mocker, tmp_path):
    local_file = tmp_path / "fail.mp4"
    local_file.write_text("data")

    mock_client = mocker.patch.object(StorageService, "client")
    mock_client.bucket.side_effect = Exception("GCS connection lost")

    service = StorageService()

    with pytest.raises(Exception, match="GCS connection lost"):
        service.upload_file(local_file, "remote.mp4")

    assert local_file.exists()
