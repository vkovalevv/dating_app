from pydantic import BaseModel

class Image(BaseModel):
    id: int
    user_id: int
    image: str
    order: int
    is_main: bool