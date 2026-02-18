from fastapi import FastAPI
from app.routers import users, images

app = FastAPI()
app.include_router(users.router)
app.include_router(images.router)
@app.get('/')
async def hello():
    return {'message':'hello world'}