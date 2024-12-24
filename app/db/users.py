from typing import Optional
from datetime import datetime
import uuid
from app.models.user import UserInDB

# Simulation d'une base de données avec un dictionnaire
# Dans un vrai projet, utilisez une vraie base de données comme PostgreSQL
users_db = {}

async def get_user_by_email(email: str) -> Optional[UserInDB]:
    """Récupère un utilisateur par son email"""
    for user in users_db.values():
        if user.email == email:
            return user
    return None

async def get_user_by_id(user_id: str) -> Optional[UserInDB]:
    """Récupère un utilisateur par son ID"""
    return users_db.get(user_id)

async def create_user(user_data: dict) -> UserInDB:
    """Crée un nouvel utilisateur"""
    user_id = str(uuid.uuid4())
    user_db = UserInDB(
        id=user_id,
        created_at=datetime.utcnow(),
        **user_data
    )
    users_db[user_id] = user_db
    return user_db 