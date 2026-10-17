# MindMate backend (FastAPI + memory layer + Nemotron agents).
# Build:  docker build -t mindmate-backend .
# Run:    docker run -p 8000:8000 --env-file .env mindmate-backend
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /srv/mindmate

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py alembic.ini conftest.py ./
COPY app ./app
COPY alembic ./alembic
COPY data ./data
COPY scripts ./scripts

# Apply migrations (no-op when the schema is current), then serve.
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
