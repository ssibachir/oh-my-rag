import logging
from typing import Any, Dict, List

import yaml  # type: ignore
from app.engine.loaders.db import DBLoaderConfig, get_db_documents
from app.engine.loaders.file import FileLoaderConfig, get_file_documents
from app.engine.loaders.web import WebLoaderConfig, get_web_documents
from llama_index.core import Document

logger = logging.getLogger(__name__)

# Liste des extensions de fichiers supportées
SUPPORTED_EXTENSIONS = {
    '.pdf',      # Documents PDF
    '.txt',      # Fichiers texte
    '.md',       # Markdown
    '.docx',     # Microsoft Word
    '.doc',      # Microsoft Word (ancien format)
    '.csv',      # Fichiers CSV
    '.xlsx',     # Microsoft Excel
    '.xls',      # Microsoft Excel (ancien format)
    '.json',     # Fichiers JSON
    '.html',     # Pages web
    '.htm'       # Pages web (ancien format)
}

def load_configs() -> Dict[str, Any]:
    """
    Charge les configurations des chargeurs de documents à partir d'un fichier YAML.

    Le fichier de configuration spécifie les paramètres nécessaires pour différents types de chargeurs,
    tels que les fichiers, le web, ou les bases de données.

    Retourne:
        Dict[str, Any]: Un dictionnaire contenant les configurations des chargeurs.
    """
    with open("config/loaders.yaml") as f:
        configs = yaml.safe_load(f)
    return configs

def get_documents() -> List[Document]:
    """
    Récupère une liste de documents à partir des sources configurées.

    Cette fonction parcourt les types de chargeurs définis dans les configurations, tels que les fichiers,
    le web et les bases de données, pour collecter les documents. Chaque type de chargeur utilise
    une configuration spécifique pour extraire les documents correspondants.

    Retourne:
        List[Document]: Une liste de documents extraits depuis les sources configurées.

    Lève:
        ValueError: Si un type de chargeur invalide est spécifié dans les configurations.
    """
    documents = []
    config = load_configs()
    for loader_type, loader_config in config.items():
        logger.info(
            f"Chargement des documents depuis le chargeur : {loader_type}, configuration : {loader_config}"
        )
        match loader_type:
            case "file":
                document = get_file_documents(FileLoaderConfig(**loader_config))
            case "web":
                document = get_web_documents(WebLoaderConfig(**loader_config))
            case "db":
                document = get_db_documents(
                    configs=[DBLoaderConfig(**cfg) for cfg in loader_config]
                )
            case _:
                raise ValueError(f"Type de chargeur invalide : {loader_type}")
        documents.extend(document)

    return documents
