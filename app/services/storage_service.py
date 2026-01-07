import logging
from pathlib import Path

from google.cloud import storage
from google.oauth2 import service_account

from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(self):
        self.bucket_name = settings.GCS_BUCKET_NAME
        try:
            credentials = service_account.Credentials.from_service_account_info(settings.gcs_credentials)
            self.client = storage.Client(credentials=credentials)
            logger.info("GCS client initialized. Bucket: %s", self.bucket_name)
        except Exception as e:
            logger.error("Failed to initialize GCS client: %s", e)
            raise

    def upload_file(self, local_path: Path, remote_path: str) -> str:
        try:
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(remote_path)

            logger.info("Uploading %s to GCS", local_path.name)

            blob.upload_from_filename(str(local_path))
            gcs_url = f"gs://{self.bucket_name}/{remote_path}"

            logger.info("Successfully uploaded to %s", gcs_url)
            return gcs_url
        except Exception as e:
            logger.error("Failed to upload %s: %s", local_path.name, e)
            raise
