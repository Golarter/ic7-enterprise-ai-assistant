# Resultados y evidencias técnicas de IC7

## Repositorio y pruebas

- Repositorio: `https://github.com/Golarter/ic7-enterprise-ai-assistant`
- Pull Request: `https://github.com/Golarter/ic7-enterprise-ai-assistant/pull/5`, tres commits fusionados.
- Commit de `main` tras fusión: `5f3b79b`.
- `git diff --exit-code main origin/fix/gemini-rag-performance`: sin diferencias.
- `.venv\Scripts\python.exe -m pytest -q`: **55 passed in 1.82s**.

## Despliegue probado

- Interfaz: `https://main.de7h6ja4dscnj.amplifyapp.com/`
- API: `https://xwejxdr534.execute-api.us-east-1.amazonaws.com`
- Lambda: `ic7-enterprise-ai-assistant`, `Active / Successful`, última revisión conocida `4b38970b-d84c-49f8-97a5-717fd80b983a`.
- CloudWatch: `/aws/lambda/ic7-enterprise-ai-assistant`.
- AWS y Cognito requieren credenciales y cuotas válidas; no almacenar credenciales en el repo.

## Observaciones de la demo

| Observación | Evidencia | Alcance |
|---|---|---|
| MFA con fuentes | `/api/ask` HTTP 200; `[F1]`, `[F3]` | Un caso RAG funcional |
| 2.007 ms | Lambda `REPORT` 2026-10-27 14:43 UTC | Una ejecución, no percentil |
| Clasificación Crítica | Captura frontend y HTTP 200 | Intención inequívoca |
| `SOL-1001` En progreso | Captura frontend y HTTP 200 | Dataset simulado |
| Abstención | Pregunta viaje a Marte | Caso puntual de información fuera de corpus |
| Error proveedor | `TimeoutError generateContent`, 503 | Riesgo reproducido |

## Capturas recomendadas para la entrega

1. Interfaz Cognito autenticada (ocultar correo/tokens).
2. Documento cargado y respuesta MFA citada.
3. Herramientas de prioridad y solicitud con sus resultados.
4. CloudWatch mostrando operaciones Gemini y duración Lambda (recortar identificadores si procede).
5. PR #5 fusionada, Actions éxito y 55 pruebas.
6. Breve demostración de abstención y explicación de prompt injection.

**Precaución:** este documento registra evidencia textual aportada durante las pruebas. Las capturas finales deben seleccionarse y adjuntarse por separado; no se simulan ni se consideran incorporadas automáticamente.
