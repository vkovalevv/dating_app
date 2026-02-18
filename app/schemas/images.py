from pydantic import BaseModel

class ImageCreate(BaseModel):
    image: str 

class Image(BaseModel):
    id: int
    user_id: int
    image: str
    order: int
    is_main: bool