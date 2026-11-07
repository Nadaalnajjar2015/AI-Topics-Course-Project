"""Shared local Chroma connection and cached default MiniLM embedding model."""
from functools import lru_cache

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2

from part2_knowledge.common.config import settings


def _client():
    return chromadb.PersistentClient(path=str(settings.chroma_dir),
                                    settings=ChromaSettings(anonymized_telemetry=False))


@lru_cache(maxsize=1)
def _embedding_function():
    return ONNXMiniLM_L6_V2(preferred_providers=["CPUExecutionProvider"])
