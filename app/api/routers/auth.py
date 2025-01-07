import os
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from app.models.user import User, UserCreate
from app.db.supabase_client import supabase
import logging
import uuid

logger = logging.getLogger(__name__)
load_dotenv()

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
auth_router = APIRouter()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@auth_router.post("/register")
async def register(user_data: UserCreate):
    try:
        logger.info(f"Début de l'inscription pour: {user_data.email}")
        
        # Vérifier si l'utilisateur existe déjà avec une requête plus précise
        existing_user = supabase.client.table('users')\
            .select('*')\
            .eq('email', user_data.email)\
            .execute()
            
        logger.info(f"Données brutes de la vérification: {existing_user}")
        
        # Vérifier explicitement si data contient des résultats
        if existing_user.data and len(existing_user.data) > 0:
            logger.info(f"Utilisateur existant trouvé: {existing_user.data}")
            raise HTTPException(
                status_code=400,
                detail="Un utilisateur avec cet email existe déjà"
            )

        # Créer l'utilisateur directement dans notre table users
        user_id = str(uuid.uuid4())
        user_table_data = {
            "id": user_id,
            "email": user_data.email,
            "username": user_data.username,
            "created_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Tentative d'insertion avec les données: {user_table_data}")
        
        try:
            # Forcer une nouvelle insertion
            user_response = supabase.client.table('users')\
                .insert(user_table_data)\
                .execute()
            
            logger.info(f"Réponse de l'insertion: {user_response}")
            
            if not user_response.data:
                raise HTTPException(
                    status_code=500,
                    detail="Erreur lors de la création du compte"
                )
                
            return {
                "message": "Utilisateur créé avec succès",
                "user": user_response.data[0]
            }
            
        except Exception as e:
            logger.error(f"Erreur détaillée lors de l'insertion: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de l'insertion: {str(e)}"
            )
            
    except HTTPException as he:
        raise he  # Propager les erreurs HTTP directement
    except Exception as e:
        logger.error(f"Erreur lors de l'inscription: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@auth_router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        logger.info(f"Tentative de connexion pour: {form_data.username}")
        
        # Récupérer l'utilisateur par email
        user_response = supabase.client.table('users')\
            .select('*')\
            .eq('email', form_data.username)\
            .execute()
        
        logger.info(f"Réponse de la recherche utilisateur: {user_response}")
        
        if not user_response.data:  # Vérifier .data au lieu de la réponse directe
            raise HTTPException(
                status_code=401,
                detail="Identifiants invalides"
            )
        
        user = user_response.data[0]  # Accéder au premier élément de data
        
        # Créer le token JWT
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user['id'])},
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": User(**user)
        }
        
    except HTTPException as he:
        # Propager les erreurs HTTP telles quelles
        raise he
    except Exception as e:
        logger.error(f"Erreur de login: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Erreur interne du serveur"
        )