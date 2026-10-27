"""Fast documentary path and bounded Gemini REST requests."""
import json
from app.agent import Agent
from cloud_aws.gemini import GeminiClient, GeminiUnavailable, gemini_request_budget
from cloud_aws import gemini

class StubModel:
    def __init__(self): self.calls=[]; self.embeddings=[]
    def embed(self, values):
        self.embeddings.extend(values)
        return [[0.7, 0.3] for _ in values]
    def chat(self, messages, tools=None):
        self.calls.append((messages,tools))
        return {'content':'Reinicia el cliente VPN [F1].'}

class StubVector:
    def search(self, vector, **kw):
        return [{'document':'vpn.md','chunk':1,'excerpt':'Reinicia el cliente VPN una vez.', 'similarity':.91}]

class StubRequests:
    def get(self, code):
        return {'codigo':code, 'estado':'En progreso'}

def test_document_question_one_chat_and_one_embedding():
    m=StubModel(); agent=Agent(m,StubVector(),StubRequests())
    answer,tools,sources=agent.answer('¿Cuál es el procedimiento para recuperar acceso a VPN?')
    assert len(m.calls)==1 and m.calls[0][1] is None
    assert len(m.embeddings)==1
    assert tools==['buscar_documentacion']
    assert '[F1]' in answer and sources[0]['document']=='vpn.md'

def test_solicitud_keeps_agent_tool_router():
    assert not Agent._documentary_intent('Consulta la solicitud SOL-1001 sobre VPN')
    assert not Agent._documentary_intent('Clasifica la prioridad de una fuga de datos')

def test_document_abstention_without_evidence():
    class EmptyVector:
        def search(self,*args,**kwargs):return []
    m=StubModel(); agent=Agent(m,EmptyVector(),StubRequests())
    answer,tools,sources=agent.answer('Procedimiento para VPN')
    assert 'No encontré información suficiente' in answer
    assert len(m.calls)==0 and not sources

def test_document_wrong_reference_rejected():
    m=StubModel()
    m.chat=lambda *args,**kwargs:{'content':'Instrucciones [F9].'}
    answer,_,sources=Agent(m,StubVector(),StubRequests()).answer('Procedimiento VPN')
    assert 'No encontré información suficiente' in answer and sources==[]

def test_gemini_budget_deadline_without_network(monkeypatch):
    client=GeminiClient(key='fake')
    calls=[]
    class Response:
        def __enter__(self):return self
        def __exit__(self,*a):return False
        def read(self):return json.dumps({'embedding':{'values':[0.1]*128}}).encode()
    def fake(req,timeout):
        calls.append(timeout)
        return Response()
    monkeypatch.setattr(gemini.request,'urlopen',fake)
    with gemini_request_budget(26):
        client.embed(['vpn'])
    assert len(calls)==1 and 0<calls[0]<=12

def test_gemini_budget_exhaustion_fails_before_network(monkeypatch):
    monkeypatch.setattr(gemini.request,'urlopen',lambda *a,**kw: (_ for _ in ()).throw(AssertionError('network')))
    client=GeminiClient(key='fake')
    with gemini_request_budget(0):
        try:
            client.embed(['vpn'])
        except GeminiUnavailable:
            pass
        else:
            raise AssertionError('expected budget exhausted')
