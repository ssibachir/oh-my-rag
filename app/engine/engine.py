import os
from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.chat_engine import ContextChatEngine
from llama_index.llms.openai import OpenAI
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.embeddings.openai import OpenAIEmbedding

from app.engine.vectordb import get_vector_store

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

def get_chat_engine(filters=None, params=None, event_handlers=None):
    """Get a chat engine instance."""
    
    # Configurer le vector store et créer l'index
    vector_store = get_vector_store()
    index = VectorStoreIndex.from_vector_store(
        vector_store,
    )
    
    # Créer le retriever
    retriever = VectorIndexRetriever(
        index=index,
        filters=filters,
        similarity_top_k=2  # Nombre de documents similaires à récupérer
    )
    
    # Créer le chat engine
    chat_engine = ContextChatEngine.from_defaults(
        retriever=retriever,
        llm=Settings.llm,
        memory=ChatMemoryBuffer.from_defaults(token_limit=3900),
        system_prompt="Tu es un assistant qui répond aux questions en utilisant uniquement les informations fournies dans le contexte. Si tu ne trouves pas l'information dans le contexte, dis-le clairement."
    )
    
    return chat_engine
