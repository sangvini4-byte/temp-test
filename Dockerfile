FROM python:3.11-slim

WORKDIR /app

# build-essential — на случай ARM-серверов (Oracle Free Tier, некоторые Hetzner),
# где для pyswisseph нет готового wheel и pip компилирует из исходников.
# curl — нужен docker-compose healthcheck'у (см. docker-compose.yaml).
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
