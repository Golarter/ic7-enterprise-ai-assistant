"""API REST del agente RAG. Inicialización diferida para inyección de dependencias en tests."""
import hmac
import json
import logging
import time
from pathlib import Path
from uuid import uuid4

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile, Request
from fastapi.responses import JSONResponse
from .agent import Agent
from .config import Settings
from .document import extract_text, chunks, document_id
from .llm import OllamaClient, OllamaUnavailable
from .schemas import AskRequest, AskResponse, HistoryItem, UploadResponse
from .storage import AuditStore, RequestsStore
from .vector import ChromaStore


class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({'level': record.levelname, 'message': record.getMessage(),
                           'logger': record.name}, ensure_ascii=False)


def create_app(settings: Settings | None = None, llm=None, vector=None) -> FastAPI:
    config = settings or Settings.from_env()
    config.data_dir.mkdir(parents=True, exist_ok=True)
    llm = llm or OllamaClient(config.ollama_url, config.chat_model, config.embed_model)
    vector = vector or ChromaStore(config.data_dir / 'chroma')
    audit = AuditStore(config.data_dir / 'audit.sqlite3')
    req_path = Path(__file__).resolve().parents[1] / 'data' / 'solicitudes_demo.json'
    requests_store = RequestsStore(req_path)
    agent = Agent(llm, vector, requests_store, config.min_similarity)

    app = FastAPI(title='Enterprise AI Assistant', version='1.0.0',
                  description='Prueba técnica: RAG empresarial y agente con herramientas, fuentes y auditoría')
    app.state.audit, app.state.vector = audit, vector

    @app.middleware('http')
    async def request_logging(request: Request, call_next):
        start = time.perf_counter()
        trace_id = str(uuid4())
        request.state.trace_id = trace_id
        try:
            response = await call_next(request)
        except Exception:
            logging.getLogger('enterprise').exception('request_error trace=%s', trace_id)
            raise
        logging.getLogger('enterprise').info('trace=%s path=%s status=%s latency_ms=%s',
            trace_id, request.url.path, response.status_code, round((time.perf_counter() - start) * 1000))
        response.headers['X-Trace-Id'] = trace_id
        return response

    def authorize(x_api_key: str | None = Header(default=None)):
        if not x_api_key or not hmac.compare_digest(x_api_key, config.api_key):
            raise HTTPException(401, 'Credenciales inválidas')

    @app.exception_handler(OllamaUnavailable)
    async def model_unavailable(_: Request, __: OllamaUnavailable):
        return JSONResponse(status_code=503, content={'detail': 'El proveedor de IA local no está disponible'})

    @app.get('/health')
    def health():
        return {'status': 'ok', 'vector_chunks': vector.count()}

    @app.get('/ready', dependencies=[Depends(authorize)])
    def ready():
        ok = llm.healthy()
        if not ok:
            raise HTTPException(503, 'Ollama no disponible')
        return {'status': 'ready', 'model': config.chat_model, 'embedding_model': config.embed_model}

    @app.post('/api/documents', response_model=UploadResponse, dependencies=[Depends(authorize)], status_code=201)
    async def upload_document(file: UploadFile = File(...)):
        filename = (file.filename or '').replace('\\', '/').split('/')[-1]
        if not filename or len(filename) > 160:
            raise HTTPException(422, 'Nombre inválido')
        from .document import ALLOWED
        if Path(filename).suffix.lower() not in ALLOWED:
            raise HTTPException(415, 'Extensión no permitida')
        content = await file.read(config.max_upload_bytes + 1)
        if len(content) > config.max_upload_bytes:
            raise HTTPException(413, 'Archivo supera el límite configurado')
        text = extract_text(filename, content)
        pieces = chunks(text)
        vectors = llm.embed(pieces)
        doc_id = document_id(content)
        vector.add(doc_id, filename, pieces, vectors)
        return UploadResponse(document_id=doc_id, name=filename, chunks=len(pieces))

    @app.post('/api/ask', response_model=AskResponse, dependencies=[Depends(authorize)])
    def ask(body: AskRequest, request: Request):
        session_id = body.session_id or uuid4().hex
        text, tools, sources = agent.answer(body.question)
        trace_id = request.state.trace_id
        audit.save(trace_id=trace_id, session_id=session_id, question=body.question,
                   answer=text, tools_used=tools, sources=sources)
        return AskResponse(answer=text, session_id=session_id, trace_id=trace_id,
                           tools_used=tools, sources=sources)

    @app.get('/api/history/{session_id}', response_model=list[HistoryItem], dependencies=[Depends(authorize)])
    def history(session_id: str):
        if len(session_id) > 80 or not session_id.replace('_', '').replace('-', '').isalnum():
            raise HTTPException(422, 'Identificador de sesión inválido')
        return audit.history(session_id)

    @app.get('/api/stats', dependencies=[Depends(authorize)])
    def stats():
        return {'interactions': audit.count(), 'indexed_chunks': vector.count()}

    return app


# `uvicorn app.main:app` inicializa el servicio con configuración real.
# En pruebas se usa create_app(...) sin conexión a Ollama.
app = None


def get_app():
    return create_app()
