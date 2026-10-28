# Desarrollo asistido por IA (AI-assisted development) — IC7

**Proyecto:** IC7 Enterprise AI Assistant
**Fecha de corte:** 28 de octubre de 2026
**Alcance:** explicación del proceso de asistencia y verificación durante el desarrollo de esta prueba técnica.

## 1. Herramientas y alcance real

Se empleó **ChatGPT** como apoyo para analizar el reto, contrastar decisiones arquitectónicas, redactar instrucciones, proponer modificaciones de código, diseñar casos de prueba, diagnosticar errores a partir de salidas de consola y elaborar borradores de documentación. La ejecución de comandos, autenticación en AWS, pruebas en el navegador, revisión de Git y despliegues fueron realizados por el candidato.

Este documento **no atribuye uso efectivo** de Kiro, Claude Code, Cursor, GitHub Copilot ni OpenAI Codex en este repositorio IC7, porque la evidencia reunida aquí no permite afirmarlo. El uso de GitHub Actions corresponde a automatización de construcción, no a generación de código por IA.

## 2. Tareas apoyadas con IA

| Área | Apoyo de IA | Validación realizada por el candidato |
|---|---|---|
| Diseño de solución | Comparación de flujo local (Ollama/Chroma) y flujo AWS (Amplify/Cognito/API Gateway/Lambda/Gemini/DynamoDB). | Revisión de requisitos, despliegue AWS y pruebas funcionales. |
| RAG y herramientas | Propuestas de optimización de rutas documentales y ejecución directa de herramientas deterministas. | `pytest`, consultas reales, citas, abstención y análisis de logs. |
| Seguridad | Diseño de escenarios de aislamiento de usuarios y prompt injection. | Dos sesiones Cognito; documento sintético de inyección y respuesta observada. |
| Diagnóstico de rendimiento | Interpretación de `TimeoutError`, HTTP 503 y latencias; propuestas de instrumentación. | CloudWatch: `embedContent`, `IC7_RAG_RETRIEVAL`, `generateContent`, `REPORT`. |
| Desarrollo y Git | Preparación de parches y comandos para ramas, commits y pull requests. | `py_compile`, `git diff --check`, 55 pruebas, PR #5, #6 y #7. |
| Documentación | Borradores de README, arquitectura, decisiones y evaluación. | Comparación con el código, resultados y enunciado; revisión antes de integración. |

## 3. Proceso de validación del código sugerido

1. **Inspección del código existente** antes de modificarlo: lectura de `app/agent.py`, `cloud_aws/gemini.py`, `cloud_aws/api.py` y pruebas.
2. **Aplicación incremental** en ramas específicas, sin modificar producción directamente desde el editor local.
3. **Comprobación sintáctica:** `python -m py_compile` en los módulos cambiados.
4. **Regresión automatizada:** 55 pruebas aprobadas en el estado integrado.
5. **Control de cambios:** `git diff --check`, preparación selectiva con `git add`, commits y pull requests.
6. **Verificación en entorno real:** pruebas con interfaz web, Cognito, Lambda y CloudWatch.
7. **Corrección basada en evidencia:** una clasificación errónea como `Baja` se corrigió a `Crítica`; los timeouts en Gemini motivaron instrumentación y rutas deterministas.

La aceptación de los cambios no se basó únicamente en la respuesta de una herramienta de IA.

## 4. Incidencias que obligaron a revisar propuestas

### Latencia y disponibilidad del proveedor

Se observó una solicitud Lambda de 31.183,17 ms y errores `TimeoutError` de Gemini. Se instrumentaron las operaciones, se redujeron llamadas innecesarias y se separaron herramientas estructuradas de la generación. Una consulta documental posterior registró 2.007,37 ms y otra prueba adversarial 1.202,48 ms. **Son observaciones puntuales**, no una garantía de tiempo de respuesta ni un benchmark repetido. Persisten fallos intermitentes del proveedor.

### Clasificación crítica

Una descripción de caída general de autenticación fue clasificada inicialmente como prioridad `Baja`. Se revisaron las reglas, se agregó reconocimiento del impacto empresarial y se incorporaron pruebas. La clasificación es **orientativa**, no una decisión operativa automática.

### Seguridad y datos no confiables

Se usó un documento sintético con una instrucción dirigida al asistente. En el ensayo observado, el asistente respondió con pasos autorizados y citó `[F1]` sin obedecer esa instrucción. Se observó separación visual de documentos e historiales entre dos usuarios Cognito. Esto **no equivale** a una evaluación de penetración ni a resistencia universal frente a prompt injection.

## 5. Riesgos del desarrollo asistido por IA y controles

| Riesgo | Control aplicado o limitación reconocida |
|---|---|
| Código aparentemente correcto pero incompatible | Compilación, pruebas y ejecución sobre el repositorio real. |
| Respuestas o diagnósticos de IA infundados | Confirmación con CloudWatch y observación del comportamiento de la aplicación. |
| Regresiones entre funcionalidades | Pruebas automatizadas y commits por funcionalidad. |
| Prompt injection y fuga de secretos | Documentos sintéticos, citas verificables, controles por identidad y no publicar credenciales. |
| Sobreestimar resultados | Separar tests simulados de ensayos reales; no presentar latencias individuales como promedios. |
| Dependencia de proveedor externo | Timeouts limitados, errores controlados y herramientas directas cuando su intención es inequívoca. |
| Uso de credenciales de alto privilegio | **Pendiente prioritario:** sustituir la identidad `root` observada en AWS CLI por identidad/rol de privilegio mínimo para operación habitual. |

## 6. Trazabilidad

- **PR #5:** optimización RAG, prioridad, métricas y rutas directas.
- **PR #6:** consolidación de documentación AWS.
- **PR #7:** matriz formal de evaluación y evidencia de seguridad.
- **Evidencia de pruebas:** 55 resultados aprobados de `pytest` y registros CloudWatch compartidos.
- **Matriz de casos:** `docs/evaluacion_rag.md`.

## 7. Reflexión del candidato

La IA aceleró el análisis, la preparación de alternativas y la documentación, pero también produjo propuestas que debieron ajustarse con evidencia de ejecución. La validación humana consistió en revisar el alcance de cada cambio, comprobar resultados reales y reconocer límites de las pruebas. El criterio de aceptación fue el comportamiento reproducible del sistema y el cumplimiento del requerimiento, no la confianza en la herramienta generativa.

**Pendientes no resueltos:** evaluación agregada de groundedness, pruebas adversariales más amplias, operación con identidad AWS de privilegio mínimo y mediciones estadísticas de latencia/disponibilidad.
