This is a [LlamaIndex](https://www.llamaindex.ai/) project using [FastAPI](https://fastapi.tiangolo.com/) bootstrapped with [`create-llama`](https://github.com/run-llama/LlamaIndexTS/tree/main/packages/create-llama).

## Project Workflow & Architecture

### Core Components

#### 1. Data Ingestion & Indexing
- `app/engine/generate.py`: Point d'entrée pour l'indexation des documents
- `app/engine/loaders/__init__.py`: Gère le chargement des documents depuis le dossier `data/`
- `app/engine/vectordb.py`: Configure la connexion avec Qdrant (base de données vectorielle)

#### 2. RAG Engine
- `app/engine/engine.py`: Cœur du système RAG
  - Configure OpenAI (LLM et embeddings)
  - Crée le chat engine qui combine :
    - Recherche de documents pertinents
    - Génération de réponses contextuelles
- `app/engine/query_filter.py`: Gère le filtrage des documents lors des requêtes

#### 3. API Layer
- `app/api/app.py`: Configuration principale de FastAPI
- `app/api/routers/chat.py`: Endpoints pour le chat
  - `/api/chat/request`: Endpoint non-streaming
  - `/api/chat`: Endpoint streaming

#### 4. Frontend
- `static/index.html`: Interface utilisateur simple
  - Chat interface
  - Communication avec l'API

### Workflow Typique

1. **Préparation des Données**
   ```bash
   # Placez vos documents dans le dossier data/
   # Générez les embeddings et indexez les documents
   poetry run generate
   ```

2. **Démarrage du Serveur**
   ```bash
   # Démarrez le serveur de développement
   poetry run dev
   ```

3. **Interaction**
   - Accédez à `http://localhost:8000`
   - Posez des questions via l'interface
   - Le système :
     1. Recherche les passages pertinents dans Qdrant
     2. Utilise GPT-4 pour générer une réponse contextuelle

### Configuration
- `.env`: Variables d'environnement
  - Clés API (OpenAI, Qdrant)
  - Configuration des modèles
  - Paramètres du serveur
- `config/tools.yaml`: Configuration des outils disponibles
- `config/loaders.yaml`: Configuration des chargeurs de documents

## Getting Started

First, setup the environment with poetry:

> **_Note:_** This step is not needed if you are using the dev-container.

```
poetry install
poetry shell
```

Then check the parameters that have been pre-configured in the `.env` file in this directory. (E.g. you might need to configure an `OPENAI_API_KEY` if you're using OpenAI as model provider).

If you are using any tools or data sources, you can update their config files in the `config` folder.

Second, generate the embeddings of the documents in the `./data` directory:

```
poetry run generate
```

Third, run the app:

```
poetry run dev
```

Open [http://localhost:8000](http://localhost:8000) with your browser to start the app.

The example provides two different API endpoints:

1. `/api/chat` - a streaming chat endpoint
2. `/api/chat/request` - a non-streaming chat endpoint

You can test the streaming endpoint with the following curl request:

```
curl --location 'localhost:8000/api/chat' \
--header 'Content-Type: application/json' \
--data '{ "messages": [{ "role": "user", "content": "Hello" }] }'
```

And for the non-streaming endpoint run:

```
curl --location 'localhost:8000/api/chat/request' \
--header 'Content-Type: application/json' \
--data '{ "messages": [{ "role": "user", "content": "Hello" }] }'
```

You can start editing the API endpoints by modifying `app/api/routers/chat.py`. The endpoints auto-update as you save the file. You can delete the endpoint you're not using.

To start the app optimized for **production**, run:

```
poetry run prod
```

## Deployments

For production deployments, check the [DEPLOY.md](DEPLOY.md) file.

## Learn More

To learn more about LlamaIndex, take a look at the following resources:

- [LlamaIndex Documentation](https://docs.llamaindex.ai) - learn about LlamaIndex.

You can check out [the LlamaIndex GitHub repository](https://github.com/run-llama/llama_index) - your feedback and contributions are welcome!
