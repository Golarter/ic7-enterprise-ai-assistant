# AWS CloudShell bloqueado: flujo GitHub Actions

Si CloudShell muestra «La verificación de su cuenta está en curso», no seguir recreándolo. La función Lambda ya existente funciona.

## Empaquetar sin credenciales AWS ni ejecución local

1. Crear un repositorio GitHub **privado** vacío.
2. Descargar este ZIP de código fuente y **extraerlo** (no ejecutar nada en tu PC).
3. Subir **el contenido** de la carpeta `enterprise_ai_assistant/` a la **raíz** del repositorio, incluyendo `.github/workflows/build_lambda.yml`. No subir secretos `.env` ni claves de API.
4. GitHub > **Actions** > **Construir ZIP AWS Lambda (sin credenciales AWS)** > **Run workflow**.
5. Al completar el job, descargar el artefacto `ic7-lambda-python312-x86_64` y extraerlo. Dentro debe estar **`ic7-lambda-deploy.zip`**.
6. AWS Lambda > función `ic7-enterprise-ai-assistant` en `us-east-1` > **Código** > **Cargar desde** > **archivo .zip** > subir **`ic7-lambda-deploy.zip`**. No subir el ZIP de código fuente ni el ZIP externo de GitHub Actions.
7. En **Configuración** > **Configuración de tiempo de ejecución** establecer `lambda_function.lambda_handler`. Runtime Python 3.12 x86_64.
8. En **Probar**, crear evento HTTP API v2 para `GET /health` tal como en `cloud_aws/GUIA_AWS.md`. La respuesta esperada es HTTP 200 y `configured:false`.

La ejecución de `/health` no requiere Gemini ni DynamoDB, y no convierte la API en una URL pública. Sin embargo, Lambda y CloudWatch pueden tener consumo facturable según las cuotas de la cuenta.

**Importante:** una alerta de presupuesto no bloquea los cobros. No crear aún una Function URL pública ni tablas de DynamoDB.

## Soporte AWS

En paralelo se puede solicitar soporte de Cuenta y facturación en https://console.aws.amazon.com/support/ para solucionar el bloqueo de CloudShell. No es necesario para continuar con el despliegue manual.
