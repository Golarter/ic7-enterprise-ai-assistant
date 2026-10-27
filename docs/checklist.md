# Matriz de cumplimiento — IC7 (corte 27-10-2026)

**Criterio:** «demostrado» significa prueba concreta reportada; no significa garantía de producción.

| Requisito | Evidencia | Estado |
|---|---|---|
| Backend Python y API | FastAPI, variante local y AWS Lambda/Mangum | Implementado y probado en AWS |
| Consulta `/api/ask` | HTTP 200 en RAG MFA, prioridad, solicitudes | Demostrado |
| Ingesta/chunking | Carga de documentos y tests; 10 documentos de prueba cargados en demo | Probado funcionalmente |
| Embeddings y búsqueda vectorial | `gemini-embedding-001`, vectores en DynamoDB; 4 evidencias MFA | Demostrado |
| Respuesta con fuentes | MFA con `[F1]`, `[F3]`; abstención sin evidencia | Demostrado en ejemplos |
| 2+ herramientas de agente | Tres: documentación, solicitud, clasificación | Demostrado |
| Autenticación | Cognito JWT en HTTP API; 401 no autenticado en verificaciones previas | Demostrado en pruebas reportadas |
| Privacidad entre usuarios | Aislamiento documental e historial probado con dos cuentas | Evidencia funcional previa; no pentest |
| Errores y logging | CloudWatch trazas, 503 ante timeout, métricas por operación | Demostrado |
| Evaluación 5+ preguntas | Casos de negocio, desconocido y prompt injection; ver `docs/evaluacion_rag.md` | Evidencia parcial; faltan métricas agregadas |
| Pruebas automatizadas | `pytest -q`: 55 passed in 1.82 s tras PR #5 | Demostrado |
| Repositorio y PR | `Golarter/ic7-enterprise-ai-assistant`, PR #5, `main` `5f3b79b` | Demostrado |
| Arquitectura y decisiones | `docs/arquitectura.md` | Actualizado |
| Uso responsable de IA | README + decisiones; revisar y documentar validaciones humanas | Documentado parcialmente |
| Video máximo 7 minutos | `docs/demo_video.md` | Guion preparado; grabación pendiente |
| Preparación producción | `docs/security_validation.md` y riesgos | Pendientes controles operacionales |
