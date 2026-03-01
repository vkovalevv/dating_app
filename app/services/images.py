from fastapi import HTTPException, status
from fastapi import UploadFile, File
from pathlib import Path
import uuid
from app.services.s3 import s3_client

BASE_DIR = Path(__file__).parent.parent.parent
MEDIA_ROOT = BASE_DIR / 'media' / 'users'
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/png', 'image/webp'}
MAX_IMAGE_SIZE = 2 * 512 * 512


async def save_user_image(file: UploadFile) -> str:
    '''
    Сохраняем изображение пользователя и возращаем его относительный URL.
    '''
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Only JPEG, PNG or WBP are allowed.')

    content = await file.read()
    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Image is too large.')

    extension = Path(file.filename or '').suffix.lower() or '.jpg'
    file_name = f'{uuid.uuid4()}{extension}'
    url = await s3_client.upload_file(
        content, file_name, file.content_type
    )
    return url


def remove_user_image(url: str | None):
    '''
    Удаляет файл изображение, если он существует
    '''
    if not url:
        return
    relative_path = url.lstrip('/')
    file_path = BASE_DIR / relative_path
    if file_path.exists():
        file_path.unlink()
