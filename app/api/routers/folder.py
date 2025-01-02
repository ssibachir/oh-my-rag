from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
import os
from typing import List, Set
from pydantic import BaseModel
import shutil
from app.engine.generate import process_documents
from app.engine.vectordb import get_vector_store, get_collection_stats
import logging
from fastapi.responses import FileResponse
from app.api.auth import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

# Import des extensions supportées
try:
    from app.engine.loaders import SUPPORTED_EXTENSIONS
except ImportError:
    # Fallback si l'import échoue
    SUPPORTED_EXTENSIONS = {'.pdf', '.txt', '.docx', '.csv', '.xlsx'}

folder_router = APIRouter()

class FileInfo(BaseModel):
    name: str
    size: int
    last_modified: float
    type: str

class FilesResponse(BaseModel):
    files: List[FileInfo]
    count: int
    message: str
    supported_extensions: Set[str]

@folder_router.get("/folder/files")
async def list_files():
    """
    Liste tous les fichiers dans le dossier data/ (documents source pour le RAG).
    """
    try:
        data_dir = "data"
        
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            return {
                "files": [],
                "count": 0,
                "message": "Le dossier data/ a été créé. Ajoutez vos documents pour le RAG ici.",
                "supported_extensions": list(SUPPORTED_EXTENSIONS)  # Convertir en liste pour la sérialisation JSON
            }

        files_info = []
        for filename in os.listdir(data_dir):
            file_path = os.path.join(data_dir, filename)
            if os.path.isfile(file_path):
                # Obtenir l'extension du fichier
                _, ext = os.path.splitext(filename)
                ext = ext.lower()
                
                # Obtenir les stats du fichier
                stat = os.stat(file_path)
                
                # Ajouter le fichier avec son statut
                files_info.append({
                    "name": filename,
                    "size": stat.st_size,
                    "last_modified": stat.st_mtime,
                    "type": "supported" if ext in SUPPORTED_EXTENSIONS else "unsupported"
                })

        # Trier les fichiers : supportés d'abord, puis par nom
        files_info.sort(key=lambda x: (x["type"] != "supported", x["name"]))

        return {
            "files": files_info,
            "count": len(files_info),
            "message": f"Trouvé {len(files_info)} fichier(s) dans le dossier data/",
            "supported_extensions": list(SUPPORTED_EXTENSIONS)
        }

    except Exception as e:
        return {
            "files": [],
            "count": 0,
            "message": f"Erreur lors de la lecture des fichiers: {str(e)}",
            "supported_extensions": list(SUPPORTED_EXTENSIONS)
        }

async def index_new_file(file_path: str):
    """
    Fonction asynchrone pour indexer un nouveau fichier.
    Cette fonction sera exécutée en arrière-plan.
    """
    try:
        logger.info(f"Début de l'indexation du fichier: {file_path}")
        
        # Vérifier que le fichier existe toujours
        if not os.path.exists(file_path):
            logger.error(f"Le fichier n'existe plus: {file_path}")
            return
            
        # Appeler la fonction d'indexation pour ce fichier spécifique
        await process_documents(specific_file=file_path)
        logger.info(f"Indexation terminée avec succès pour: {file_path}")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'indexation du fichier {file_path}: {str(e)}", exc_info=True)

@folder_router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user)  # Ajouter l'authentification
):
    """
    Upload un fichier dans le dossier data/ et lance son indexation.
    """
    try:
        # Vérifier l'extension du fichier
        _, ext = os.path.splitext(file.filename)
        ext = ext.lower()
        
        if ext not in SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Format de fichier non supporté. Extensions acceptées: {', '.join(SUPPORTED_EXTENSIONS)}"
            )
        
        # Créer le dossier data/ s'il n'existe pas
        data_dir = "data"
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        # Chemin complet du fichier
        file_path = os.path.join(data_dir, file.filename)
        
        # Sauvegarder le fichier
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Ajouter la tâche d'indexation en arrière-plan
        if background_tasks:
            background_tasks.add_task(index_new_file, file_path)
        
        return {
            "message": f"Fichier {file.filename} uploadé avec succès et en cours d'indexation",
            "filename": file.filename,
            "size": os.path.getsize(file_path),
            "status": "indexing"
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur inattendue: {str(e)}"
        )

@folder_router.get("/folder/debug")
async def debug_vectorstore():
    """
    Route de debug pour vérifier le contenu du vector store
    """
    try:
        vector_store = get_vector_store()
        
        # Récupérer les stats
        stats = get_collection_stats(vector_store)
        
        # Récupérer les documents
        docs = vector_store.client.scroll(
            collection_name=os.getenv("QDRANT_COLLECTION"),
            limit=100
        )
        
        # Grouper par source
        docs_by_source = {}
        for doc in docs[0]:
            source = doc.payload.get("metadata", {}).get("source", "unknown")
            if source not in docs_by_source:
                docs_by_source[source] = 0
            docs_by_source[source] += 1
        
        return {
            "collection_stats": stats,
            "documents_count": len(docs[0]),
            "documents_by_source": docs_by_source,
            "documents": [doc.payload for doc in docs[0]]
        }
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des stats: {str(e)}")
        return {"error": str(e)}

@folder_router.get("/folder/view/{filename}")
async def view_file(filename: str):
    """
    Sert le fichier PDF pour la visualisation.
    """
    try:
        # Nettoyer le nom du fichier de tout chemin potentiel
        clean_filename = os.path.basename(filename)
        file_path = os.path.join("data", clean_filename)
        
        logger.info(f"Tentative d'accès au fichier: {file_path}")
        
        if not os.path.exists(file_path):
            logger.error(f"Fichier non trouvé: {file_path}")
            raise HTTPException(status_code=404, detail=f"Fichier non trouvé: {clean_filename}")
        
        # Vérifier que c'est bien un PDF
        if not clean_filename.lower().endswith('.pdf'):
            logger.error(f"Format non supporté: {clean_filename}")
            raise HTTPException(status_code=400, detail="Format de fichier non supporté")
        
        logger.info(f"Envoi du fichier PDF: {file_path}")
        return FileResponse(
            path=file_path,
            media_type='application/pdf',
            filename=clean_filename,
            headers={
                "Content-Disposition": f"inline; filename={clean_filename}",
                "Content-Type": "application/pdf"
            }
        )
    except Exception as e:
        logger.error(f"Erreur lors de l'accès au fichier: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

