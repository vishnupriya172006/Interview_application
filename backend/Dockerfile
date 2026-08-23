# Build with the repository root as context: docker build -f backend/Dockerfile .
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libgomp1 \
    && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt
COPY backend/ ./backend/
COPY training/ ./training/
COPY models/ ./models/
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/app/backend:/app \
    MODEL_PATH=/app/models/deepfake_model.pth YOLO_MODEL_PATH=/app/models/yolov8n.pt
WORKDIR /app/backend
EXPOSE 8000
CMD ["sh", "./start.sh"]
