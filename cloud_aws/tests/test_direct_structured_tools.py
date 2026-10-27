"""Las herramientas deterministas pueden funcionar sin Gemini."""
from app.agent import Agent


class NoGemini:
    def chat(self, *args, **kwargs):
        raise AssertionError('No debe utilizarse Gemini')

    def embed(self, *args, **kwargs):
        raise AssertionError('No debe generar embeddings')


class Requests:
    def get(self, code):
        if code == 'SOL-1001':
            return {'estado': 'En progreso', 'prioridad': 'Alta'}
        return None


def agent():
    return Agent(NoGemini(), None, Requests())


def test_critica_directa_sin_llm():
    text, tools, sources = agent().answer('Clasifica la prioridad: el sistema de autenticación de toda la empresa está caído y ningún empleado puede ingresar.')
    assert '**Crítica**' in text
    assert tools == ['clasificar_prioridad'] and sources == []


def test_prioridad_baja_directa_sin_llm():
    text, tools, sources = agent().answer('Clasifica la prioridad: solicitud informativa')
    assert '**Baja**' in text
    assert tools == ['clasificar_prioridad'] and sources == []


def test_solicitud_directa_sin_llm():
    text, tools, sources = agent().answer('Consulta el estado de la solicitud SOL-1001.')
    assert 'En progreso' in text and 'SOL-1001' in text
    assert tools == ['consultar_solicitud'] and sources == []


def test_solicitud_inexistente_directa_sin_llm():
    text, tools, sources = agent().answer('Consulta el estado de la solicitud SOL-9999.')
    assert 'no encontrada' in text.lower()
    assert tools == ['consultar_solicitud'] and sources == []


def test_no_routing_mixto():
    assert agent()._structured_direct_intent('Clasifica la prioridad: caída general y consulta la solicitud SOL-1001') is None
    assert agent()._structured_direct_intent('Consulta el estado de SOL-1001 y explica la política VPN') is None


def test_no_routing_orden_indirecta():
    assert agent()._structured_direct_intent('¿Puedes analizar por qué no funciona la VPN?') is None
