from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import chat, folder, auth
from app.middlewares.frontend import FrontendMiddleware
from app.core.logging import setup_logging
import uvicorn
import logging

# Création de l'application FastAPI
app = FastAPI()

# Configuration CORS plus permissive
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permet toutes les origines en développement
    allow_credentials=False,  # Important: doit être False si allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Montage des routers
app.include_router(auth.auth_router, prefix="/api/auth")
app.include_router(chat.chat_router, prefix="/api")
app.include_router(folder.folder_router, prefix="/api/folder")

# Middleware pour servir le frontend
app.add_middleware(FrontendMiddleware)

setup_logging()  # Ajoutez cette ligne au début du fichier

# Configuration des logs
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Configuration spécifique pour les logs FastAPI et nos modules
for logger_name in ['uvicorn', 'fastapi', 'app']:
    logging.getLogger(logger_name).setLevel(logging.DEBUG)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug"
    ) 