# Guion de demostración IC7 — duración objetivo: 6:30 (máximo 7:00)

**Preparación:** cuenta Cognito ya autorizada, documentos de demo cargados, consola sin claves, GitHub PR #5, pestaña AWS CloudWatch con registros filtrados. Ensayar la secuencia y no mostrar datos personales ni tokens. Grabar pantalla con resolución legible.

| Tiempo | Pantalla | Mensaje / evidencia |
|---|---|---|
| 00:00–00:35 | Inicio en Amplify | Problema: información dispersa y consultas repetitivas; asistente empresarial RAG con herramientas |
| 00:35–01:20 | `docs/arquitectura.md` | React/Amplify → Cognito → API Gateway → Lambda/FastAPI → DynamoDB y Gemini; ruta local Ollama separada |
| 01:20–02:10 | Documentos | Mostrar listado de documentos de demostración, carga y borrado privado (sin datos sensibles) |
| 02:10–03:20 | Pregunta SOP-002 MFA | Respuesta con `[F1]`, `[F3]`, documentos fuente y abstención si falta contexto |
| 03:20–04:10 | Herramientas | Clasificar caída de autenticación (Crítica); consultar `SOL-1001` (En progreso). Explicar rutas directas sin Gemini |
| 04:10–04:55 | Nueva conversación / historial | Cognito, privacidad, historial por sesión, trazas; mencionar ensayos de aislamiento con dos usuarios sin mostrar datos |
| 04:55–05:45 | CMD y CloudWatch | `pytest -q`: 55/55; logs RAG: embed 342 ms, recuperación 383 ms, generación 1495 ms, Lambda 2007 ms |
| 05:45–06:15 | GitHub PR #5 | Tres commits fusionados en `main`, workflow empaquetado y pruebas |
| 06:15–06:40 | Riesgos | Timeouts Gemini intermitentes (503), vector search acotado, falta de métricas de carga y producción |
| 06:40–06:55 | Cierre | Decisiones técnicas, aprendizaje y revisión humana del trabajo asistido por IA |

**No afirmar:** latencia promedio, ausencia absoluta de alucinaciones, seguridad certificada ni disponibilidad garantizada. La medición de 2.007 ms corresponde a una solicitud concreta.
