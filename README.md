# InterviewGuard AI

InterviewGuard AI is a React/Vite and FastAPI application for scheduling and monitoring live interviews. It uses PostgreSQL, Socket.IO/WebRTC signalling, PDF reports, YOLOv8 phone detection, and optional trained deepfake inference.

## Architecture

`Browser → Render frontend (Nginx) → Render backend (FastAPI + Socket.IO) → Render PostgreSQL`

The frontend calls the backend using `VITE_API_URL` and Socket.IO uses `VITE_SOCKET_URL`. Both must be HTTPS Render URLs in production; Socket.IO automatically upgrades to secure WebSockets (`wss://`) from an HTTPS page.

## Local Docker setup

1. Copy `.env.example` to `.env` and set `POSTGRES_PASSWORD` and `JWT_SECRET`.
2. Run `docker compose up --build`.
3. Open http://localhost:5173. The API is http://localhost:8000, docs are http://localhost:8000/docs, and health is http://localhost:8000/health.

Compose starts PostgreSQL, waits for it to become healthy, runs `alembic upgrade head`, then starts FastAPI. Reports persist in the `reports_data` Docker volume.

For non-Docker development, install backend dependencies, configure `DATABASE_URL`, run `alembic upgrade head`, then run:

```powershell
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Start the frontend separately with `cd frontend; npm ci; npm run dev`. Its default local API and Socket.IO targets are `http://127.0.0.1:8000`.

## Render deployment

Create a Render PostgreSQL instance first. Then create two Docker Web Services from this repository. Use repository root (`.`) as the Root Directory for both services because the backend image packages the shared `training/` and `models/` directories.

### Backend service

- Dockerfile path: `backend/Dockerfile`
- Health check path: `/health`
- Docker command: handled by the Dockerfile; it runs migrations, then Uvicorn on Render's `PORT`.

Set these environment variables:

```text
ENVIRONMENT=production
DATABASE_URL=<Render PostgreSQL internal connection string>
JWT_SECRET=<long random secret>
FRONTEND_BASE_URL=https://<frontend>.onrender.com
INTERVIEW_BASE_URL=https://<frontend>.onrender.com
FRONTEND_URLS=["https://<frontend>.onrender.com"]
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=
MODEL_PATH=/app/models/deepfake_model.pth
MODEL_URL=
YOLO_MODEL_PATH=/app/models/yolov8n.pt
```

`DATABASE_URL` may use Render's legacy `postgres://` scheme; the application normalizes it. Leave SMTP variables blank if email is not configured—the interview is still saved and its link is returned. `FRONTEND_URLS` must be JSON as shown.

### Frontend service

- Dockerfile path: `frontend/Dockerfile`
- Set these **Docker build arguments** (not only runtime environment variables, because Vite embeds them while building):

```text
VITE_API_URL=https://<backend>.onrender.com/api
VITE_SOCKET_URL=https://<backend>.onrender.com
```

After deploying, update the backend's frontend URLs to the frontend service URL, then redeploy the backend. Never put database, JWT, or SMTP secrets in frontend variables.

## ML models

`models/yolov8n.pt` is included (about 6.5 MB) and is a real pre-trained COCO YOLOv8 model used to identify cell phones. It is not a deepfake model.

No trained deepfake classifier is present in this repository. The application does **not** run random weights or claim a deepfake result when it is absent. Supply a compatible trained checkpoint with `MODEL_PATH`, or supply a protected direct `MODEL_URL`; it is downloaded only when the local model is missing. If unavailable, deepfake detection is disabled while the remaining monitoring components continue.

MediaPipe Face Mesh is initialized from the installed MediaPipe package; it does not require a separate model file. A production deployment should use persistent storage or an artifact URL for any model too large for the Docker image.

## Troubleshooting

- If migrations fail, confirm the backend uses Render's PostgreSQL **internal** URL and that it is reachable from the backend service.
- If browser requests fail, check `VITE_API_URL`, `VITE_SOCKET_URL`, and the backend `FRONTEND_URLS` JSON value.
- If camera access fails, use the deployed HTTPS frontend (browser camera and microphone access requires a secure context outside localhost).
- Report PDF files are container-local on Render unless you attach persistent storage or move them to object storage; database report records remain in PostgreSQL.
