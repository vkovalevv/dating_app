from pydantic import BaseModel, ConfigDict

class ImageCreate(BaseModel):
    image: str 

class Image(BaseModel):
    id: int
    user_id: int
    image: str
    order: int
    is_main: bool

    model_config = ConfigDict(from_attributes=True)