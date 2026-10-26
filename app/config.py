from dataclasses import dataclass
from pathlib import Path
import os


def _load_dotenv() -> None:
    path = Path('.env')
    if not path.exists():
        return
    for line in path.read_text(encoding='utf-8').splitlines():
        if '=' in line and not line.strip().startswith('#'):
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())


@dataclass(frozen=True)
class Settings:
    api_key: str
    ollama_url: str
    chat_model: str
    embed_model: str
    data_dir: Path
    max_upload_bytes: int = 5 * 1024 * 1024
    min_similarity: float = 0.22

    @classmethod
    def from_env(cls):
        _load_dotenv()
        key = os.getenv('APP_API_KEY', '')
        if len(key) < 20 or key.startswith('reemplazar'):
            raise RuntimeError('Configura APP_API_KEY con al menos 20 caracteres aleatorios')
        return cls(
            api_key=key,
            ollama_url=os.getenv('OLLAMA_URL', 'http://127.0.0.1:11434').rstrip('/'),
            chat_model=os.getenv('OLLAMA_CHAT_MODEL', 'qwen3:4b-instruct'),
            embed_model=os.getenv('OLLAMA_EMBED_MODEL', 'embeddinggemma'),
            data_dir=Path(os.getenv('DATA_DIR', './data')),
            max_upload_bytes=int(os.getenv('MAX_UPLOAD_BYTES', str(5 * 1024 * 1024))),
            min_similarity=float(os.getenv('MIN_SIMILARITY', '.22')),
        )
