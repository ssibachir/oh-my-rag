from supabase import create_client, Client
import os
from dotenv import load_dotenv
import logging
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

# Charger le .env depuis le répertoire racine du projet
project_root = Path(__file__).parent.parent.parent
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path)

class SupabaseClient:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not self.url or not self.key:
            logger.error(f"URL: {self.url}, KEY: {'présente' if self.key else 'absente'}")
            raise ValueError("SUPABASE_URL et SUPABASE_SERVICE_KEY sont requis")
        
        self.client: Client = create_client(self.url, self.key)
    
    async def select(self, table: str, query: dict = None) -> list:
        try:
            response = self.client.table(table).select("*")
            if query and 'email' in query:
                response = response.eq('email', query['email'].split('eq.')[1])
            elif query and 'id' in query:
                response = response.eq('id', query['id'].split('eq.')[1])
            
            data = response.execute()
            return data.data
        except Exception as e:
            logger.error(f"Erreur select: {str(e)}")
            raise
    
    async def insert(self, table: str, data: dict) -> dict:
        try:
            sanitized_data = {}
            for key, value in data.items():
                if isinstance(value, uuid.UUID):
                    sanitized_data[key] = str(value)
                else:
                    sanitized_data[key] = value
            
            response = self.client.table(table).insert(sanitized_data).execute()
            return response.data
        except Exception as e:
            logger.error(f"Erreur insert: {str(e)}")
            logger.error(f"Type de l'erreur: {type(e)}")
            raise

    def from_(self, table: str):
        return self.client.table(table)

# Instance unique de SupabaseClient
supabase = SupabaseClient() 