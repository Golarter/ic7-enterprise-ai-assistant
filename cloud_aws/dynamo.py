"""DynamoDB de tamaño acotado para DEMO. No es un vector DB escalable.

Items pequeños con vectores cuantizados (int8) para limitar consumo de WCU.
Tablas Standard con capacidad PROVISIONED, nunca On-demand por defecto.
"""
import base64
import json
import math
import os
import struct
from datetime import datetime, timezone


def _qencode(vector):
    norm = math.sqrt(sum(x*x for x in vector)) or 1
    values = [int(max(-127, min(127, round(x/norm*127)))) for x in vector]
    return base64.b64encode(struct.pack(f'{len(values)}b', *values)).decode('ascii')


def _qdecode(value):
    data = base64.b64decode(value)
    return struct.unpack(f'{len(data)}b', data)


class DynamoVectorStore:
    def __init__(self, table, max_docs=50):
        self.table = table
        self.max_docs = max_docs

    def add(self, doc_id, name, parts, embeddings, *, owner=None):
        if len(parts) != len(embeddings):
            raise ValueError('Embeddings inconsistentes')
        if len(parts) > 12:
            raise ValueError('Máximo 12 fragmentos por documento para mantener costos controlados')
        # 1 WCU aproximada por ítem pequeño; evitar documentos extensos en la demo.
        for i, (part, vec) in enumerate(zip(parts, embeddings), 1):
            self.table.put_item(Item={
                'pk':f'USER#{owner}#DOC' if owner else 'DOC', 'sk':f'{doc_id}#{i:04}', 'document':name,
                'chunk':i, 'excerpt':part[:900], 'v':_qencode(vec),
                'embedding_model':os.getenv('GEMINI_EMBED_MODEL','gemini-embedding-001')},
                ConditionExpression='attribute_not_exists(pk) AND attribute_not_exists(sk)')

    def search(self, vector, count=4, min_similarity=0.22, *, owner=None):
        from boto3.dynamodb.conditions import Key
        # Biblioteca existente compartida + documentos privados del usuario actual.
        partitions = ['DOC'] + ([f'USER#{owner}#DOC'] if owner else [])
        items = []
        for pk in partitions:
            items.extend(self.table.query(KeyConditionExpression=Key('pk').eq(pk), Limit=self.max_docs).get('Items', []))
        q = _qdecode(_qencode(vector))
        qn = math.sqrt(sum(x*x for x in q)) or 1
        matches = []
        for item in items:
            if item.get('embedding_model') != os.getenv('GEMINI_EMBED_MODEL','gemini-embedding-001'):
                continue
            v = _qdecode(item['v'])
            if len(v) != len(q):
                continue
            vn = math.sqrt(sum(x*x for x in v)) or 1
            similarity = sum(a*b for a,b in zip(q,v)) / (qn*vn)
            if similarity >= min_similarity:
                matches.append({'document':item['document'], 'chunk':int(item['chunk']),
                                'excerpt':item['excerpt'], 'similarity':round(similarity,4)})
        return sorted(matches,key=lambda x:x['similarity'],reverse=True)[:count]

    def count(self, *, owner=None):
        from boto3.dynamodb.conditions import Key
        partitions = ['DOC'] + ([f'USER#{owner}#DOC'] if owner else [])
        return sum(self.table.query(KeyConditionExpression=Key('pk').eq(pk),
                      Select='COUNT', Limit=self.max_docs).get('Count', 0)
                   for pk in partitions)


class DynamoAuditStore:
    def __init__(self, table):
        self.table = table

    def save(self, *, trace_id, session_id, question, answer, tools_used, sources, owner=None):
        timestamp = datetime.now(timezone.utc).isoformat()
        self.table.put_item(Item={
            'pk':f'USER#{owner}#SESSION#{session_id}' if owner else f'SESSION#{session_id}', 'sk':f'{timestamp}#{trace_id}',
            'trace_id':trace_id, 'session_id':session_id,
            'question':question, 'answer':answer,
            'tools_used':json.dumps(tools_used,ensure_ascii=False),
            'sources':json.dumps(sources,ensure_ascii=False), 'timestamp':timestamp})

    def history(self, session_id, limit=50, *, owner=None):
        from boto3.dynamodb.conditions import Key
        data = self.table.query(KeyConditionExpression=Key('pk').eq(f'USER#{owner}#SESSION#{session_id}' if owner else f'SESSION#{session_id}'),
                                ScanIndexForward=False, Limit=min(limit,50))
        return [dict(trace_id=x['trace_id'], session_id=x['session_id'],question=x['question'],
                     answer=x['answer'],tools_used=json.loads(x['tools_used']),
                     sources=json.loads(x['sources']),timestamp=x['timestamp']) for x in data.get('Items',[])]

    def count(self):
        # DynamoDB item_count es aproximado; nunca se muestra como cifra exacta de auditoría.
        return self.table.item_count
