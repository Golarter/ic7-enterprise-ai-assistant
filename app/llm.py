"""Cliente HTTP Ollama: embeddings y chat con tool calling, sin API de pago."""
import httpx


class OllamaUnavailable(RuntimeError):
    pass


class OllamaClient:
    def __init__(self, url: str, chat_model: str, embed_model: str):
        self.url, self.chat_model, self.embed_model = url, chat_model, embed_model

    def _post(self, path: str, payload: dict, timeout=120) -> dict:
        try:
            resp = httpx.post(self.url + path, json=payload, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise OllamaUnavailable('No se pudo conectar a Ollama o al modelo configurado') from exc

    def embed(self, values: list[str]) -> list[list[float]]:
        if not values:
            return []
        data = self._post('/api/embed', {'model': self.embed_model, 'input': values}, 120)
        vectors = data.get('embeddings', [])
        if len(vectors) != len(values):
            raise OllamaUnavailable('Ollama devolvió embeddings incompletos')
        return vectors

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        body = {'model': self.chat_model, 'messages': messages, 'stream': False, 'options': {'temperature': 0}}
        if tools:
            body['tools'] = tools
        return self._post('/api/chat', body, 180).get('message', {})

    def healthy(self):
        try:
            response = httpx.get(self.url + '/api/tags', timeout=3)
            return response.is_success
        except httpx.HTTPError:
            return False
