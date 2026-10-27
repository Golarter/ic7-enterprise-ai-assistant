# Decisiones técnicas y trade-offs — IC7

| Decisión | Motivo | Contrapartida |
|---|---|---|
| FastAPI en Lambda (Mangum) | Reutilizar lógica Python, despliegue serverless de demo | Cold starts y límite de integración |
| React en Amplify | UI navegable con documentos e historial | Dependencia de servicios AWS |
| Cognito JWT | Identidad verificada por usuario | Gestión de cuentas y configuración JWT |
| DynamoDB para fragmentos/historial | Persistencia sin servidor SQL propio | Búsqueda vectorial acotada poco escalable |
| Gemini externo para RAG | Inferencia y embeddings sin servir modelos en Lambda | Latencia, disponibilidad y confidencialidad del proveedor |
| Rutas directas para dos herramientas | Disponibilidad y baja latencia sin generación | Enrutamiento por patrones: ambiguos van al agente |
| Citas obligatorias y abstención | Reducir respuestas sin soporte | Evaluación semántica humana aún necesaria |
| 26 s presupuesto del agente y HTTP 30 s | Controlar duración de solicitudes | No elimina fallos del proveedor |
| Ollama/Chroma en alternativa local | Funciona sin nube y permite evaluación | Diferencias funcionales de identidad, persistencia y entorno |

## IA asistida y verificación humana

Se utilizó ChatGPT para análisis de incidencias, diseño y propuestas de parches. Se aplicaron comprobaciones con `pytest` (55 pruebas), revisión de diffs, GitHub PR #5, respaldos ZIP antes de actualizar Lambda y observaciones en CloudWatch. Esta evidencia no acredita revisión independiente de seguridad; el candidato debe revisar y declarar personalmente sus contribuciones, limitaciones y herramientas antes de entregar.
