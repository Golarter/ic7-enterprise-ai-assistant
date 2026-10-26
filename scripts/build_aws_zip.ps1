# Construye un paquete Linux x86_64 para AWS Lambda Python 3.12 desde Windows.
# No modifica ni crea ningún recurso AWS.
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$build = Join-Path $root '_aws_build'
$out = Join-Path $root 'ic7-lambda-deploy.zip'
if (Test-Path $build) { Remove-Item $build -Recurse -Force }
New-Item -ItemType Directory -Path $build | Out-Null

python -m pip install --disable-pip-version-check --no-compile --platform manylinux2014_x86_64 --implementation cp --python-version 3.12 --only-binary=:all: --target "$build" -r (Join-Path $root 'requirements-aws.txt')
if ($LASTEXITCODE -ne 0) { throw 'Fallo la instalacion. No subir un ZIP incompleto.' }
Copy-Item (Join-Path $root 'app') "$build/app" -Recurse
Copy-Item (Join-Path $root 'cloud_aws') "$build/cloud_aws" -Recurse
New-Item -ItemType Directory -Path "$build/data" | Out-Null
Copy-Item (Join-Path $root 'data/solicitudes_demo.json') "$build/data/solicitudes_demo.json"
Copy-Item (Join-Path $root 'lambda_function.py') "$build/lambda_function.py"
Get-ChildItem "$build" -Recurse -Directory -Include '__pycache__','.pytest_cache' | Remove-Item -Force -Recurse
if (Test-Path $out) { Remove-Item $out -Force }
# ZipFile de Python: permite nombres internos con / y rutas relativas, compatibles con Lambda.
$env:IC7_BUILD = $build
$env:IC7_ZIP = $out
@'
import os, zipfile
from pathlib import Path
root = Path(os.environ['IC7_BUILD']); target=Path(os.environ['IC7_ZIP'])
with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in root.rglob('*'):
        if p.is_file() and p.suffix not in ('.pyc', '.pyo'):
            z.write(p,p.relative_to(root).as_posix())
print(f'PAQUETE: {target} ({target.stat().st_size/1024/1024:.2f} MiB)')
with zipfile.ZipFile(target) as z:
    assert 'lambda_function.py' in z.namelist()
    assert 'mangum/__init__.py' in z.namelist()
    assert any(n.startswith('fastapi/') for n in z.namelist())
print('Estructura basica validada; aun falta comprobar en Lambda.')
'@ | python -
if ($LASTEXITCODE -ne 0) { throw 'Fallo la compresion del ZIP' }
