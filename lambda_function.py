"""Handler de AWS Lambda para Function URLs API Gateway v2."""
from mangum import Mangum
from cloud_aws.api import create_cloud_app

app = create_cloud_app()
lambda_handler = Mangum(app, lifespan='off')
