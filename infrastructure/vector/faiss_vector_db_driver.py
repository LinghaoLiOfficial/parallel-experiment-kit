import pickle
from pathlib import Path

import faiss
import numpy as np

from infrastructure.logging.logger import get_logger


logger = get_logger(__name__)


class FAISSVectorDBDriver:
    def __init__(self, file_save_path: str, resume=False, dimension=1024, index_type="flat"):
        self.file_save_path = Path(file_save_path)
        self.index_file_save_path = self.file_save_path.with_suffix(".faiss")
        self.metadata_file_save_path = self.file_save_path.with_suffix(".pkl")
        self.dimension = dimension
        self.index_type = index_type
        self.index = None
        self.ids = []
        if resume:
            self.read()

    def search(self, query_vectors, k=5):
        if self.index_type == "flat_ip":
            faiss.normalize_L2(query_vectors)
        distances, indices = self.index.search(query_vectors, k)
        results = []
        for i in range(len(query_vectors)):
            query_results = []
            for j in range(k):
                idx = indices[i][j]
                if idx != -1:
                    query_results.append({"id": self.ids[idx], "index": idx, "distance": float(distances[i][j])})
            results.append(query_results)
        return results

    def insert(self, vectors: np.ndarray, ids: list | None = None):
        if self.index is None:
            self._create_index()
        n_vectors = vectors.shape[0]
        if ids is None:
            start_id = len(self.ids)
            ids = list(range(start_id, start_id + n_vectors))
        if self.index_type == "flat_ip":
            faiss.normalize_L2(vectors)
        self.index.add(vectors)
        self.ids.extend(ids)
        self.save()

    def read(self):
        try:
            if self.index_file_save_path.exists():
                self.index = faiss.read_index(str(self.index_file_save_path))
                with open(str(self.metadata_file_save_path), "rb") as file:
                    metadata = pickle.load(file)
                self.ids = metadata["ids"]
                self.dimension = metadata["dimension"]
                self.index_type = metadata["index_type"]
        except Exception as exc:
            logger.warning(f"FAISSVectorDBDriver read func error, e={exc}")

    def save(self):
        if self.index is None:
            self._create_index()
        try:
            faiss.write_index(self.index, str(self.index_file_save_path))
            metadata = {"ids": self.ids, "dimension": self.dimension, "index_type": self.index_type}
            with open(str(self.metadata_file_save_path), "wb") as file:
                pickle.dump(metadata, file)
        except Exception as exc:
            logger.warning(f"FAISSVectorDBDriver save func error, e={exc}")

    def _create_index(self, ivf_nlist=100, hnsw_m=32):
        index_mapping = {
            "flat": lambda: faiss.IndexFlatL2(self.dimension),
            "flat_ip": lambda: faiss.IndexFlatIP(self.dimension),
            "ivf": lambda: faiss.IndexIVFFlat(faiss.IndexFlatL2(self.dimension), self.dimension, ivf_nlist),
            "hnsw": lambda: faiss.IndexHNSWFlat(self.dimension, hnsw_m),
        }
        self.index = index_mapping.get(self.index_type)()
