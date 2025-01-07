from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.db.supabase_client import supabase
import logging
from app.models.user import User
from jose import JWTError, jwt
import os

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
logger = logging.getLogger(__name__)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    try:
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Non authentifié"
            )

        try:
            # Décoder le JWT token
            secret_key = os.getenv("JWT_SECRET_KEY")
            algorithm = os.getenv("JWT_ALGORITHM", "HS256")
            
            payload = jwt.decode(token, secret_key, algorithms=[algorithm])
            user_id = payload.get("sub")
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token invalide"
                )
            
            # Récupérer l'utilisateur avec l'ID décodé
            user_response = await supabase.select(
                'users',
                {'id': f'eq.{user_id}'}
            )
            
            if not user_response:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Utilisateur non trouvé"
                )
            
            return User(**user_response[0])
            
        except JWTError as e:
            logger.error(f"Erreur JWT: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide"
            )
            
    except Exception as e:
        logger.error(f"Erreur d'authentification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Non authentifié"
        ) 