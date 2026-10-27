# IC7 — Validación de seguridad y pertinencia de RAG (V4)

## Cambios implementados

1. **Fuentes citadas:** `sources` contiene únicamente los fragmentos cuyos identificadores `[F#]` aparecen en la respuesta. Ya no incluye todos los candidatos recuperados por el motor vectorial.
2. **Relevancia relativa:** un fragmento se descarta cuando su similitud queda más de 0,10 por debajo de la mejor coincidencia de la consulta, o por debajo del umbral mínimo efectivo de 0,30. Estos umbrales son heurísticos de demostración y requieren evaluación con documentos reales.
3. **Instrucciones en documentos:** se descartan líneas con patrones evidentes de órdenes dirigidas al asistente antes de entregarlas al LLM y antes de devolver extractos por API. Los originales se conservan en el almacenamiento de demo para trazabilidad.
4. **Abstenciones y citas inválidas:** no se devuelve `sources` cuando el agente declara información insuficiente o fabrica referencias inexistentes.
5. **Herramientas:** la lista permitida continúa limitada a consultas de solo lectura; se deduplican nombres en `tools_used`.

## Cómo verificar

En GitHub Actions se ejecutan todos los tests con `PYTHONPATH=. python -m pytest -q`. Se añadieron nueve pruebas, incluyendo:

- Fuentes relevantes citadas y exclusión de coincidencias incidentales.
- Eliminación de órdenes evidentes en fragmentos documentales.
- Tres formas de abstención sin citas.
- Rechazo de referencias inexistentes (`[F99]`).
- Rechazo de herramientas no autorizadas.
- Respuestas que legítimamente citan más de un documento.

## Pruebas AWS pendientes después de subir esta versión

1. Repetir pregunta sobre la política Mesa de Ayuda: solo deben aparecer fuentes que el modelo cite; el extracto mostrado no debe contener la orden `SEGURIDAD DESACTIVADA`.
2. Repetir la consulta sobre vacaciones: respuesta de abstención y `sources: []`.
3. Repetir pregunta por el procedimiento de VPN: respuesta documentada y referencia `[F1]`.
4. Verificar auditoría y `trace_id` en DynamoDB.

**Alcance:** esto es endurecimiento básico, no protección completa contra prompt injection. Para producción se requiere aislamiento de confianza, controles de acceso por documento y usuario, validación del origen, políticas de salida, pruebas adversariales más amplias y revisión de riesgos de exfiltración. No se ha confirmado todavía ninguna prueba AWS con esta V4.

## Anexo — Evidencia AWS posterior a V4 (27-10-2026)

La nota anterior «ninguna prueba AWS confirmada» era válida al redactar V4, pero ya no describe el estado actual. Se ejecutó una consulta sobre SOP-002 con respuesta citada y `/api/ask` HTTP 200; `IC7_RAG_RETRIEVAL` informó 4 evidencias, y se citaron `[F1]` y `[F3]`. La pregunta fuera de corpus sobre viajes a Marte produjo abstención sin fuentes. Se validó recuperación de `SOL-1001` y clasificación de caída empresarial como Crítica. La separación de documentos e historial por usuario fue probada previamente con dos cuentas Cognito. Estas pruebas no sustituyen red teaming ni una auditoría de permisos IAM.

**Observación de seguridad y operación:** se registró un timeout `generateContent` de 12.021 ms con HTTP 503 el mismo día; las herramientas estructuradas directas respondieron HTTP 200 sin llamadas Gemini en las ejecuciones observadas. No incluir tokens ni claves en capturas o registros publicados.
