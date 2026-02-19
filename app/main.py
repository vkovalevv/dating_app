from fastapi import FastAPI
from app.routers import users, images, swipes

app = FastAPI()
app.include_router(users.router)
app.include_router(images.router)
app.include_router(swipes.router)
@app.get('/')
async def hello():
    return {'message':'hello world'}