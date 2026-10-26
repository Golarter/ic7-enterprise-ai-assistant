# Despliegue de IC7 en AWS Lambda (Python 3.12, x86_64)

## Estado real

- **Se construyó y probó la aplicación local** en tests automatizados con dependencias simuladas.
- **La variante AWS se puede empaquetar** con `scripts/build_aws_zip.ps1`.
- **No** está desplegada ni probada con la cuenta AWS del candidato: requiere que este cree tablas y configure claves.
- Las cuotas gratuitas dependen de recursos y consumo, **presupuesto de gasto cero alerta, no bloquea**.
- **No crear recursos hasta verificar que corresponden al nivel gratuito aplicable.**

## Fase A: empaquetar y verificar `/health` (sin DynamoDB ni Gemini)

1. En Windows con Python y conexión a internet, extraer el ZIP de código fuente en una carpeta local.
2. Abrir PowerShell en la raíz del proyecto y ejecutar:

   ```powershell
   Set-ExecutionPolicy -Scope Process Bypass
   .\scripts\build_aws_zip.ps1
   ```

3. Comprobar que se generó `ic7-lambda-deploy.zip`. **No** subir el ZIP del proyecto completo.
4. En Lambda (`ic7-enterprise-ai-assistant`) > pestaña Código > **Cargar desde** > Archivo `.zip` > seleccionar `ic7-lambda-deploy.zip`.
5. En **Configuración > Configuración de tiempo de ejecución > Editar**, handler `lambda_function.lambda_handler`.
6. Conservar Python 3.12, x86_64, sin VPC ni Function URL. Memoria 256 MB, timeout 30 s (para smoke test `health`, no model calls). Evitar concurrency alta.
7. Prueba de evento HTTP API v2 (`/health`), **NO** `{}`:

   ```json
   {
     "version":"2.0",
     "routeKey":"GET /health",
     "rawPath":"/health",
     "rawQueryString":"",
     "headers":{"host":"localhost"},
     "requestContext":{"http":{"method":"GET","path":"/health","sourceIp":"127.0.0.1","userAgent":"ConsoleTest"},"requestId":"demo"},
     "isBase64Encoded":false
   }
   ```

   Respuesta esperada: `statusCode:200`, `body` JSON con `"platform":"aws-lambda"` y `"configured":false`.

## Fase B: persistencia (requiere validar el presupuesto y cuotas aplicables)

Crear **dos tablas** DynamoDB, clase **Standard**, modo **Provisioned**, en **us-east-1**:

- `ic7-demo-docs`: clave de partición `pk` (String), ordenación `sk` (String). Capacidad provisionada inicial: 2 RCU/2 WCU, sin autoscaling, sin backups PITR. 
- `ic7-demo-audit`: iguales claves y capacidad. No activar streams, backups continuos, replicación global ni aceleradores.

IAM del rol **de ejecución de esta Lambda**: política mínima `dynamodb:PutItem`, `dynamodb:Query` en ARN de **ambas** tablas. CloudWatch básico ya lo aporta el rol inicial. No crear access keys.

Variables de entorno Lambda:

- `APP_API_KEY`: cadena aleatoria larga, solo en AWS (no en repositorio).
- `IC7_DOCS_TABLE=ic7-demo-docs`
- `IC7_AUDIT_TABLE=ic7-demo-audit`
- `GEMINI_API_KEY`: clave de Google AI Studio, mantenida secreta.
- `GEMINI_CHAT_MODEL=gemini-2.5-flash` (verificar la tarifa/modelo disponible en la cuenta).
- `GEMINI_EMBED_MODEL=gemini-embedding-001` (verificar cuota gratuita).

*Seguridad*: variables de entorno se ven para quien tenga acceso a la configuración; en una implementación empresarial, usar Secrets Manager y control IAM, pero puede costar dinero. La API exige `X-API-Key` para rutas salvo `/health`, y no debe quedar expuesta públicamente sin IAM y límites. **No habilitar `Function URL` con AuthType NONE**. Con `AWS_IAM` la llamada HTTP necesita firma SigV4.

Para las invocaciones con Gemini, aumentar timeout hasta 120 s solo tras confirmar las cuotas, y usar datos sintéticos. No registrar preguntas/respuestas sensibles en la consola.

## Fase C: pruebas de aceptación reales

- Ingestar `data/manual_demo.md` por POST `/api/documents`.
- Consultar políticas con fuentes `[F1]`.
- Probar `SOL-1001` con la herramienta `consultar_solicitud`.
- Probar `clasificar_prioridad`.
- Ver historial en `/api/history/{session_id}`.
- Probar rechazo sin `X-API-Key`, pregunta sin fuente, documento de inyección.
- Comprobar que la latencia, llamadas a Gemini, límites y uso de AWS permanecen bajo las cuotas gratuitas.

## Limitaciones declaradas del MVP

- DynamoDB usado como repositorio vectorial de demo con consulta acotada a 50 fragmentos (búsqueda de fuerza bruta con coseno), **no un motor vectorial de producción**.
- La ingesta persiste fragmentos/documento en DynamoDB, no el archivo original completo.
- Las consultas pueden agotar cuotas gratuitas de Gemini; el servicio de IA puede devolver 429/503.
- El historial usa API key compartida, no aislamiento de usuarios (no usar para datos reales).
- Solo tests automatizados locales; no afirmar que el despliegue se validó sin una ejecución real.

## Referencias oficiales (revisadas 2026-10-25)

- AWS empaquetar Python Linux: https://docs.aws.amazon.com/lambda/latest/dg/python-package.html
- AWS función URL IAM: https://docs.aws.amazon.com/lambda/latest/dg/urls-configuration.html
- AWS DynamoDB free tier y precios: https://aws.amazon.com/dynamodb/pricing/
- Google Gemini modelos y costos: https://ai.google.dev/gemini-api/docs/pricing
- Google claves API y riesgos: https://ai.google.dev/gemini-api/docs/api-key
