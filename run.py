"""Arranque explícito para evitar requerir secretos al importar módulos en pruebas."""
import uvicorn
from app.main import create_app

if __name__ == '__main__':
    uvicorn.run(create_app(), host='0.0.0.0', port=8000)
