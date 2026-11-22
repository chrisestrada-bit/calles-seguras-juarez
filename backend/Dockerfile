# API FastAPI de Calles Seguras Juárez.
# El contexto de construcción es la RAÍZ del repositorio (ver docker-compose.yml) porque la imagen
# también incluye db/ (Alembic y seed.py).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/srv

WORKDIR /srv

COPY backend/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

COPY backend/app ./app
COPY db ./db

# Usuario sin privilegios.
RUN useradd --system --no-create-home --uid 10001 api && chown -R api:api /srv
USER api

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
