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

    def list_private(self, *, owner, max_items=250):
        """Enumera solo la particion privada; nunca expone textos ni embeddings."""
        if not owner:
            raise ValueError('Se requiere propietario autenticado')
        from boto3.dynamodb.conditions import Key
        partition = f'USER#{owner}#DOC'
        items = []
        cursor = None
        while len(items) < max_items:
            kwargs = dict(
                KeyConditionExpression=Key('pk').eq(partition),
                ProjectionExpression='sk, #document, chunk',
                ExpressionAttributeNames={'#document': 'document'},
                Limit=min(50, max_items - len(items)),
            )
            if cursor:
                kwargs['ExclusiveStartKey'] = cursor
            result = self.table.query(**kwargs)
            items.extend(result.get('Items', []))
            cursor = result.get('LastEvaluatedKey')
            if not cursor:
                break
        # Si se agota el limite entre fragmentos de un documento,
        # no presentarlo como si estuviera indexado por completo.
        incomplete_id = None
        if cursor and items:
            last_sk = str(items[-1].get('sk', ''))
            if '#' in last_sk:
                incomplete_id = last_sk.rsplit('#', 1)[0]
        grouped = {}
        for item in items:
            sk = str(item.get('sk', ''))
            if '#' not in sk:
                continue
            doc_id = sk.rsplit('#', 1)[0]
            if doc_id == incomplete_id:
                continue
            row = grouped.setdefault(doc_id, {
                'document_id': doc_id,
                'name': str(item.get('document', '')),
                'chunks': 0,
            })
            row['chunks'] += 1
        return {'documents': sorted(grouped.values(), key=lambda x: x['name'].casefold()),
                'truncated': bool(cursor)}

    def delete_private(self, doc_id, *, owner):
        """Delete only the given document from the verified owner's partition.

        Uses an exact sort-key prefix, never a table scan or a client-supplied pk.
        The demo ingestion limit is 12 chunks; unexpected larger matches fail
        before any deletion to avoid leaving partially deleted documents.
        """
        import re
        from boto3.dynamodb.conditions import Key
        if not owner:
            raise ValueError('Se requiere propietario autenticado')
        if not re.fullmatch(r'[0-9a-fA-F]{16,64}', doc_id):
            raise ValueError('ID de documento inválido')
        partition = f'USER#{owner}#DOC'
        result = self.table.query(
            KeyConditionExpression=Key('pk').eq(partition) & Key('sk').begins_with(doc_id.lower() + '#'),
            ProjectionExpression='pk, sk',
            Limit=13,
        )
        rows = result.get('Items', [])
        if len(rows) > 12 or result.get('LastEvaluatedKey'):
            raise ValueError('Documento excede los límites seguros de eliminación')
        for row in rows:
            # Preserve the exact queried keys; do not accept keys from client input.
            self.table.delete_item(Key={'pk': partition, 'sk': row['sk']})
        return len(rows)

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
        if owner:
            # Eventos cronológicos para descubrir sesiones sin Scan ni GSI.
            # El índice no contiene respuestas ni fuentes privadas.
            self.table.put_item(Item={
                'pk': f'USER#{owner}#SESSIONS',
                'sk': f'{timestamp}#{trace_id}',
                'session_id': session_id,
                'last_question': question[:140],
                'updated_at': timestamp,
            })

    def history(self, session_id, limit=50, *, owner=None):
        from boto3.dynamodb.conditions import Key
        data = self.table.query(KeyConditionExpression=Key('pk').eq(f'USER#{owner}#SESSION#{session_id}' if owner else f'SESSION#{session_id}'),
                                ScanIndexForward=False, Limit=min(limit,50))
        return [dict(trace_id=x['trace_id'], session_id=x['session_id'],question=x['question'],
                     answer=x['answer'],tools_used=json.loads(x['tools_used']),
                     sources=json.loads(x['sources']),timestamp=x['timestamp']) for x in data.get('Items',[])]

    def list_sessions(self, *, owner, limit=30, max_events=200):
        """Devuelve sesiones recientes únicas, acotadas a max_events eventos.

        Para la demo, un evento por consulta permite ordenar por actividad
        con Query de DynamoDB, sin Scan, GSI ni UpdateItem.
        """
        if not owner:
            raise ValueError('Se requiere propietario autenticado')
        from boto3.dynamodb.conditions import Key
        limit = max(1, min(int(limit), 50))
        max_events = max(limit, min(int(max_events), 500))
        result_items = []
        cursor = None
        while len(result_items) < max_events:
            kwargs = {
                'KeyConditionExpression': Key('pk').eq(f'USER#{owner}#SESSIONS'),
                'ScanIndexForward': False,
                'Limit': min(50, max_events-len(result_items)),
                'ProjectionExpression': 'session_id, last_question, updated_at',
            }
            if cursor:
                kwargs['ExclusiveStartKey'] = cursor
            result = self.table.query(**kwargs)
            result_items.extend(result.get('Items', []))
            cursor = result.get('LastEvaluatedKey')
            if not cursor:
                break
        seen = set()
        sessions = []
        for item in result_items:
            sid = item.get('session_id')
            if not isinstance(sid, str) or sid in seen:
                continue
            seen.add(sid)
            sessions.append({
                'session_id': sid,
                'title': str(item.get('last_question') or 'Conversación')[:140],
                'updated_at': str(item.get('updated_at') or ''),
            })
            if len(sessions) >= limit:
                break
        return {'conversations': sessions,
                'truncated': bool(cursor) or len(seen) > limit or len(result_items) >= max_events}

    def count(self):
        # DynamoDB item_count es aproximado; nunca se muestra como cifra exacta de auditoría.
        return self.table.item_count
