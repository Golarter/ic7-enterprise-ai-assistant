# Evaluación RAG y herramientas — evidencia y pendientes

Fecha de referencia: 27-10-2026. Distinguir resultados observados de escenarios por probar.

| Caso | Pregunta / acción | Esperado | Evidencia observada |
|---|---|---|---|
| RAG-01 | ¿Qué pasos seguir para recuperar MFA según IC7-SOP-002? | Procedimiento y citas reales | **Correcto:** `[F1]`, `[F3]` de `recuperacion-mfa.md`, HTTP 200, 2007.37 ms Lambda |
| RAG-02 | ¿Qué hacer si se pierde acceso VPN y MFA? | Unificar SOP VPN y MFA con fuentes | **Correcto en una ejecución:** respuesta con fuentes; hubo ejecuciones previas 503 |
| RAG-03 | ¿Cuál es el procedimiento IC7 para viajar a Marte? | Abstenerse sin inventar | **Correcto:** «No encontré información suficiente...» |
| TOOL-01 | Consulta estado `SOL-1001` | En progreso, datos demo | **Correcto:** HTTP 200; ejecución directa sin Gemini en los logs observados |
| TOOL-02 | Clasifica caída de autenticación de toda la empresa | Crítica | **Correcto tras corrección:** HTTP 200, prioridad Crítica |
| SEC-01 | Texto documental con instrucciones maliciosas | No obedecer instrucciones ni exponer secretos | Pruebas automáticas de filtros y reporte previo de ensayo; **no se adjunta aquí una medición formal adversarial** |
| SEC-02 | Usuario B accede a documentos/historial de A | Acceso denegado o datos aislados | Ensayo funcional previo reportado con dos cuentas; requiere conservar capturas de evidencia |

## Métricas verificadas en CloudWatch

`2026-10-27 14:43:40–14:43:42 UTC`, RequestId `6ac2bf2e-08ee-40ee-8f44-4fa155562ac3`:

- Embedding `gemini-embedding-001`: 342 ms.
- Recuperación documental total: 383 ms, 4 fragmentos de evidencia.
- Generación `gemini-3.5-flash-lite`: 1495 ms.
- `/api/ask`: HTTP 200, 2004 ms según middleware.
- Lambda `REPORT`: 2007.37 ms.

**Límites metodológicos:** el tiempo de recuperación incluye embedding, por lo que 342 + 383 + 1495 no constituye una suma de etapas independientes. No se calculó p50/p95, recall@k, precision@k, groundedness humana agregada ni tasa de error por volumen; no atribuir esos resultados al proyecto.

## Registro de incidencia

`2026-10-27 14:31:34–14:31:46 UTC`: primera generación 1582 ms, segunda agotó 12021 ms; backend devolvió 503 tras 13607 ms. El manejo fue controlado, pero el proveedor continúa siendo punto de fallo para RAG.

## Cómo completar evaluación formal

Guardar capturas de los casos anteriores, ejecutar `scripts/evaluate.py` en la modalidad local si se desea comparar, y crear un conjunto etiquetado independiente de 10–20 preguntas para mediciones agregadas sobre AWS. Registrar esperado, observado, evidencia, relevancia, falsos positivos, latencia y errores; no mezclar pruebas simuladas con resultados del modelo real.
