# Evidencias visuales IC7 — 28/10/2026

Capturas procedentes de las demostraciones compartidas durante la prueba. Se ha difuminado la región superior derecha para ocultar correos y datos de sesión visibles. No son capturas nuevas de AWS ni sustituyen un informe de pentesting.

| Archivo | Evidencia | Alcance |
|---|---|---|
| 01-rag-mfa.png | Consulta documental con referencias | RAG funcional en una ejecución |
| 02-herramientas.png | Clasificación crítica y consulta SOL-1001 | Herramientas estructuradas |
| 03-prompt-injection.png | Respuesta basada en fragmento legítimo | Ensayo adversarial específico |
| 04-aislamiento-documentos-usuario-a.png | 11 documentos privados, incluido archivo adversarial | Lista del usuario A |
| 05-aislamiento-documentos-usuario-b.png | 0 documentos privados | Lista del usuario B |
| 06-aislamiento-historial-usuario-a.png | Conversaciones del usuario A | Historial por usuario |
| 07-aislamiento-historial-usuario-b.png | Historial propio, distinto del usuario A | Historial por usuario |
| 08-github-pr7.png | Evaluación formal fusionada en main | Trazabilidad documental |

## Evidencia de terminal registrada durante las pruebas (transcripción)

- `python -m pytest -q`: **55 passed in 1.79s**, tras el merge documental previo.
- RAG MFA, Lambda `RequestId=6ac2bf2e-08ee-40ee-8f44-4fa155562ac3`: `embedContent=342 ms`, `IC7_RAG_RETRIEVAL=383 ms`, `generateContent=1495 ms`, `REPORT Duration=2007.37 ms`, `HTTP 200`.
- Prompt injection, `RequestId=a18f83af-da01-4ccc-9c83-41c06dd2637e`: `embedContent=223 ms`, recuperación `243 ms`, generación `905 ms`, `REPORT Duration=1202.48 ms`, `HTTP 200`.

**Nota:** Las cifras anteriores son transcripciones de salidas verificadas en la conversación, no imágenes de la consola ni mediciones estadísticas agregadas. Para una auditoría externa conviene adjuntar archivos de logs exportados, sin credenciales ni datos personales.
