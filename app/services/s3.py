from aiobotocore.session import get_session
from contextlib import asynccontextmanager
from app.config import settings

class S3Client:
    def __init__(
            self,
            access_key: str,
            secret_key: str,
            endpoint_url: str,
            bucket_name: str,
            bucket_uuid: str
    ):
        self.config = {
            'aws_access_key_id': access_key,
            'aws_secret_access_key': secret_key,
            'endpoint_url': endpoint_url
        }
        
        self.bucket_name = bucket_name
        self.bucket_uuid = bucket_uuid
        self.session = get_session()

    @asynccontextmanager
    async def get_client(self):
        async with self.session.create_client('s3', **self.config, verify=False) as client:
            yield client

    async def upload_file(self, file_bytes: bytes, file_name: str, content_type: str):
        async with self.get_client() as client:
            await client.put_object(
                Bucket=self.bucket_name,
                Key=file_name,
                Body=file_bytes,
                ContentType=content_type
            )
        return f"https://{self.bucket_uuid}.selstorage.ru/{file_name}"

    async def delete_file(self, file_name):
        async with self.get_client() as client:
            await client.delete_object(
                Bucket=self.bucket_name,
                Key=file_name
            )

s3_client = S3Client(
    access_key=settings.S3_ACCESS_KEY,
    secret_key=settings.S3_SECRET_KEY,
    endpoint_url=settings.S3_ENDPOINT_URL,
    bucket_name=settings.S3_BUCKET_NAME,
    bucket_uuid='44a7329f-364c-46e2-8182-50a9436ed725'
)
