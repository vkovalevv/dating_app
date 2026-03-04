from fastapi import FastAPI, Request
from app.routers import users, images, swipes, preferences
from app.task.celery import generate_stack_for_all
from app.logger import logger
from uuid import uuid4
import time
from fastapi.responses import JSONResponse

app = FastAPI()
app.include_router(users.router)
app.include_router(images.router)
app.include_router(swipes.router)
app.include_router(preferences.router)


@app.middleware('http')
async def log_requests(request: Request, call_next):
    log_id = uuid4()
    with logger.contextualize(log_id=log_id):
        try:
            start_time = time.time()
            response = await call_next(request)
            duration = round(time.time() - start_time, 4)

            if response.status_code >= 400:
                logger.warning(
                    '{} {} - {} - {:.4f}s',
                    request.method,
                    request.url.path,
                    response.status_code,
                    duration
                )
            else:
                logger.info(
                    '{} {} - {} - {:.4f}s',
                    request.method,
                    request.url.path,
                    response.status_code,
                    duration
                )
        except Exception as exc:
            logger.error('{} {} Failed: {}',
                         request.method,
                         request.url.path,
                         str(exc))

            response = JSONResponse(
                content={
                    'access': False,
                },
                status_code=500
            )
        return response


@app.get('/')
async def hello():
    generate_stack_for_all.apply_async()
    return {'message': 'hello world'}
