from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List
import json
import logging
from llama_index.core.llms import MessageRole
from app.engine.engine import get_chat_engine
from app.engine.query_filter import generate_filters
import re  # Ajoutez cet import en haut du fichier

# Initialisation du logger
logger = logging.getLogger(__name__)

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
        # Log pour debug
        print("Messages reçus:", request.messages)
        
        # Obtenir le dernier message
        last_message = request.messages[-1].content
        
        # Initialiser le chat engine
        chat_engine = get_chat_engine()
        
        # Obtenir la réponse
        response = await chat_engine.achat(
            last_message,
            []  # Pour l'instant, on n'utilise pas l'historique
        )
        
        # Retourner la réponse avec les sources
        return {
            "response": response.response,
            "source_nodes": [
                {
                    "text": node.node.text,
                    "metadata": {
                        "source": node.node.metadata.get('source', ''),
                        "view_url": f"/api/folder/view/{node.node.metadata.get('source', '').replace('data/', '')}",
                        "score": float(node.score) if hasattr(node, 'score') else 0
                    }
                }
                for node in (response.source_nodes or [])
            ]
        }
        
    except Exception as e:
        print("Erreur:", str(e))  # Log pour debug
        return {"response": f"Error: {str(e)}"}

@chat_router.post("/chat")
async def chat(request: ChatRequest):
    """
    Endpoint de chat qui retourne la réponse en streaming avec les références.
    """
    try:
        user_message = request.messages[-1].content
        chat_engine = get_chat_engine()
        
        async def generate_response():
            streaming_response = chat_engine.stream_chat(user_message)
            
            # Trouver la meilleure source
            best_source = None
            logger.debug("Recherche des sources pertinentes...")
            
            if (hasattr(streaming_response, 'source_nodes') and 
                streaming_response.source_nodes):
                # Log de tous les scores trouvés
                for node in streaming_response.source_nodes:
                    logger.debug(f"Score trouvé: {node.score * 100:.1f}% pour {node.node.metadata.get('source', 'unknown')}")
                
                best_source = max(streaming_response.source_nodes, key=lambda x: x.score)
                logger.debug(f"Meilleure source trouvée: {best_source.node.metadata.get('source', 'unknown')}")
                logger.debug(f"Score de pertinence: {best_source.score * 100:.1f}%")
            else:
                logger.debug("Aucune source trouvée dans la réponse")
            
            # Pour détecter et supprimer la première citation
            first_citation_found = False
            buffer = ""
            
            # Traiter la réponse en streaming
            for token in streaming_response.response_gen:
                buffer += token
                
                # Si on n'a pas encore trouvé la première citation
                if not first_citation_found:
                    # Vérifier si le buffer contient une citation
                    match = re.search(r'\(source : [^)]+\)', buffer)
                    if match:
                        # Supprimer la première citation
                        buffer = re.sub(r'\(source : [^)]+\)', '', buffer, count=1)
                        first_citation_found = True
                        # Envoyer le buffer nettoyé
                        for char in buffer:
                            yield f"data: {json.dumps({'token': char})}\n\n"
                        buffer = ""
                    elif len(buffer) > 100:  # Si le buffer est assez long et pas de citation
                        # Envoyer le début du buffer
                        yield f"data: {json.dumps({'token': buffer[0]})}\n\n"
                        buffer = buffer[1:]
                else:
                    # Une fois la première citation trouvée, streaming normal
                    yield f"data: {json.dumps({'token': token})}\n\n"
            
            # Envoyer le reste du buffer s'il en reste
            if buffer:
                for char in buffer:
                    yield f"data: {json.dumps({'token': char})}\n\n"
            
            # Ajouter notre propre citation si pertinent
            if best_source and best_source.score > 0.5:
                filename = best_source.node.metadata.get('source', 'unknown').replace('data/', '')
                source_text = f" (source : {filename})"
                
                for char in source_text:
                    yield f"data: {json.dumps({'token': char})}\n\n"
                
                yield f"data: {json.dumps({'source_metadata': {
                    'file': filename,
                    'text': best_source.node.text,
                    'score': float(best_source.score),
                    'view_url': f"/api/folder/view/{filename}"
                }})}\n\n"
            
            yield f"data: {json.dumps({'end': True})}\n\n"
        
        return StreamingResponse(
            generate_response(),
            media_type="text/event-stream"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
