from pydantic import BaseModel, Field
from typing import Annotated
from app.models.swipes import SwipeAction

class SwipeCreate(BaseModel):
    target_user: int  = Field(...)
    acion: SwipeAction = Field(..., description='Действие: pass=0; like=1')

class Swipe(BaseModel):
    first_user_id: int
    second_user_id: int
    # If the first user liked the second one,
    # then the first_decision=True
    first_action: SwipeAction
    second_action: Annotated[SwipeAction | None, Field(default=None)] = None
  