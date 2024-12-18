from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.api.routers.folder import folder_router
from app.api.routers.chat import chat_router
from app.middlewares.frontend import FrontendMiddleware

app = FastAPI()

# Ajoute le middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permet les requêtes provenant de n'importe quelle origine
    allow_credentials=True,  # Autorise l'envoi de cookies avec les requêtes
    allow_methods=["*"],  # Permet toutes les méthodes HTTP (GET, POST, etc.)
    allow_headers=["*"],  # Autorise tous les en-têtes
)

# Monte les fichiers statiques uniquement si le répertoire existe
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Ajoute le middleware pour la gestion du frontend
app.add_middleware(FrontendMiddleware)

# Inclut les routes de l'API
app.include_router(
    folder_router,
    prefix="/api",
    tags=["files"]  # Ajoute un tag pour la documentation
)

app.include_router(
    chat_router,
    prefix="/api",
    tags=["chat"]  # Ajoute un tag pour la documentation
)