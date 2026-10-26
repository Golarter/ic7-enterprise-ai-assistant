FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /service
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd -m app
COPY app ./app
COPY data/solicitudes_demo.json ./data/solicitudes_demo.json
COPY run.py ./run.py
RUN mkdir -p /service/data && chown -R app:app /service/data
USER app
EXPOSE 8000
CMD ["python", "run.py"]
