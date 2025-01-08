import json
import asyncio
import logging
from typing import AsyncGenerator, Dict, Any, List, Optional
from llama_index.core.callbacks.base import BaseCallbackHandler
from llama_index.core.callbacks.schema import CBEventType
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class CallbackEvent(BaseModel):
    event_type: CBEventType
    payload: Optional[Dict[str, Any]] = None
    event_id: str = ""

    def get_retrieval_message(self) -> dict | None:
        if self.payload and "nodes" in self.payload:
            nodes = self.payload["nodes"]
            return {
                "type": "events",
                "data": {"title": f"Trouvé {len(nodes)} sources pour la requête"}
            }
        return None

    def to_response(self):
        try:
            if self.event_type == "retrieve":
                return self.get_retrieval_message()
            return None
        except Exception as e:
            logger.error(f"Erreur de conversion: {e}")
            return None

class EventCallbackHandler(BaseCallbackHandler):
    _aqueue: asyncio.Queue
    is_done: bool = False

    def __init__(self):
        ignored_events = [CBEventType.CHUNKING, CBEventType.NODE_PARSING, 
                         CBEventType.EMBEDDING, CBEventType.LLM]
        super().__init__(ignored_events, ignored_events)
        self._aqueue = asyncio.Queue()

    def on_event_start(self, event_type: CBEventType, payload: Dict[str, Any] = None, 
                      event_id: str = "", **kwargs) -> str:
        event = CallbackEvent(event_type=event_type, payload=payload, event_id=event_id)
        if event.to_response():
            self._aqueue.put_nowait(event)
        return event_id

    def on_event_end(self, event_type: CBEventType, payload: Dict[str, Any] = None,
                    event_id: str = "", **kwargs) -> None:
        event = CallbackEvent(event_type=event_type, payload=payload, event_id=event_id)
        if event.to_response():
            self._aqueue.put_nowait(event)

    def start_trace(self, trace_id: Optional[str] = None) -> None:
        """Démarrer le traçage."""
        pass

    def end_trace(self, trace_id: Optional[str] = None, 
                 trace_map: Optional[Dict[str, List[str]]] = None) -> None:
        """Terminer le traçage."""
        pass

    async def async_event_gen(self) -> AsyncGenerator[CallbackEvent, None]:
        while not self._aqueue.empty() or not self.is_done:
            try:
                yield await asyncio.wait_for(self._aqueue.get(), timeout=0.1)
            except asyncio.TimeoutError:
                pass 