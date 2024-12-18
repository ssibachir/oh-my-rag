from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from llama_index.core.llms import MessageRole
from app.engine.engine import get_chat_engine
from app.engine.query_filter import generate_filters

chat_router = APIRouter()

class Message(BaseModel):
    """
    Représente un message utilisé dans les requêtes de chat.

    Attributs:
        role (str): Le rôle du message (par exemple, "user" pour l'utilisateur ou "assistant" pour le modèle).
        content (str): Le contenu textuel du message.
    """
    role: str
    content: str

class ChatRequest(BaseModel):
    """
    Modèle de requête pour le chat.

    Attributs:
        messages (List[Message]): Liste des messages échangés, incluant l'historique et le dernier message.
    """
    messages: List[Message]

@chat_router.post("/chat/request")
async def chat_request(request: ChatRequest):
    """
    Traite une requête de chat en utilisant un moteur de chat.

    Cette route prend une requête contenant une liste de messages, extrait le dernier message,
    traite l'historique des messages pour le modèle de chat, et renvoie une réponse générée
    ainsi que les éventuelles métadonnées associées.

    Args:
        request (ChatRequest): La requête contenant les messages d'historique et le dernier message.

    Returns:
        dict: Une réponse contenant:
            - "response": La réponse générée par le modèle.
            - "source_nodes": Une liste de sources associées à la réponse, si disponible.

    Exceptions:
        Retourne un message d'erreur si une exception est levée lors du traitement.
    """
    try:
        # Obtenir le dernier message de l'utilisateur
        last_message = request.messages[-1].content
        
        # Convertir les messages pour LlamaIndex
        history_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages[:-1]
        ]
        
        # Initialiser le chat engine
        chat_engine = get_chat_engine()
        
        # Obtenir la réponse
        response = await chat_engine.achat(
            last_message,
            history_messages
        )
        
        return {
            "response": response.response,
            "source_nodes": [
                {
                    "text": node.node.text,
                    "metadata": node.node.metadata
                }
                for node in response.source_nodes
            ] if response.source_nodes else []
        }
        
    except Exception as e:
        return {"response": f"Error: {str(e)}"}

@chat_router.post("/chat")
async def chat(request: ChatRequest):
    """
    Traite une requête de chat via une interface alternative.

    Cette route utilise la logique de `chat_request`, mais est potentiellement prévue
    pour le streaming des réponses.

    Args:
        request (ChatRequest): La requête contenant les messages.

    Returns:
        dict: Une réponse identique à celle de la route `/chat/request`.
    """
    # Pour le streaming, utilisez la même logique mais avec astream_chat
    response = await chat_request(request)
    return response
