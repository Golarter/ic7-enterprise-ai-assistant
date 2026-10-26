# Guion de demostración (6:30–7:00 minutos)

**00:00–00:40 — problema:** app legada y búsqueda manual; mostrar objetivo del asistente.

**00:40–01:20 — arquitectura:** diagrama, FastAPI, ChromaDB, Ollama, SQLite y separación en módulos. Aclarar que AWS es una ruta de despliegue documentada, no desplegada.

**01:20–02:10 — ingesta:** abrir Swagger, `POST /api/documents`, cargar `data/manual_demo.md`; enseñar documento/chunks y `/api/stats`.

**02:10–03:00 — RAG:** preguntar «¿Cómo se solicita acceso VPN?», mostrar contenido, herramienta `buscar_documentacion`, fuente `[F1]` y fragmento.

**03:00–04:00 — agente:** consultar estado `SOL-1001` y clasificación «fuga de datos». En ambos ejemplos mostrar `tools_used` y la respuesta exacta.

**04:00–04:45 — trazabilidad y seguridad:** consultar historial `demo_001`, `trace_id`, demostrar 401 sin API key y validación de extensiones.

**04:45–05:45 — evaluaciones:** ejecutar `pytest -q` y `python scripts/evaluate.py`. Explicar resultados reales sin ocultar casos fallidos; incluir pregunta desconocida e inyección.

**05:45–06:30 — producción:** explicar riesgos, secretos, autorización por documentos, limitaciones del modelo y despliegue potencial en AWS.

**06:30–07:00 — cierre:** decisiones técnicas, trade-offs, mejoras y uso de IA en el desarrollo.

No grabar claves, documentos reales ni datos personales.
