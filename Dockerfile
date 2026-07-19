# Build the React client once, then serve it from the FastAPI service.
FROM node:20-slim AS frontend-build

WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim AS runtime

WORKDIR /app

# Runtime libraries used by OpenCV, PyTorch, and MediaPipe.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY training/ ./training/
COPY models/ ./models/
COPY --from=frontend-build /build/frontend/dist ./frontend-dist/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/backend:/app

EXPOSE 8080

# Railway injects PORT at runtime. The fallback keeps local Docker runs usable.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
