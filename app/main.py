from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers.auth import auth_router
from app.api.routers.chat import chat_router
from app.api.routers.files import files_router

app = FastAPI()

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Montage des routers
app.include_router(auth_router, prefix="/api/auth")
app.include_router(chat_router, prefix="/api")
app.include_router(files_router, prefix="/api")

# Pour le débogage
@app.options("/{full_path:path}")
async def options_route(full_path: str):
    return {"detail": "OK"} 