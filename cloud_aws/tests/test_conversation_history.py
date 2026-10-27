"""Pruebas locales del índice cronológico. No prueban los permisos IAM."""
from fastapi.testclient import TestClient
from cloud_aws.api import create_cloud_app
from cloud_aws.dynamo import DynamoAuditStore, DynamoVectorStore
from cloud_aws.tests.test_multiuser_isolation import A, B, Table, Gateway, Model


def test_new_sessions_listed_only_to_owner():
    table = Table()
    audit = DynamoAuditStore(table)
    vector = DynamoVectorStore(Table())
    app = create_cloud_app(llm=Model(), vector=vector, audit=audit)
    with TestClient(Gateway(app, A)) as alice, TestClient(Gateway(app, B)) as bob:
        for session in ('s1', 's1', 's2'):
            resp = alice.post('/api/ask', json={'question':'Consulta de ejemplo', 'session_id': session})
            assert resp.status_code == 200, resp.text
        r = alice.get('/api/conversations')
        assert r.status_code == 200, r.text
        assert {s['session_id'] for s in r.json()['conversations']} == {'s1', 's2'}
        assert bob.get('/api/conversations').json()['conversations'] == []
        assert len(alice.get('/api/history/s1').json()) == 2
        assert bob.get('/api/history/s1').json() == []
    assert all('answer' not in item for item in table.items if item['pk'].endswith('#SESSIONS'))


def test_legacy_histories_are_preserved_not_discovered():
    table = Table()
    audit = DynamoAuditStore(table)
    audit.save(trace_id='old',session_id='old-session',question='q',answer='a',tools_used=[],sources=[])
    assert len(audit.history('old-session')) == 1
    assert audit.list_sessions(owner=A)['conversations'] == []


def test_anonymous_and_api_key_are_rejected(monkeypatch):
    monkeypatch.setenv('APP_API_KEY', 'test-key-long-enough-for-cloud')
    app = create_cloud_app(llm=Model(), vector=DynamoVectorStore(Table()), audit=DynamoAuditStore(Table()))
    with TestClient(app) as client:
        assert client.get('/api/conversations').status_code == 401
        assert client.get('/api/conversations',headers={'X-API-Key':'test-key-long-enough-for-cloud'}).status_code == 401
