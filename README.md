# Enterprise AI Assistant — I Cloud Seven | AI Developer Engineer Semi-Senior

MVP **agente RAG empresarial** que consulta documentos internos, usa herramientas sobre solicitudes simuladas y conserva evidencias y trazas. **No contiene código ni documentos de la empresa reclutadora; es un ejercicio demostrativo propio.**

## Funcionalidades entregadas

- Backend FastAPI, Swagger UI, autenticación por clave, validación Pydantic y errores HTTP.
- `POST /api/documents`: ingesta TXT/MD/PDF textuales, chunking, embeddings multilingües y persistencia en Chroma.
- `POST /api/ask`: agente LLM con tres herramientas de solo lectura: `buscar_documentacion`, `consultar_solicitud`, `clasificar_prioridad`.
- Respuestas con fuentes `[F1]` y metadatos de fragmentos, sesiones, ID de traza por solicitud.
- `GET /api/history/{session_id}`, `/api/stats`, `/health`, `/ready`.
- Evaluación offline automatizada y evaluación de 8 casos de negocio con ejecución de modelo, incluyendo falta de respuesta y prompt injection.
- Docker Compose, diagrama y decisión de arquitectura, consideraciones de producción, guion para video.

## Requisitos

- Python 3.11 o 3.12, Docker opcional.
- [Ollama](https://ollama.com/download) instalado localmente. Modelo de chat `qwen3:4b-instruct` (~2.5 GB), embeddings `embeddinggemma` (~0.6 GB); se descargan una vez. CPU puede ser lento.
- Ningún crédito de Azure/AWS ni API de IA de pago para ejecución local.

## Ruta A: ejecución local

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
cp .env.example .env  # en Windows: copy .env.example .env
# Edita .env: asigna una clave única aleatoria de 32+ caracteres a APP_API_KEY.
ollama pull qwen3:4b-instruct
ollama pull embeddinggemma
ollama serve  # omitir si Ollama ya funciona como servicio
python run.py
```

Servidor en http://127.0.0.1:8000. Documentación: http://127.0.0.1:8000/docs. La API key se envía en el encabezado `X-API-Key` para todos los endpoints salvo `/health`.

**Ejemplos de Windows PowerShell** (tras crear `.env` y arrancar):

```powershell
$key = (Get-Content .env | Where-Object { $_ -like 'APP_API_KEY=*' }).Split('=',2)[1]
curl.exe -X POST "http://127.0.0.1:8000/api/documents" -H "X-API-Key: $key" -F "file=@data/manual_demo.md"
$body = @{ question = '¿Cómo solicito acceso VPN?'; session_id = 'demo_001' } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8000/api/ask' -Headers @{ 'X-API-Key' = $key } -ContentType 'application/json' -Body $body
Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/history/demo_001' -Headers @{ 'X-API-Key' = $key }
```

**Ejemplos de Linux/macOS**:

```bash
set -a; source .env; set +a
curl -s -X POST http://127.0.0.1:8000/api/documents -H "X-API-Key: $APP_API_KEY" -F file=@data/manual_demo.md
curl -s -X POST http://127.0.0.1:8000/api/ask -H "X-API-Key: $APP_API_KEY" -H 'Content-Type: application/json' -d '{"question":"¿Cuál es el estado de SOL-1001?","session_id":"demo_001"}'
curl -s http://127.0.0.1:8000/api/history/demo_001 -H "X-API-Key: $APP_API_KEY"
```

## Ruta B: Docker Compose

Instala Docker Desktop, crea `.env` como arriba y ejecuta:

```bash
docker compose up -d --build
docker compose exec ollama ollama pull qwen3:4b-instruct
docker compose exec ollama ollama pull embeddinggemma
```

El servidor queda disponible **solo en localhost**. La app y los modelos usan volúmenes persistentes; para datos reales se requiere autenticar el acceso, implementar permisos y cifrar backups. El contenedor de Ollama utiliza CPU por defecto.

## Pruebas

```bash
pytest -q
```

Esto usa modelos y vector store simulados y **no demuestra que el modelo real ya responda bien**. Para ejecutar casos reales, lanza el evaluador (cargará automáticamente `manual_demo.md` y `injection_demo.md`):

```bash
python scripts/evaluate.py
```

El script crea `data/evaluation_report.json` con pregunta, criterio esperado, respuesta real, fuentes, resultado de heurística y observaciones para completar manualmente. Su puntuación es orientativa, no sustituye una revisión de groundedness.

## Endpoints

| Método | Ruta | Función |
|---|---|---|
| GET | `/health` | Salud básica, sin exponer secretos |
| GET | `/ready` | Disponibilidad Ollama |
| POST | `/api/documents` | Ingesta documental |
| POST | `/api/ask` | Preguntar y usar herramientas |
| GET | `/api/history/{session_id}` | Historial por sesión |
| GET | `/api/stats` | Contadores |

### Ejemplo de respuesta

```json
{
  "answer": "El equipo de soporte valida la identidad del usuario [F1].",
  "session_id": "demo_001",
  "trace_id": "<uuid generado>",
  "tools_used": ["buscar_documentacion"],
  "sources": [{"ref": "F1", "document": "manual_demo.md", "chunk": 1,
               "excerpt": "...", "similarity": 0.72}]
}
```

Ejemplo **ilustrativo**, no un resultado real de evaluación. Las citas son etiquetas generadas sobre fragmentos retornados, no pruebas de que el contenido sea correcto; revisar manualmente.

## Decisiones, riesgos y nube

- [Diagrama y decisiones técnicas](docs/arquitectura.md).
- [Guion de video (máximo 7 minutos)](docs/demo_video.md).
- [Matriz de requisitos y estado](docs/checklist.md).
- [Evaluación real](scripts/evaluate.py).

### Seguridad y límites del MVP

La API key identifica el acceso **de la demo**, no usuarios individuales; el historial no tiene aislamiento por usuario. La exposición pública del servicio está **prohibida** sin control de identidad y autorización, TLS, rate-limiting y política de retención. Logs HTTP omiten contenido del prompt, pero el historial en SQLite almacena preguntas y respuestas. No cargar documentos con datos personales o secretos. No expone herramientas que modifiquen solicitudes.

### Despliegue AWS (variante adicional de código fuente)

Esta versión del repositorio incluye `cloud_aws/`, `lambda_function.py`,
`requirements-aws.txt` y `scripts/build_aws_zip.ps1`, preparados para
**Lambda Python 3.12 x86_64**. La prueba inicial `/health` funciona sin
DynamoDB ni Gemini; después se configuran los proveedores reales.

Consulta [la guía paso a paso para AWS](cloud_aws/GUIA_AWS.md).

**No se ha validado un despliegue real de esta variante.** Los tests prueban
la lógica local con dobles; generar el ZIP de dependencias requiere acceso
a PyPI para descargar las ruedas Linux compatibles. Desplegar en AWS es
opcional en el enunciado, pero agrega valor a la demostración si puedes
hacerlo dentro de cuotas gratuitas.

La integración con DynamoDB implementa una búsqueda acotada sobre fragmentos
vectorizados; no equivale a usar un servicio de búsqueda vectorial gestionado.

## Mejoras futuras

OAuth2/OIDC + RBAC por tenant/documento, versionado y eliminación de documentos, reranker, evaluación por juez LLM con corpus etiquetado, controles semánticos de groundedness, desidentificación PII, deduplicación por colección y políticas de retención, observabilidad OpenTelemetry, rate limit y cuotas, CI/CD, IaC y despliegue cloud tras estimar costos.

## Uso responsable de IA durante el desarrollo

El diseño y la implementación inicial se elaboraron con asistencia de ChatGPT. El uso responsable exige **revisar cada archivo, ejecutar las pruebas, inspeccionar dependencias, corregir resultados falsos y no afirmar cobertura sin evidencias**. Riesgos: APIs desactualizadas, prompt injection, rutas no autorizadas, expectativas de gratuidad en cloud, modelos locales que no siempre obedecen tool calling y falsos positivos en evaluación. Reportar las validaciones humanas y cambios reales realizados por el candidato antes de entregar.

### AWS sin CloudShell

El repositorio incluye `.github/workflows/build_lambda.yml` para empaquetar la aplicación en **GitHub Actions** sin credenciales AWS. Ver [pasos](docs/cloudshell_alternativa_github.md). El archivo descargado se despliega y prueba **en AWS Lambda**; construir el ZIP no es validar la ejecución cloud.
