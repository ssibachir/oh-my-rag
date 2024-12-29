from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.responses import FileResponse
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
files_router = APIRouter()

@files_router.get("/folder/view/{file_path:path}")
async def view_file(file_path: str):
    try:
        project_root = Path(__file__).parent.parent.parent.parent
        data_path = project_root / "data"
        full_path = data_path / file_path.lstrip('/')
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="Fichier non trouvé")
            
        return FileResponse(
            path=str(full_path),
            media_type="application/pdf",
            headers={
                "Content-Type": "application/pdf",
                "Content-Disposition": "inline; filename=\"{}\"".format(full_path.name)
            }
        )
    except Exception as e:
        logger.error(f"Erreur: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 