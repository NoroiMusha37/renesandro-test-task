import pytest
import shutil
from pathlib import Path
from app.core.config import settings

@pytest.fixture(autouse=True)
def cleanup_tmp():
    yield
    test_dir = Path(settings.TEMP_DIR)
    if test_dir.exists():
        shutil.rmtree(test_dir)
