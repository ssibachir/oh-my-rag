# flake8: noqa: E402
from dotenv import load_dotenv

load_dotenv()

import logging
import os

from llama_index.core.ingestion import DocstoreStrategy, IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.settings import Settings
from llama_index.core.storage import StorageContext
from llama_index.core.storage.docstore import SimpleDocumentStore

from app.engine.loaders import get_documents
from app.engine.vectordb import get_vector_store, add_documents_to_vectorstore, get_collection_stats
from app.settings import init_settings

from typing import Optional
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

STORAGE_DIR = os.getenv("STORAGE_DIR", "storage")

def get_doc_store():
    """
    Récupère ou crée un magasin de documents.

    Si le répertoire de stockage existe, charge le magasin de documents à partir de celui-ci.
    Sinon, crée un magasin de documents en mémoire.

    Retourne:
        SimpleDocumentStore: Une instance du magasin de documents.
    """
    if os.path.exists(STORAGE_DIR):
        return SimpleDocumentStore.from_persist_dir(STORAGE_DIR)
    else:
        return SimpleDocumentStore()

def run_pipeline(docstore, vector_store, documents):
    """
    Exécute le pipeline d'ingestion pour traiter et stocker les documents.

    Le pipeline applique un diviseur de phrases et un modèle d'embedding pour transformer
    les documents en noeuds, qui sont ensuite stockés dans le magasin de documents et le magasin de vecteurs.

    Arguments:
        docstore (SimpleDocumentStore): Le magasin de documents pour stocker les noeuds.
        vector_store: Le magasin de vecteurs pour stocker les embeddings.
        documents (list): Une liste de documents à traiter.

    Retourne:
        list: Une liste de noeuds générés par le pipeline.
    """
    pipeline = IngestionPipeline(
        transformations=[
            SentenceSplitter(
                chunk_size=Settings.chunk_size,
                chunk_overlap=Settings.chunk_overlap,
            ),
            Settings.embed_model,
        ],
        docstore=docstore,
        docstore_strategy=DocstoreStrategy.UPSERTS_AND_DELETE,  # type: ignore
        vector_store=vector_store,
    )

    # Exécute le pipeline d'ingestion et stocke les résultats
    nodes = pipeline.run(show_progress=True, documents=documents)

    return nodes

def persist_storage(docstore, vector_store):
    """
    Persiste les magasins de documents et de vecteurs sur le disque.

    Arguments:
        docstore (SimpleDocumentStore): Le magasin de documents à persister.
        vector_store: Le magasin de vecteurs à persister.
    """
    storage_context = StorageContext.from_defaults(
        docstore=docstore,
        vector_store=vector_store,
    )
    storage_context.persist(STORAGE_DIR)

def generate_datasource():
    """
    Fonction principale pour générer l'index pour les données fournies.

    Cette fonction initialise les paramètres, récupère les documents, les traite via
    le pipeline d'ingestion et persiste les magasins de documents et de vecteurs résultants.
    """
    init_settings()
    logger.info("Génération de l'index pour les données fournies")

    # Récupère les magasins et les documents ou en crée de nouveaux
    documents = get_documents()
    # Définit private=false pour marquer le document comme public (nécessaire pour le filtrage)
    for doc in documents:
        doc.metadata["private"] = "false"
    docstore = get_doc_store()
    vector_store = get_vector_store()

    # Exécute le pipeline d'ingestion
    _ = run_pipeline(docstore, vector_store, documents)

    # Crée l'index et persiste le stockage
    persist_storage(docstore, vector_store)

    logger.info("Fin de la génération de l'index")

async def process_documents(specific_file: Optional[str] = None):
    """
    Traite et indexe les documents.
    """
    try:
        logger.info(f"Début du traitement {'du fichier ' + specific_file if specific_file else 'des documents'}")
        
        # Initialiser les paramètres
        init_settings()
        logger.info("Paramètres initialisés")

        # Obtenir le vector store existant
        vector_store = get_vector_store()
        
        # Log des stats avant
        stats_before = get_collection_stats(vector_store)
        logger.info(f"Stats avant indexation:")
        logger.info(f"Collection '{stats_before['collection_name']}' - "
                   f"Points: {stats_before['points_count']}, "
                   f"Segments: {stats_before['segments_count']}")

        if specific_file:
            if not os.path.exists(specific_file):
                logger.error(f"Fichier non trouvé: {specific_file}")
                raise FileNotFoundError(f"Le fichier {specific_file} n'existe pas")
            
            logger.info(f"Chargement du fichier: {specific_file}")
            new_documents = SimpleDirectoryReader(
                input_files=[specific_file]
            ).load_data()
            logger.info(f"Fichier chargé avec succès: {len(new_documents)} document(s)")

            # Marquer les nouveaux documents comme publics
            for doc in new_documents:
                doc.metadata["private"] = "false"
                doc.metadata["source"] = specific_file  # Ajouter la source
            logger.info("Métadonnées des documents mises à jour")

            # Créer un pipeline d'ingestion pour les nouveaux documents
            pipeline = IngestionPipeline(
                transformations=[
                    SentenceSplitter(
                        chunk_size=Settings.chunk_size,
                        chunk_overlap=Settings.chunk_overlap,
                    ),
                    Settings.embed_model,
                ],
                vector_store=vector_store
            )

            # Exécuter le pipeline d'ingestion
            logger.info("Début de l'ingestion des nouveaux documents")
            nodes = pipeline.run(
                documents=new_documents,
                show_progress=True
            )
            logger.info(f"Ingestion terminée: {len(nodes)} nœuds générés")
            
            # Log des stats après
            stats_after = get_collection_stats(vector_store)
            logger.info(f"Après indexation - "
                       f"Points: {stats_after['points_count']} (+{stats_after['points_count'] - stats_before['points_count']}), "
                       f"Segments: {stats_after['segments_count']}")

        else:
            # Pour une réindexation complète
            logger.warning("Réindexation complète demandée")
            documents = get_documents()
            for doc in documents:
                doc.metadata["private"] = "false"
            
            # Recréer l'index complet
            vector_store = get_vector_store(force_recreate=True)
            pipeline = IngestionPipeline(
                transformations=[
                    SentenceSplitter(
                        chunk_size=Settings.chunk_size,
                        chunk_overlap=Settings.chunk_overlap,
                    ),
                    Settings.embed_model,
                ],
                vector_store=vector_store
            )
            nodes = pipeline.run(documents=documents, show_progress=True)
        
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement des documents: {str(e)}", exc_info=True)
        raise e

if __name__ == "__main__":
    generate_datasource()