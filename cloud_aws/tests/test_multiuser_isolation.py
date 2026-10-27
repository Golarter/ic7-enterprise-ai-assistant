"""Offline isolation tests. Simulated API Gateway event is NOT an AWS IAM security test."""
import json
import os
import uuid
from fastapi.testclient import TestClient
from cloud_aws.api import create_cloud_app
from cloud_aws.dynamo import DynamoAuditStore, DynamoVectorStore
from cloud_aws.tenant import ScopedVector

A = '11111111-1111-4111-8111-111111111111'
B = '22222222-2222-4222-8222-222222222222'

class Table:
    def __init__(self): self.items = []
    def put_item(self, Item, **_):
        if any(x['pk'] == Item['pk'] and x['sk'] == Item['sk'] for x in self.items):
            raise ValueError('duplicate')
        self.items.append(Item)
    def query(self, KeyConditionExpression, **kw):
        pk = KeyConditionExpression.get_expression()['values'][1]
        data = [x for x in self.items if x['pk'] == pk]
        data.sort(key=lambda x:x['sk'], reverse=not kw.get('ScanIndexForward', True))
        data = data[:kw.get('Limit', 100)]
        return {'Items': data, 'Count': len(data)}
    @property
    def item_count(self): return len(self.items)

class Model:
    chat_model='stub'
    embed_model='stub'
    def healthy(self): return True
    def embed(self, values): return [[0.7, 0.3] for _ in values]
    def chat(self, messages, tools=None):
        return {'content': 'No encontré información suficiente en los documentos cargados.'}

class Gateway:
    def __init__(self, app, subject): self.app=app; self.subject=subject
    async def __call__(self, scope, receive, send):
        scope = dict(scope)
        scope['aws.event'] = {'requestContext': {'apiId': 'xwejxdr534', 'authorizer': {
            'jwt': {'claims': {'iss':'https://cognito-idp.us-east-1.amazonaws.com/us-east-1_IDR1J7OIo',
            'client_id':'78ipamj1tmh1g10ffsld9471nj', 'token_use':'access',
            'scope':'openid email profile', 'sub':self.subject}}}}}
        await self.app(scope, receive, send)

def test_audit_partition_prevents_cross_user_access():
    table = Table(); audit = DynamoAuditStore(table)
    args = dict(trace_id='t1', session_id='same-id', question='q', answer='a', tools_used=[], sources=[])
    audit.save(**args, owner=A)
    assert len(audit.history('same-id', owner=A)) == 1
    assert audit.history('same-id', owner=B) == []
    assert audit.history('same-id') == []
    assert table.items[0]['pk'] == f'USER#{A}#SESSION#same-id'

def test_vectors_private_and_shared():
    table=Table(); store=DynamoVectorStore(table)
    store.add('shared','comun.txt',['compartido'],[[.7,.3]])
    store.add('private','privado.txt',['privado'],[[.7,.3]], owner=A)
    a=store.search([.7,.3], owner=A)
    b=store.search([.7,.3], owner=B)
    assert {x['document'] for x in a} == {'comun.txt','privado.txt'}
    assert {x['document'] for x in b} == {'comun.txt'}
    assert {x['document'] for x in store.search([.7,.3])} == {'comun.txt'}

def test_jwt_authenticated_histories_are_isolated(monkeypatch):
    monkeypatch.setenv('APP_API_KEY','test-key-long-enough-for-cloud')
    vector=DynamoVectorStore(Table()); audit=DynamoAuditStore(Table())
    app=create_cloud_app(llm=Model(),vector=vector,audit=audit)
    with TestClient(Gateway(app,A)) as a, TestClient(Gateway(app,B)) as b:
        r=a.post('/api/ask',json={'question':'Estado de VPN','session_id':'shared-session'})
        assert r.status_code == 200, r.text
        assert a.get('/api/history/shared-session').status_code == 200
        assert len(a.get('/api/history/shared-session').json()) == 1
        assert b.get('/api/history/shared-session').json() == []
    with TestClient(app) as direct:
        assert direct.get('/api/history/shared-session',headers={'x-user-id':A}).status_code == 401
        legacy=direct.get('/api/history/shared-session',headers={'x-api-key':'test-key-long-enough-for-cloud'})
        assert legacy.status_code == 401
