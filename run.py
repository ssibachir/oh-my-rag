import uvicorn
import logging
from dotenv import load_dotenv
import os

# Configuration du logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Chargement des variables d'environnement
load_dotenv()

def dev():
    """Démarre le serveur en mode développement"""
    try:
        uvicorn.run(
            "app.api.app:app",
            host=os.getenv("APP_HOST", "0.0.0.0"),
            port=int(os.getenv("APP_PORT", "8000")),
            reload=True,
            log_level="debug"
        )
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du serveur: {str(e)}", exc_info=True)
        raise SystemError(f"Impossible de démarrer le serveur: {str(e)}") from e

def prod():
    """Démarre le serveur en mode production"""
    try:
        uvicorn.run(
            "app.api.app:app",
            host=os.getenv("APP_HOST", "0.0.0.0"),
            port=int(os.getenv("APP_PORT", "8000")),
            workers=4
        )
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du serveur: {str(e)}", exc_info=True)
        raise SystemError(f"Impossible de démarrer le serveur: {str(e)}") from e

if __name__ == "__main__":
    dev()
