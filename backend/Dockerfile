FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    VOICE_ENABLED=false AUTOMATION_ENABLED=true OLLAMA_WARMUP_ENABLED=false
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libportaudio2 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /app/data/platform && useradd --create-home naya && chown -R naya:naya /app
USER naya
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers"]
