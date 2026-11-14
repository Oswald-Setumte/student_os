from fastapi import FastAPI
from source.database.session import engine
from source.api.authentication import router as authentication
from source.api.lecture import router as lecture
from contextlib import asynccontextmanager

@asynccontextmanager
async def life(app:FastAPI):
    yield
    await engine.dispose()


app = FastAPI(lifespan=life)
app.include_router(authentication)
app.include_router(lecture)