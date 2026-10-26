"""Adaptador Gemini REST para el protocolo de herramientas del agente.

No depende de google-genai para limitar el tamaño del ZIP Lambda.
Retiene íntegramente partes/signatures al reconstruir function calling.
"""
import json
import os
from urllib import request, error

class GeminiUnavailable(RuntimeError):
    pass


class GeminiClient:
    def __init__(self, key=None, chat_model=None, embed_model=None, dimensions=128):
        self.key = key if key is not None else os.getenv('GEMINI_API_KEY', '')
        self.chat_model = chat_model or os.getenv('GEMINI_CHAT_MODEL', 'gemini-2.5-flash')
        self.embed_model = embed_model or os.getenv('GEMINI_EMBED_MODEL', 'gemini-embedding-001')
        self.dimensions = int(dimensions)
        if not self.key:
            raise GeminiUnavailable('Falta GEMINI_API_KEY (no se recibe ninguna clave desde el navegador)')

    def _post(self, model, verb, payload):
        url = 'https://generativelanguage.googleapis.com/v1beta/models/' + model + ':' + verb
        req = request.Request(url, method='POST', data=json.dumps(payload).encode(),
                              headers={'Content-Type':'application/json', 'x-goog-api-key':self.key})
        try:
            with request.urlopen(req, timeout=25) as response:
                return json.loads(response.read())
        except (error.URLError, TimeoutError, ValueError) as exc:
            raise GeminiUnavailable('El proveedor Gemini no respondió correctamente') from exc

    def embed(self, values):
        # Usar embeddings del mismo modelo y dimensión para consultas y documentos.
        out = []
        for value in values:
            data = self._post(self.embed_model, 'embedContent', {
                'model': 'models/' + self.embed_model,
                'content': {'parts': [{'text': value}]},
                'outputDimensionality': self.dimensions,
            })
            vector = data.get('embedding', {}).get('values')
            if not vector or len(vector) != self.dimensions:
                raise GeminiUnavailable('Gemini devolvió un embedding incompleto')
            out.append(vector)
        return out

    def chat(self, messages, tools=None):
        from app.agent import TOOL_DEFINITIONS
        contents, system = [], []
        for m in messages:
            role = m.get('role')
            if role == 'system':
                system.append(m['content'])
            elif role == 'user':
                contents.append({'role':'user', 'parts':[{'text': m['content']}]})
            elif role == 'assistant':
                parts = m.get('provider_parts') or [{'text': m.get('content') or ''}]
                contents.append({'role':'model','parts':parts})
            elif role == 'tool':
                try:
                    result = json.loads(m['content'])
                except ValueError:
                    result = {'text':m['content']}
                response = {'name':m['tool_name'], 'response':result}
                if m.get('tool_call_id'):
                    response['id'] = m['tool_call_id']
                contents.append({'role':'user','parts':[{'functionResponse':response}]})
        payload = {'contents':contents, 'systemInstruction':{'parts':[{'text':'\n'.join(system)}]},
                   'generationConfig':{'temperature':0, 'maxOutputTokens':700}}
        if tools:
            payload['tools'] = [{'functionDeclarations':[
                dict(name=t['function']['name'], description=t['function']['description'],
                     parameters=t['function']['parameters']) for t in tools]}]
        data = self._post(self.chat_model,'generateContent',payload)
        candidates = data.get('candidates') or []
        if not candidates:
            return {'content':''}
        parts = candidates[0].get('content',{}).get('parts') or []
        calls = []
        for part in parts:
            fc = part.get('functionCall')
            if fc:
                calls.append({'id':fc.get('id'), 'function':{'name':fc.get('name'), 'arguments':fc.get('args',{})}})
        return {'content':'\n'.join(p['text'] for p in parts if 'text' in p),
                'tool_calls':calls, 'provider_parts':parts}

    def healthy(self):
        return bool(self.key)
