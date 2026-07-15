FROM node:20-alpine AS frontend-build
WORKDIR /build
COPY package.json package-lock.json tsconfig.json vite.config.ts ./
RUN npm ci
COPY src/frontend/app ./src/frontend/app
RUN npm run build:frontend

FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8000 THESISION_DATA_DIR=/tmp/thesision
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --create-home --uid 10001 thesision \
    && mkdir -p /tmp/thesision \
    && chown -R thesision:thesision /app /tmp/thesision

COPY --chown=thesision:thesision src ./src
COPY --from=frontend-build --chown=thesision:thesision /build/src/frontend/app/dist ./src/frontend/app/dist
COPY --chown=thesision:thesision README.md ./

USER thesision
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live')" || exit 1
CMD ["sh", "-c", "uvicorn src.backend.app.main:app --host 0.0.0.0 --port $PORT"]
