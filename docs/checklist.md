# Matriz de cumplimiento — prueba I Cloud Seven

Leyenda: **implementado** = código presente, no equivale a validación real; **pendiente** = necesita ejecución/verificación externa.

| Requisito del documento | Entrega | Estado |
|---|---|---|
| 5.1 API Python y manejo errores | `app/main.py`, `/docs` | Implementado; integración real pendiente |
| 5.1 Consulta al asistente | `POST /api/ask` | Implementado |
| 5.1 Ingesta de documentos | `POST /api/documents` | Implementado |
| 5.1 Historial/logs | `GET /api/history/{session_id}`, `audit.sqlite3` | Implementado |
| 5.2 Chunking | `app/document.py` | Implementado y testeado |
| 5.2 Embeddings | `app/llm.py`, Ollama EmbeddingGemma | Implementado; Ollama real pendiente |
| 5.2 Vector store | Chroma persistente | Implementado; integración real pendiente |
| 5.2 Recuperación | `buscar_documentacion` | Implementado |
| 5.2 Respuesta y fuentes | `[F1]` + excerpts | Implementado; groundedness real pendiente |
| 5.3 Dos herramientas | Tres herramientas de solo lectura | Implementado y testeado con mocks |
| 5.4 AI assisted development | README de transparencia y riesgos | Preparado; completar bitácora personal |
| 5.5 Variables de entorno y secretos | `.env.example`, `X-API-Key`, `.gitignore` | Implementado |
| 5.5 Logging, validación y errores | Middleware de trazas, Pydantic, HTTP | Implementado |
| 5.5 Riesgos y readiness | `docs/arquitectura.md` | Documentado |
| 5.6 5 preguntas + expected, observed | 8 casos en `scripts/evaluate.py` | Preparado; ejecutar contra IA real |
| 5.6 Groundedness y accuracy | Heurística y casos de abstención/inyección | Preparado; validar manualmente |
| 6 Repositorio | Código local para iniciar Git | Preparado; publicar por candidato |
| 6 README | `README.md` | Implementado |
| 6 Diagrama | Mermaid en `docs/arquitectura.md` | Implementado |
| 6 Decisiones técnicas | `docs/arquitectura.md` | Implementado |
| 6 Evidencia ejecutada | `pytest`, reporte real | Pendiente ejecutar y adjuntar |
| 6 Video hasta 7 min | Guion en `docs/demo_video.md` | Pendiente grabar |
| 6 Mejoras futuras | README y arquitectura | Documentado |
| 6 Riesgos producción | Arquitectura | Documentado |
| Nube | AWS diseño documentado | Despliegue opcional no realizado |

No marcar como funcional o evaluado un servicio que no se ejecutó.
