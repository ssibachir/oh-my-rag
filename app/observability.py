import llama_index.core
import os
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

def init_observability():
    try:
        PHOENIX_API_KEY = os.getenv("PHOENIX_API_KEY")
        if not PHOENIX_API_KEY:
            raise ValueError("PHOENIX_API_KEY environment variable is not set")
            
        # Configuration de base pour LlamaTrace
        os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"api_key={PHOENIX_API_KEY}"
        
        # Initialiser LlamaIndex avec Phoenix
        llama_index.core.set_global_handler(
            "arize_phoenix", 
            endpoint="https://llamatrace.com/v1/traces"
        )
        
        # Obtenir le traceur pour les spans personnalisées
        tracer = trace.get_tracer(__name__)
        
        logger.info("Observability initialized successfully with LlamaTrace")
        return tracer
        
    except Exception as e:
        logger.error(f"Failed to initialize observability: {str(e)}")
        raise

def create_chat_span(tracer, conversation_id: str, user_message: str):
    """
    Crée un span pour suivre une interaction de chat
    """
    with tracer.start_as_current_span("chat_interaction") as span:
        span.set_attribute("conversation_id", conversation_id)
        span.set_attribute("user_message", user_message)
        return span

def end_chat_span(span, success: bool, response: str = None, error: str = None):
    """
    Termine un span de chat avec les résultats
    """
    if success:
        span.set_status(Status(StatusCode.OK))
        if response:
            span.set_attribute("assistant_response", response)
    else:
        span.set_status(Status(StatusCode.ERROR))
        if error:
            span.set_attribute("error", error)
    span.end()
