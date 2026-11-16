"""Shared local Chroma connection and cached default MiniLM embedding model."""
import os
from functools import cached_property, lru_cache

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


class _OneThreadMiniLM(ONNXMiniLM_L6_V2):
    """Chroma's default MiniLM model, limited to one ONNX thread.

    By default ONNX Runtime starts one thread per physical core of the host machine. In a
    container limited to a fraction of a CPU (Render free: 0.1) those threads fight for the
    same slice and a single search took ~5 s. Same model and name, so existing indexes match.
    """

    @cached_property
    def model(self):
        options = self.ort.SessionOptions()
        options.log_severity_level = 3
        options.graph_optimization_level = self.ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        options.intra_op_num_threads = 1
        options.inter_op_num_threads = 1
        return self.ort.InferenceSession(
            os.path.join(self.DOWNLOAD_PATH, self.EXTRACTED_FOLDER_NAME, "model.onnx"),
            providers=self._preferred_providers, sess_options=options)


@lru_cache(maxsize=1)
def _embedding_function():
    return _OneThreadMiniLM(preferred_providers=["CPUExecutionProvider"])
