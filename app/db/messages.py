from app.db.supabase_client import supabase
from typing import List
from app.models.chat import ChatMessage

async def save_message(user_id: str, role: str, content: str):
    """Sauvegarde un message dans l'historique"""
    try:
        response = supabase.table('chat_messages').insert({
            'user_id': user_id,
            'role': role,
            'content': content
        }).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Erreur lors de la sauvegarde du message: {e}")
        return None

async def get_user_chat_history(user_id: str) -> List[ChatMessage]:
    """Récupère l'historique des messages d'un utilisateur"""
    try:
        response = supabase.table('chat_messages')\
            .select("*")\
            .eq('user_id', user_id)\
            .order('created_at')\
            .execute()
        
        return [ChatMessage(**msg) for msg in response.data]
    except Exception as e:
        print(f"Erreur lors de la récupération de l'historique: {e}")
        return [] 