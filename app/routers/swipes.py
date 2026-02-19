from fastapi import APIRouter, Depends, HTTPException, status
from app.db import get_async_db
from app.auth import get_current_user

from app.models.swipes import Swipe as SwipeModel
from app.models.users import User as UserModel

from app.schemas.swipes import SwipeCreate, Swipe as SwipeSchema
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.swipes import SwipeCreate
from sqlalchemy import select

router = APIRouter(prefix='/swipes',
                   tags=['swipes'])


@router.post('/make_swipe')
async def make_swipe(swipe: SwipeCreate,
                     current_user: UserModel = Depends(get_current_user),
                     db: AsyncSession = Depends(get_async_db)) -> dict:

    if swipe.target_user == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="You can't swipe yourself")

    check_swipe_result = await db.scalars(select(SwipeModel)
                                          .where(SwipeModel.first_user_id == current_user.id,
                                                 SwipeModel.second_user_id == swipe.target_user))
    check_swipe = check_swipe_result.first()

    if check_swipe:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="You've already swiped this user")
    '''
    Check for the presence of a combination 
    of these two users in the swipe table
    '''
    db_swipe_result = await db.scalars(select(SwipeModel)
                                       .where(SwipeModel.first_user_id == swipe.target_user,
                                              SwipeModel.second_user_id == current_user.id))
    db_swipe = db_swipe_result.first()
    if db_swipe is not None:
        db_swipe.second_action = swipe.acion.value
    else:
        new_swipe = SwipeModel(first_user_id=current_user.id,
                               second_user_id=swipe.target_user,
                               first_action=swipe.acion.value)
        db.add(new_swipe)
    await db.commit()
    return {'detail': 'successfully swiped'}
