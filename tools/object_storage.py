from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from config import (
    AWS_REGION,
    AZURE_STORAGE_CONNECTION_STRING,
    AZURE_STORAGE_CONTAINER,
    AZURE_STORAGE_PREFIX,
    S3_BUCKET,
    S3_PREFIX,
    STORAGE_LOCAL_DIR,
    STORAGE_PROVIDER,
)


@dataclass
class StoredObject:
    provider: str
    bucket: str
    key: str
    uri: str
    size_bytes: int


class ObjectStorage:
    provider = "base"

    def put_bytes(self, key: str, content: bytes, content_type: str = "application/octet-stream") -> StoredObject:
        raise NotImplementedError


class LocalObjectStorage(ObjectStorage):
    provider = "local"

    def __init__(self, root_dir: str = STORAGE_LOCAL_DIR):
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def put_bytes(self, key: str, content: bytes, content_type: str = "application/octet-stream") -> StoredObject:
        path = self.root_dir / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return StoredObject(
            provider=self.provider,
            bucket=str(self.root_dir),
            key=key,
            uri=str(path),
            size_bytes=len(content),
        )


class S3ObjectStorage(ObjectStorage):
    provider = "s3"

    def __init__(self, bucket: str = S3_BUCKET, prefix: str = S3_PREFIX, region: str = AWS_REGION):
        if not bucket:
            raise ValueError("S3_BUCKET is required when STORAGE_PROVIDER=s3")
        try:
            import boto3
        except Exception as exc:
            raise RuntimeError("boto3 is required when STORAGE_PROVIDER=s3") from exc

        self.bucket = bucket
        self.prefix = prefix.strip("/")
        kwargs = {"region_name": region} if region else {}
        self.client = boto3.client("s3", **kwargs)

    def put_bytes(self, key: str, content: bytes, content_type: str = "application/octet-stream") -> StoredObject:
        object_key = "/".join(part for part in [self.prefix, key] if part)
        self.client.put_object(
            Bucket=self.bucket,
            Key=object_key,
            Body=content,
            ContentType=content_type,
        )
        return StoredObject(
            provider=self.provider,
            bucket=self.bucket,
            key=object_key,
            uri=f"s3://{self.bucket}/{object_key}",
            size_bytes=len(content),
        )


class AzureBlobObjectStorage(ObjectStorage):
    provider = "azure_blob"

    def __init__(
        self,
        connection_string: str = AZURE_STORAGE_CONNECTION_STRING,
        container: str = AZURE_STORAGE_CONTAINER,
        prefix: str = AZURE_STORAGE_PREFIX,
    ):
        if not connection_string:
            raise ValueError("AZURE_STORAGE_CONNECTION_STRING is required when STORAGE_PROVIDER=azure_blob")
        if not container:
            raise ValueError("AZURE_STORAGE_CONTAINER is required when STORAGE_PROVIDER=azure_blob")
        try:
            from azure.storage.blob import BlobServiceClient, ContentSettings
        except Exception as exc:
            raise RuntimeError("azure-storage-blob is required when STORAGE_PROVIDER=azure_blob") from exc

        self.content_settings_cls = ContentSettings
        self.container = container
        self.prefix = prefix.strip("/")
        self.service = BlobServiceClient.from_connection_string(connection_string)
        self.container_client = self.service.get_container_client(container)
        if not self.container_client.exists():
            self.container_client.create_container()

    def put_bytes(self, key: str, content: bytes, content_type: str = "application/octet-stream") -> StoredObject:
        blob_name = "/".join(part for part in [self.prefix, key] if part)
        blob_client = self.container_client.get_blob_client(blob_name)
        blob_client.upload_blob(
            content,
            overwrite=True,
            content_settings=self.content_settings_cls(content_type=content_type),
        )
        return StoredObject(
            provider=self.provider,
            bucket=self.container,
            key=blob_name,
            uri=f"azure://{self.container}/{blob_name}",
            size_bytes=len(content),
        )


def build_object_storage(provider: str = STORAGE_PROVIDER) -> ObjectStorage:
    normalized = (provider or "local").lower()
    if normalized == "local":
        return LocalObjectStorage()
    if normalized == "s3":
        return S3ObjectStorage()
    if normalized in {"azure", "azure_blob", "blob"}:
        return AzureBlobObjectStorage()
    raise ValueError(f"Unsupported STORAGE_PROVIDER: {provider}")
