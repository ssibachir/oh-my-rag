import os
from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.chat_engine import ContextChatEngine
from llama_index.llms.openai import OpenAI
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.embeddings.openai import OpenAIEmbedding

from app.engine.vectordb import get_vector_store
from app.settings import init_settings

# Configuration globale de LlamaIndex
Settings.llm = OpenAI(
    model="gpt-4",
    temperature=0.7,
    api_key=os.getenv("OPENAI_API_KEY")
)

# Configuration des embeddings
Settings.embed_model = OpenAIEmbedding(
    model="text-embedding-3-small",
    api_key=os.getenv("OPENAI_API_KEY")
)

def get_chat_engine(filters=None):
    """
    Crée et retourne un moteur de chat configuré pour le streaming et le RAG.
    
    Args:
        filters: Filtres optionnels pour la recherche de documents
    """
    # Initialiser les paramètres
    init_settings()
    
    # Créer l'index avec le vector store existant
    vector_store = get_vector_store()
    index = VectorStoreIndex.from_vector_store(vector_store)
    
    # Créer le retriever avec les paramètres optimisés
    retriever = VectorIndexRetriever(
        index=index,
        filters=filters,
        similarity_top_k=1,  # Nombre de documents similaires à récupérer
        similarity_cutoff=0.1  # Seuil minimal de similarité abaissé
    )
    
    # Créer le chat engine avec le retriever et la mémoire
    chat_engine = ContextChatEngine.from_defaults(
        retriever=retriever,
        llm=Settings.llm,
        memory=ChatMemoryBuffer.from_defaults(token_limit=3900),
        system_prompt="""Tu es un assistant qui répond aux questions en utilisant uniquement les informations fournies dans le contexte. 
        Si tu trouves l'information dans le contexte, utilise-la et cite ta source.
        Si tu ne trouves pas l'information dans le contexte, dis-le clairement.""",
        verbose=True,
        # Paramètres pour améliorer la pertinence
        node_postprocessors=[],  # Désactiver les post-processeurs qui pourraient affecter les scores
        similarity_score_threshold=0.1  # Seuil de score pour considérer un document comme pertinent
    )
    
    # Activer le streaming sur le chat engine
    chat_engine.streaming = True
    
    return chat_engine
