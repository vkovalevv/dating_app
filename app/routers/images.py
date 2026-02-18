from fastapi import APIRouter, Depends, HTTPException, status

from app.db import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.images import Image as ImageModel
from app.models.users import User as UserModel
from app.schemas.images import Image as ImageSchema, ImageCreate

from app.auth import get_current_user
from sqlalchemy import select
router = APIRouter(prefix='/images',
                   tags=['images'])


@router.post('/create', response_model=ImageSchema)
async def create_image(image: ImageCreate,
                       db: AsyncSession = Depends(get_async_db),
                       current_user: UserModel = Depends(get_current_user)):

    images = (await db.scalars(select(ImageModel)
                               .where(ImageModel.user_id == current_user.id)
                               .order_by(ImageModel.order))
              ).all()

    is_main = True if len(images) == 0 else False
    order = images[-1].order + 1 if len(images) != 0 else 0

    db_image = ImageModel(**image.model_dump(),
                          user_id=current_user.id,
                          order=order,
                          is_main=is_main)
    db.add(db_image)
    await db.commit()
    return db_image


@router.delete('/{image_id}/delete')
async def delete_image(image_id: int,
                       db: AsyncSession = Depends(get_async_db),
                       current_user: UserModel = Depends(get_current_user)):

    image = (await db.scalars(select(ImageModel)
                              .where(ImageModel.id == image_id))).first()
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='Image not found.')

    if current_user.role != 'admin' and image.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detai='Only author or admins can perform this action.')

    images = (await db.scalars(select(ImageModel)
                               .where(ImageModel.user_id == current_user.id)
                               .order_by(ImageModel.order))
              ).all()

    fl = False
    if image.is_main and len(images) != 1:
        for i, img in enumerate(images):
            if fl:
                img.is_main = True
                break
            if img.is_main:
                fl = True

    await db.execute(delete(ImageModel).where(ImageModel.id == image_id))
    await db.commit()
    return {'detail': 'Image deleted'}
