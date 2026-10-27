"""Pruebas del listado de documentos, sin AWS real ni credenciales."""
from fastapi.testclient import TestClient
from cloud_aws.api import create_cloud_app
from cloud_aws.dynamo import DynamoAuditStore, DynamoVectorStore
from cloud_aws.tests.test_multiuser_isolation import A, B, Gateway, Model


class PaginatedTable:
    def __init__(self, page_size=2):
        self.items = []
        self.page_size = page_size

    def put_item(self, Item, **kwargs):
        if any(x['pk'] == Item['pk'] and x['sk'] == Item['sk'] for x in self.items):
            raise ValueError('duplicate')
        self.items.append(Item)

    def query(self, KeyConditionExpression, **kwargs):
        pk = KeyConditionExpression.get_expression()['values'][1]
        rows = sorted((x for x in self.items if x['pk'] == pk), key=lambda x: x['sk'])
        start_key = kwargs.get('ExclusiveStartKey')
        if start_key:
            rows = [x for x in rows if x['sk'] > start_key['sk']]
        n = min(self.page_size, kwargs.get('Limit', self.page_size))
        batch = rows[:n]
        out = {'Items': batch, 'Count': len(batch)}
        if len(rows) > n:
            out['LastEvaluatedKey'] = {'pk': pk, 'sk': batch[-1]['sk']}
        return out

    @property
    def item_count(self):
        return len(self.items)


def make_app(table):
    return create_cloud_app(llm=Model(), vector=DynamoVectorStore(table),
                            audit=DynamoAuditStore(PaginatedTable()))


def test_document_list_is_private_and_has_no_embedded_text():
    table = PaginatedTable(page_size=1)
    store = DynamoVectorStore(table)
    store.add('a-doc', 'alfa.txt', ['secreto-a-1', 'secreto-a-2'], [[.7,.3]] * 2, owner=A)
    store.add('b-doc', 'beta.txt', ['secreto-b'], [[.7,.3]], owner=B)
    store.add('common', 'comun.txt', ['publico'], [[.7,.3]])
    app = make_app(table)
    with TestClient(Gateway(app,A)) as a, TestClient(Gateway(app,B)) as b:
        ra = a.get('/api/documents')
        rb = b.get('/api/documents')
        assert ra.status_code == rb.status_code == 200
        assert ra.json() == {'documents': [{'document_id':'a-doc', 'name':'alfa.txt', 'chunks':2}], 'truncated':False}
        assert rb.json() == {'documents': [{'document_id':'b-doc', 'name':'beta.txt', 'chunks':1}], 'truncated':False}
        for response in (ra, rb):
            assert 'excerpt' not in response.text
            assert 'secreto-' not in response.text
            assert 'embedding_model' not in response.text
            assert 'comun.txt' not in response.text


def test_document_list_empty_for_other_user_and_anonymous_rejected():
    table = PaginatedTable()
    DynamoVectorStore(table).add('a', 'a.txt', ['contenido'], [[.7,.3]], owner=A)
    app = make_app(table)
    with TestClient(Gateway(app,B)) as b:
        assert b.get('/api/documents').json() == {'documents':[], 'truncated':False}
    with TestClient(app) as anonymous:
        assert anonymous.get('/api/documents').status_code == 401
        assert anonymous.get('/api/documents', headers={'x-api-key':'test-key-long-enough-for-cloud'}).status_code == 401


def test_pagination_does_not_present_incomplete_document_as_complete():
    table = PaginatedTable(page_size=2)
    store = DynamoVectorStore(table)
    store.add('aaa', 'primero.txt', ['uno', 'dos'], [[.7,.3]]*2, owner=A)
    store.add('bbb', 'segundo.txt', ['tres', 'cuatro', 'cinco'], [[.7,.3]]*3, owner=A)
    result = store.list_private(owner=A, max_items=3)
    assert result['truncated'] is True
    assert result['documents'] == [{'document_id':'aaa', 'name':'primero.txt', 'chunks':2}]
    all_result = store.list_private(owner=A, max_items=10)
    assert all_result['truncated'] is False
    assert [x['chunks'] for x in all_result['documents']] == [2, 3]


def test_owner_required_for_private_listing():
    store = DynamoVectorStore(PaginatedTable())
    try:
        store.list_private(owner=None)
    except ValueError:
        pass
    else:
        raise AssertionError('El listado privado no puede aceptar owner=None')
