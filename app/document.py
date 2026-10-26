"""Extracción, chunking con solapamiento y rechazo de contenido no legible."""
import hashlib
import io
import re
from pathlib import Path
from fastapi import HTTPException

ALLOWED = {'.txt', '.md', '.pdf'}


def extract_text(name: str, content: bytes) -> str:
    ext = Path(name).suffix.lower()
    if ext not in ALLOWED:
        raise HTTPException(415, 'Solo se permiten .txt, .md o .pdf')
    if ext == '.pdf':
        from pypdf import PdfReader
        try:
            reader = PdfReader(io.BytesIO(content))
            if reader.is_encrypted:
                raise HTTPException(422, 'PDF cifrado no soportado')
            text = '\n'.join(page.extract_text() or '' for page in reader.pages)
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(422, 'PDF inválido o ilegible') from exc
    else:
        try:
            text = content.decode('utf-8-sig')
        except UnicodeDecodeError as exc:
            raise HTTPException(422, 'El archivo debe estar codificado en UTF-8') from exc
    text = re.sub(r'[\t\r ]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    if len(text) < 40:
        raise HTTPException(422, 'Documento vacío o con texto insuficiente; no se aplica OCR')
    return text


def chunks(text: str, size: int = 900, overlap: int = 150) -> list[str]:
    assert size > overlap >= 0
    result = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            i = text.rfind(' ', start + int(size * .65), end)
            if i > start:
                end = i
        snippet = text[start:end].strip()
        if snippet:
            result.append(snippet)
        if end >= len(text):
            break
        start = max(start + 1, end - overlap)
    return result


def document_id(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()[:24]
