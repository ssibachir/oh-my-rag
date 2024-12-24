from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import chat, folder, auth
from app.middlewares.frontend import FrontendMiddleware

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

if __name__ == "__main__":
    import uvicorn
    # Lancement du serveur de développement
    uvicorn.run(
        "run:app",
        host="0.0.0.0",  # Écoute sur toutes les interfaces
        port=8000,       # Port du serveur
        reload=True      # Rechargement automatique en développement
    ) 