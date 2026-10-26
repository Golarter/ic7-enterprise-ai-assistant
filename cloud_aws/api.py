"""API cloud RAG: mismas rutas que la app local con adaptadores externos."""
import hmac
import logging
import os
import time
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Depends, HTTPException, Request, Header, File, UploadFile
from fastapi.responses import JSONResponse

from app.agent import Agent
from app.document import extract_text, chunks, document_id, ALLOWED
from app.schemas import AskRequest, AskResponse, HistoryItem, UploadResponse
from app.storage import RequestsStore
from cloud_aws.gemini import GeminiUnavailable
from cloud_aws.gemini import GeminiClient
from cloud_aws.dynamo import DynamoVectorStore, DynamoAuditStore

log = logging.getLogger('enterprise.aws')


def create_cloud_app(llm=None, vector=None, audit=None):
    app = FastAPI(title='Enterprise AI Assistant - AWS', version='1.1.0',
                  description='RAG y agente con herramientas para AWS Lambda')

    # Construcción diferida: /health responde antes de crear tablas y claves.
    def services():
        if not hasattr(app.state, 'services'):
            if llm is not None and vector is not None and audit is not None:
                model, index, history = llm, vector, audit
            else:
                if not os.getenv('GEMINI_API_KEY'):
                    raise HTTPException(503,'Configurar GEMINI_API_KEY en Lambda antes de consultar')
                if not os.getenv('IC7_DOCS_TABLE') or not os.getenv('IC7_AUDIT_TABLE'):
                    raise HTTPException(503,'Configurar las dos tablas de DynamoDB antes de consultar')
                import boto3
                db = boto3.resource('dynamodb')
                model = GeminiClient()
                index = DynamoVectorStore(db.Table(os.environ['IC7_DOCS_TABLE']))
                history = DynamoAuditStore(db.Table(os.environ['IC7_AUDIT_TABLE']))
            store = RequestsStore(Path(__file__).resolve().parents[1]/'data'/'solicitudes_demo.json')
            app.state.services = (model, index, history, Agent(model,index,store,.22))
        return app.state.services

    def authorize(x_api_key: str | None = Header(None)):
        expected = os.getenv('APP_API_KEY','')
        if len(expected)<20:
            raise HTTPException(503,'Configurar APP_API_KEY antes de abrir la API')
        if not x_api_key or not hmac.compare_digest(x_api_key,expected):
            raise HTTPException(401,'Credenciales inválidas')

    @app.middleware('http')
    async def access_log(request:Request, call_next):
        trace = str(uuid4())
        request.state.trace_id = trace
        start = time.perf_counter()
        try:
            resp = await call_next(request)
        except Exception:
            log.exception('lambda_request_error trace=%s',trace)
            raise
        log.info('trace=%s path=%s status=%s latency_ms=%.0f',trace,request.url.path,
                 resp.status_code,(time.perf_counter()-start)*1000)
        resp.headers['X-Trace-Id'] = trace
        return resp

    @app.exception_handler(GeminiUnavailable)
    async def llm_error(_:Request, __:GeminiUnavailable):
        return JSONResponse(status_code=503,content={'detail':'Proveedor de IA no disponible'})

    @app.get('/health')
    def health():
        return {'status':'ok','platform':'aws-lambda','configured':
                bool(os.getenv('APP_API_KEY') and os.getenv('GEMINI_API_KEY')
                     and os.getenv('IC7_DOCS_TABLE') and os.getenv('IC7_AUDIT_TABLE'))}

    @app.get('/ready', dependencies=[Depends(authorize)])
    def ready():
        model,_,__,___ = services()
        return {'status':'ready' if model.healthy() else 'not_ready', 'model':model.chat_model,
                'embedding_model':model.embed_model}

    @app.post('/api/documents',response_model=UploadResponse, status_code=201,
              dependencies=[Depends(authorize)])
    async def upload(file:UploadFile=File(...)):
        filename = (file.filename or '').replace('\\','/').split('/')[-1]
        if not filename or len(filename)>160:
            raise HTTPException(422,'Nombre inválido')
        if Path(filename).suffix.lower() not in ALLOWED:
            raise HTTPException(415,'Extensión no permitida')
        data = await file.read(256 * 1024 + 1)
        if len(data)>256*1024:
            raise HTTPException(413,'Máximo 256 KB en la demo AWS')
        text = extract_text(filename,data)
        parts = chunks(text)
        if len(parts)>12:
            raise HTTPException(413,'Máximo 12 fragmentos en la demo AWS')
        model,index,_,__=services()
        vectors=model.embed(parts)
        try:
            index.add(document_id(data),filename,parts,vectors)
        except Exception as exc:
            # Duplicados -> idempotencia de subida: el propio ID deriva de los bytes.
            if exc.__class__.__name__ != 'ConditionalCheckFailedException':
                raise
        return UploadResponse(document_id=document_id(data),name=filename,chunks=len(parts))

    @app.post('/api/ask',response_model=AskResponse,dependencies=[Depends(authorize)])
    def ask(body:AskRequest, request:Request):
        session_id=body.session_id or uuid4().hex
        model,index,history,agent=services()
        text,tools,sources=agent.answer(body.question)
        trace=request.state.trace_id
        history.save(trace_id=trace,session_id=session_id,question=body.question,
                     answer=text,tools_used=tools,sources=sources)
        return AskResponse(answer=text,session_id=session_id,trace_id=trace,
                           tools_used=tools,sources=sources)

    @app.get('/api/history/{session_id}',response_model=list[HistoryItem],
             dependencies=[Depends(authorize)])
    def get_history(session_id:str):
        if len(session_id)>80 or not session_id.replace('_','').replace('-','').isalnum():
            raise HTTPException(422,'Identificador inválido')
        return services()[2].history(session_id)

    @app.get('/api/stats',dependencies=[Depends(authorize)])
    def stats():
        _,vector,audit,_=services()
        return {'indexed_chunks_bounded':vector.count(), 'interactions_approximate':audit.count()}

    return app
