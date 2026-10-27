import os
from pathlib import Path
from fastapi.testclient import TestClient
from cloud_aws.api import create_cloud_app
from cloud_aws.gemini import GeminiClient
from cloud_aws.dynamo import _qencode, _qdecode
from app.storage import AuditStore
from app.agent import Agent
from app.storage import RequestsStore

class StubLLM:
    chat_model='stub-chat'
    embed_model='stub-embed'
    def __init__(self): self.calls=0
    def healthy(self): return True
    def embed(self, values): return [[0.1,0.9] for _ in values]
    def chat(self, messages, tools=None):
        self.calls+=1
        if self.calls%2==1 and tools:
            return {'tool_calls':[{'function':{'name':'consultar_solicitud','arguments':{'codigo':'SOL-1001'}}}]}
        return {'content':'La solicitud está en progreso.'}
class StubVector:
    def count(self): return 0
    def search(self,*a,**kw): return []
    def add(self,*args): pass

def test_cloud_healthy_without_configuration(monkeypatch):
    for k in ('APP_API_KEY','GEMINI_API_KEY','IC7_DOCS_TABLE','IC7_AUDIT_TABLE'):
        monkeypatch.delenv(k,raising=False)
    c=TestClient(create_cloud_app())
    assert c.get('/health').json()=={'status':'ok','platform':'aws-lambda','configured':False}
    assert c.post('/api/ask',json={'question':'Estado SOL-1001'}).status_code==401


def test_cloud_auth_tool_and_history(tmp_path, monkeypatch):
    monkeypatch.setenv(
        'APP_API_KEY',
        'test-key-long-enough-for-cloud'
    )

    app = create_cloud_app(
        llm=StubLLM(),
        vector=StubVector(),
        audit=AuditStore(tmp_path / 'traces.db')
    )

    c = TestClient(app)

    # Sin Cognito no hay acceso.
    assert c.post(
        '/api/ask',
        json={'question': 'SOL-1001'}
    ).status_code == 401

    # La API key anterior ya no autoriza solicitudes.
    r = c.post(
        '/api/ask',
        headers={
            'X-API-Key': os.getenv('APP_API_KEY')
        },
        json={
            'question': '¿Cómo va SOL-1001?',
            'session_id': 'test_aws'
        }
    )

    assert r.status_code == 401

    # Tampoco permite recuperar historiales.
    hist = c.get(
        '/api/history/test_aws',
        headers={
            'X-API-Key': os.getenv('APP_API_KEY')
        }
    )

    assert hist.status_code == 401


def test_quantized_embeddings_roundtrip():
    a=[0.7,-0.2,0.,0.4]
    recovered=_qdecode(_qencode(a))
    assert len(recovered)==4 and recovered[0]>0 and recovered[1]<0


def test_gemini_function_call_preserves_raw_parts(monkeypatch):
    fake=GeminiClient(key='fake',chat_model='gemini-2.5-flash')
    out=[]
    fake._post=lambda model, action, payload: (out.append(payload) or {
        'candidates':[{'content':{'parts':[{'functionCall':{'name':'consultar_solicitud','args':{'codigo':'SOL-1001'},'id':'abc'},'thoughtSignature':'signature'}]}}]})
    definitions=[{'type':'function','function':{'name':'consultar_solicitud','description':'Consulta','parameters':{'type':'object','properties':{'codigo':{'type':'string'}},'required':['codigo']}}}]
    resp=fake.chat([{'role':'system','content':'reglas'},{'role':'user','content':'estado SOL-1001'}],tools=definitions)
    assert resp['tool_calls'][0]['function']['name']=='consultar_solicitud'
    assert resp['provider_parts'][0]['thoughtSignature']=='signature'
    fake.chat([{'role':'system','content':'reglas'},{'role':'user','content':'estado SOL-1001'},
               {'role':'assistant','content':'','provider_parts':resp['provider_parts']},
               {'role':'tool','tool_name':'consultar_solicitud','tool_call_id':'abc','content':'{"estado":"abierto"}'}],tools=definitions)
    assert out[-1]['contents'][-2]['parts'][0]['thoughtSignature']=='signature'
    assert out[-1]['contents'][-1]['parts'][0]['functionResponse']['id']=='abc'
