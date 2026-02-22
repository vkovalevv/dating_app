from typing import Annotated
from pydantic import BaseModel, Field, ConfigDict


class PreferenceCreate(BaseModel):
    age: Annotated[int, Field(..., ge=18, le=100,
                              description='Возраст больше или равен заданного')]
    gender: Annotated[str, Field(..., pattern='^(male|female)$')]
    max_distance: Annotated[float,
                        Field(...,
                              description='Расстояние между пользователями',
                              )
                        ]


class Preference(BaseModel):
    id: int
    user_id: Annotated[int, Field(...)]
    age: Annotated[int, Field(..., ge=18, le=100,
                              description='Возраст больше или равен заданного')]
    gender: Annotated[str, Field(..., pattern='^(male|female)$')]
    max_distance: Annotated[float,
                        Field(...,
                              description='Расстояние между пользователями'
                              )
                        ]

    model_config = ConfigDict(from_attributes=True)
