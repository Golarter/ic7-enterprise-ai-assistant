"""Request-scoped DynamoDB boundary. Never cache across users."""

class ScopedVector:
    def __init__(self, underlying, owner):
        self.underlying = underlying
        self.owner = owner

    def search(self, vector, count=4, min_similarity=0.22):
        return self.underlying.search(
            vector, count=count, min_similarity=min_similarity, owner=self.owner
        )

    def add(self, doc_id, name, parts, embeddings):
        return self.underlying.add(
            doc_id, name, parts, embeddings, owner=self.owner
        )

    def count(self):
        return self.underlying.count(owner=self.owner)
