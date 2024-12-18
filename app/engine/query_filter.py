from llama_index.core.vector_stores.types import MetadataFilter, MetadataFilters


def generate_filters(doc_ids=None):
    """Generate filters for the query engine."""
    if not doc_ids:
        return None
    
    return {
        "doc_id": {"$in": doc_ids}
    }
