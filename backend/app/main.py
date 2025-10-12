from fastapi import FastAPI
from fastapi.responses import Response, FileResponse
import os
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.users import router as users_router
from app.api.v1.routes.chat import router as chat_router
from app.api.v1.routes.conversations import router as conv_router
from app.api.v1.routes.audio import router as audio_router

app = FastAPI(title="Backend FastAPI Base", version="0.1.1")

# CORS configuration to allow frontend dev origin(s)
origins = [
    "http://localhost",
    "http://localhost:5173",  # Vite default dev port
    "http://localhost:1416",  # Previous frontend port if used
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router, prefix="/api/v1", tags=["health"])
app.include_router(users_router, prefix="/api/v1", tags=["sessions"])
app.include_router(chat_router, prefix="/api/v1", tags=["agent"])
app.include_router(conv_router, prefix="/api/v1", tags=["conversations"])
app.include_router(audio_router, prefix="/api/v1", tags=["audio"])


# Optional favicon handler to avoid 404 noise when hitting the API root in a browser
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    here = os.path.dirname(__file__)
    candidate = os.path.join(here, "static", "favicon.ico")
    if os.path.exists(candidate):
        return FileResponse(candidate)
    # No favicon available; return empty response instead of 404
    return Response(status_code=204)
