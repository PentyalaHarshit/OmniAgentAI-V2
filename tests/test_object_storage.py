import pytest

from tools.object_storage import LocalObjectStorage, build_object_storage
from tools.upload_manager import UploadManager


class FakeUploadFile:
    filename = "notes.txt"
    content_type = "text/plain"

    async def read(self):
        return b"OmniAgentAI storage test document"


def test_local_object_storage_put_bytes(tmp_path):
    storage = LocalObjectStorage(root_dir=str(tmp_path))

    stored = storage.put_bytes("files/example.txt", b"hello", content_type="text/plain")

    assert stored.provider == "local"
    assert stored.key == "files/example.txt"
    assert stored.size_bytes == 5
    assert (tmp_path / "files" / "example.txt").read_text(encoding="utf-8") == "hello"


def test_build_object_storage_defaults_to_local():
    storage = build_object_storage("local")

    assert storage.provider == "local"


@pytest.mark.anyio
async def test_upload_manager_indexes_storage_metadata(tmp_path):
    storage = LocalObjectStorage(root_dir=str(tmp_path))
    manager = UploadManager(upload_dir=str(tmp_path), storage=storage)

    result = await manager.save_and_index(FakeUploadFile())
    files = manager.list_files()["files"]

    assert result["storage_provider"] == "local"
    assert result["storage_uri"]
    assert files[0]["storage_provider"] == "local"
    assert files[0]["storage_uri"] == result["storage_uri"]
    assert manager.get_context(result["file_id"], "storage test")
