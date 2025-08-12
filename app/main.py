from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise
from app.config import settings
from app.user.router import router as user_router

@asynccontextmanager
async def start_app(app: FastAPI):
    print('Starting app')
    yield
app = FastAPI(root_path="/auth", lifespan=start_app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)

register_tortoise(
    app,
    config=settings.tortoise_orm,
    generate_schemas=True,
    add_exception_handlers=True,
)
