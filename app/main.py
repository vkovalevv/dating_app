from fastapi import FastAPI
from app.routers import users

app = FastAPI()
app.include_router(users.router)

@app.get('/')
async def hello():
    return {'message':'hello world'}