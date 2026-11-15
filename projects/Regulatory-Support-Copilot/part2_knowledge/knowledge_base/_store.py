"""Shared local Chroma connection and cached default MiniLM embedding model."""
from functools import lru_cache

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2

from part2_knowledge.common.config import settings


def _client():
    return _client_for(str(settings.chroma_dir))


@lru_cache(maxsize=8)
def _client_for(path: str):
    """One client per index folder: building a client re-reads settings and costs ~60 ms locally
    (seconds on a 0.1-CPU free host), so creating one per search made every search slow."""
    return chromadb.PersistentClient(path=path, settings=ChromaSettings(anonymized_telemetry=False))


@lru_cache(maxsize=1)
def _embedding_function():
    return ONNXMiniLM_L6_V2(preferred_providers=["CPUExecutionProvider"])
