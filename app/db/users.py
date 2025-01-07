from typing import Optional
from datetime import datetime
import uuid
from app.models.user import User, UserCreate
from app.db.supabase_client import supabase
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

async def get_user_by_email(email: str) -> User | None:
    """Récupère un utilisateur par son email"""
    try:
        response = await supabase.select(
            'users',
            {'email': f'eq.{email}'}
        )
        if response and len(response) > 0:
            return User(**response[0])
        return None
    except Exception as e:
        logger.error(f"Erreur get_user_by_email: {str(e)}")
        return None  # Retourner None au lieu de lever une exception

async def get_user_by_id(user_id: str) -> User | None:
    """Récupère un utilisateur par son ID"""
    try:
        response = await supabase.select(
            'users',
            {'id': f'eq.{user_id}'}
        )
        if response and len(response) > 0:
            return User(**response[0])
        return None
    except Exception as e:
        print(f"Erreur lors de la récupération de l'utilisateur: {e}")
        raise HTTPException(status_code=500, detail="Erreur base de données")

async def create_user(user_data: UserCreate) -> User:
    """Crée un nouvel utilisateur"""
    try:
        # Vérifier si l'email existe déjà
        existing_user = await get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email déjà utilisé")

        # Créer l'utilisateur
        user_dict = {
            "email": user_data.email,
            "username": user_data.username,
            "created_at": datetime.utcnow().isoformat()
        }
        
        response = await supabase.insert('users', user_dict)
        
        if not response:
            raise HTTPException(status_code=500, detail="Erreur lors de la création")
            
        return User(**response[0])
    except Exception as e:
        logger.error(f"Erreur create_user: {str(e)}")
        raise