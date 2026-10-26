"""ChromaDB local persistente; cada fragmento conserva procedencia verificable."""
from pathlib import Path


class ChromaStore:
    def __init__(self, directory: Path):
        import chromadb  # dependencia diferida: facilita las pruebas unitarias aisladas
        directory.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(directory))
        self.collection = client.get_or_create_collection('solicitudes_conocimiento', metadata={'hnsw:space': 'cosine'})

    def add(self, doc_id: str, name: str, parts: list[str], embeddings: list[list[float]]) -> None:
        if len(parts) != len(embeddings):
            raise ValueError('Dimensiones de chunks y embeddings inconsistentes')
        ids = [f'{doc_id}:{i}' for i in range(len(parts))]
        self.collection.upsert(ids=ids, documents=parts, embeddings=embeddings,
                               metadatas=[{'document_id': doc_id, 'source': name, 'chunk': i + 1} for i in range(len(parts))])

    def search(self, vector: list[float], count: int = 4, min_similarity: float = 0.22):
        total = self.collection.count()
        if total == 0:
            return []
        hits = self.collection.query(query_embeddings=[vector], n_results=min(count, total),
                                     include=['documents', 'metadatas', 'distances'])
        out = []
        for text, meta, distance in zip(hits['documents'][0], hits['metadatas'][0], hits['distances'][0]):
            similarity = 1.0 - float(distance)
            if similarity >= min_similarity:
                out.append({'document': meta['source'], 'chunk': meta['chunk'],
                            'excerpt': text, 'similarity': round(similarity, 4)})
        return out

    def count(self):
        return self.collection.count()
