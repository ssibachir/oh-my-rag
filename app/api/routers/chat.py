from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List
import json
import logging
from llama_index.core.llms import MessageRole
from app.engine.engine import get_chat_engine
from app.engine.query_filter import generate_filters
import re
from app.models.chat import ChatMessage
from app.models.user import User
from app.api.auth import get_current_user
from app.db.supabase_client import supabase
from datetime import datetime
import asyncio
from app.observability import create_chat_span, end_chat_span
from opentelemetry import trace
from app.api.chat.events import EventCallbackHandler
import os

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

chat_router = APIRouter()

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str  # Message unique au lieu d'une liste
    conversation_id: str  # Ajout de l'ID de conversation

@chat_router.get("/chat/history")
async def get_chat_history(conversation_id: str, current_user: User = Depends(get_current_user)):
    try:
        logger.info(f"Récupération de l'historique pour la conversation: {conversation_id}")
        
        # Récupérer les messages de la conversation
        messages_response = supabase.client.table('chat_messages')\
            .select('*')\
            .eq('conversation_id', conversation_id)\
            .eq('user_id', str(current_user.id))\
            .order('created_at', desc=False)\
            .execute()
            
        logger.info(f"Messages récupérés: {messages_response}")
        
        if not messages_response.data:
            return []
            
        return messages_response.data
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'historique: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur serveur")

@chat_router.post("/chat/message")
async def create_message(message: ChatMessage, current_user: User = Depends(get_current_user)):
    try:
        # Récupérer d'abord l'ID de notre table users
        user_response = await supabase.select(
            'users',
            {'email': f'eq.{current_user.email}'}
        )
        if not user_response:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
            
        user_id = user_response[0]['id']
        
        message_data = {
            "content": message.content,
            "role": message.role,
            "user_id": user_id,  # Utiliser l'ID de notre table users
            "conversation_id": message.conversation_id,
            "created_at": datetime.utcnow().isoformat()
        }
        response = await supabase.insert('chat_messages', message_data)
        return response[0]
    except Exception as e:
        logger.error(f"Erreur lors de la création du message: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur serveur")

async def get_chat_response(message: str, conversation_id: str):
    try:
        chat_engine = get_chat_engine()
        response = chat_engine.chat(message)
        
        # Adapter la réponse au format attendu
        return {
            "content": response.response,  # Utiliser response.response au lieu de response.content
            "source_nodes": response.source_nodes if hasattr(response, 'source_nodes') else []
        }
    except Exception as e:
        logger.error(f"Erreur get_chat_response: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la génération de la réponse"
        )

@chat_router.post("/chat/request")
async def chat_request(request: ChatRequest, current_user: User = Depends(get_current_user)):
    # Créer un span pour cette interaction
    span = create_chat_span(tracer, request.conversation_id, request.message)
    
    try:
        logger.info(f"Nouvelle requête de chat de l'utilisateur: {current_user.id}")
        
        # Créer le message utilisateur
        user_message = {
            "conversation_id": request.conversation_id,
            "user_id": str(current_user.id),
            "content": request.message,
            "role": "user",
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Insérer le message utilisateur
        supabase.client.table('chat_messages').insert(user_message).execute()

        # Initialiser le gestionnaire d'événements
        event_handler = EventCallbackHandler()
        
        # Obtenir la réponse avec streaming
        chat_engine = get_chat_engine()
        response = await chat_engine.astream_chat(request.message)

        # Marquer le span comme réussi avant de commencer le streaming
        end_chat_span(span, True)

        return StreamingResponse(
            content=stream_chat_response(
                request=request,
                event_handler=event_handler,
                response=response,
                current_user=current_user
            ),
            media_type="text/event-stream"
        )

    except Exception as e:
        # Marquer le span comme échoué
        end_chat_span(span, False, error=str(e))
        logger.error(f"Erreur: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def stream_chat_response(request, event_handler, response, current_user):
    try:
        final_response = ""
        async for token in response.async_response_gen():
            final_response += token
            # Format SSE correct
            yield f"data: {json.dumps({'content': token})}\n\n"

        # Une fois le texte terminé, envoyer les sources
        if hasattr(response, 'source_nodes'):
            source_nodes = []
            for node in response.source_nodes:
                # S'assurer que le nom du fichier est correctement extrait
                file_name = node.node.metadata.get('file_name')
                if not file_name and 'source' in node.node.metadata:
                    file_name = os.path.basename(node.node.metadata['source'])
                
                source_nodes.append({
                    "metadata": {
                        "file_name": file_name,
                        "score": float(node.score) if node.score else 0,
                        "source": node.node.metadata.get('source')
                    }
                })
            
            yield f"data: {json.dumps({'type': 'sources', 'data': source_nodes})}\n\n"

        # Sauvegarder le message de l'assistant une fois complet
        assistant_message = {
            "conversation_id": request.conversation_id,
            "user_id": str(current_user.id),
            "content": final_response,
            "role": "assistant",
            "created_at": datetime.utcnow().isoformat()
        }
        supabase.client.table('chat_messages').insert(assistant_message).execute()

    except Exception as e:
        logger.error(f"Erreur streaming: {e}")
        # Format SSE pour les erreurs
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
    finally:
        event_handler.is_done = True

@chat_router.post("/chat/conversation")
async def create_conversation(current_user: User = Depends(get_current_user)):
    """
    Crée une nouvelle conversation pour l'utilisateur.
    """
    try:
        conversation_data = {
            "user_id": str(current_user.id),
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Utiliser from_ au lieu de table
        response = supabase.from_('conversations')\
            .insert(conversation_data)\
            .execute()
            
        if not response.data:
            raise HTTPException(
                status_code=500,
                detail="Erreur lors de la création de la conversation"
            )
            
        return {"conversation_id": response.data[0]['id']}
        
    except Exception as e:
        logger.error(f"Erreur lors de la création de la conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_or_create_user(email: str) -> str:
    """Récupère ou crée un utilisateur dans la table users."""
    try:
        # Chercher l'utilisateur
        user_response = await supabase.select(
            'users',
            {'email': f'eq.{email}'}
        )
        
        if user_response:
            return user_response[0]['id']
            
        # Créer l'utilisateur s'il n'existe pas
        user_data = {
            "email": email,
            "username": email.split('@')[0],
            "created_at": datetime.utcnow().isoformat()
        }
        user_response = await supabase.insert('users', user_data)
        
        if not user_response:
            raise HTTPException(status_code=500, detail="Erreur lors de la création de l'utilisateur")
            
        return user_response[0]['id']
    except Exception as e:
        logger.error(f"Erreur get_or_create_user: {str(e)}")
        raise e
    
@chat_router.get("/conversations")
async def get_user_conversations(current_user: User = Depends(get_current_user)):
    """
    Récupère toutes les conversations d'un utilisateur.
    
    Args:
        current_user: L'utilisateur authentifié actuel
    
    Returns:
        list: Liste des conversations de l'utilisateur
    """
    try:
        # Log pour le débogage
        logger.debug(f"Récupération des conversations pour l'utilisateur: {current_user.id}")
        
        # Utiliser from_ au lieu de table
        response = supabase.from_('conversations')\
            .select('*')\
            .eq('user_id', str(current_user.id))\
            .order('created_at', desc=True)\
            .execute()
            
        logger.debug(f"Réponse de Supabase: {response}")
        
        if not response.data:
            logger.info(f"Aucune conversation trouvée pour l'utilisateur {current_user.id}")
            return []
            
        # Formater les conversations pour le frontend
        conversations = [{
            'id': conv['id'],
            'created_at': conv['created_at']
        } for conv in response.data]
        
        return conversations
            
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des conversations: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des conversations: {str(e)}"
        )
