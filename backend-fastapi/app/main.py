from fastapi import FastAPI
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.users import router as users_router
from app.api.v1.routes.chat import router as chat_router
from app.api.v1.routes.conversations import router as conv_router

app = FastAPI(title="Backend FastAPI Base", version="0.1.1")
app.include_router(health_router, prefix="/api/v1", tags=["health"])
app.include_router(users_router, prefix="/api/v1", tags=["sessions"])
app.include_router(chat_router, prefix="/api/v1", tags=["agent"])
app.include_router(conv_router, prefix="/api/v1", tags=["conversations"])
