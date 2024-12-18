import os
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core import Document
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

def get_collection_stats(vector_store: QdrantVectorStore) -> Dict[str, Any]:
    """
    Récupère les statistiques essentielles de la collection Qdrant.
    """
    try:
        collection_name = os.getenv("QDRANT_COLLECTION")
        client = vector_store.client
        
        # Récupérer les infos de la collection
        collection_info = client.get_collection(collection_name)
        
        return {
            "collection_name": collection_name,
            "points_count": collection_info.points_count,
            "segments_count": collection_info.segments_count
        }
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des stats: {str(e)}")
        return {"error": str(e)}

def get_vector_store(force_recreate: bool = False) -> QdrantVectorStore:
    """
    Récupère ou crée un vector store Qdrant.
    """
    collection_name = os.getenv("QDRANT_COLLECTION")
    url = os.getenv("QDRANT_URL")
    api_key = os.getenv("QDRANT_API_KEY")
    
    if not collection_name or not url:
        raise ValueError(
            "Please set QDRANT_COLLECTION, QDRANT_URL"
            " to your environment variables or config them in the .env file"
        )

    store = QdrantVectorStore(
        collection_name=collection_name,
        url=url,
        api_key=api_key,
    )

    # Log des stats avant création/modification
    logger.info("Stats de la collection avant modification:")
    logger.info(get_collection_stats(store))

    return store

def add_documents_to_vectorstore(documents: List[Document], vector_store: QdrantVectorStore) -> bool:
    """
    Ajoute de nouveaux documents au vector store existant sans réinitialiser la collection.
    """
    try:
        logger.info(f"Ajout de {len(documents)} document(s) au vector store")
        vector_store.add_documents(documents)
        logger.info("Documents ajoutés avec succès au vector store")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout des documents au vector store: {str(e)}")
        raise e
