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

`DATABASE_URL` may use Render's legacy `postgres://` scheme; the application normalizes it. Leave SMTP variables blank if email is not configured—the interview is still saved and its link is returned. Password recovery sends a one-hour, reset-only link only when SMTP credentials and a frontend URL are configured; otherwise the API returns a generic response without logging a token. `FRONTEND_URLS` must be JSON as shown and must use HTTPS in production.

New meeting invitation codes are high-entropy bearer credentials: anyone with the code can pass the public join preflight and join as the candidate. Share invitation links privately. Meetings created before this change retain their older, lower-entropy numeric codes; schedule a new interview if an old link may have been exposed. Public join preflight returns only the candidate name, scheduled time, duration, and status needed by the lobby.

### Frontend service

- Dockerfile path: `frontend/Dockerfile`
- Set these **Docker build arguments** (not only runtime environment variables, because Vite embeds them while building):

```text
VITE_API_URL=https://<backend>.onrender.com/api
VITE_SOCKET_URL=https://<backend>.onrender.com
```

After deploying, update the backend's frontend URLs to the frontend service URL, then redeploy the backend. If the peers cannot establish a direct WebRTC connection across their networks, configure a TURN relay on the frontend service as Docker build arguments:

```text
VITE_TURN_URL=turn:<turn-host>:3478?transport=udp,turns:<turn-host>:5349?transport=tcp
VITE_TURN_USERNAME=<short-lived-turn-username>
VITE_TURN_CREDENTIAL=<short-lived-turn-credential>
```

TURN credentials are delivered to browsers as part of WebRTC setup; use provider-issued, short-lived credentials rather than a permanent secret. Redeploy the frontend after changing any `VITE_*` build argument. Never put database, JWT, or SMTP secrets in frontend variables.

## ML models

`models/yolov8n.pt` is included (about 6.5 MB) and is a real pre-trained COCO YOLOv8 model used to identify cell phones. It is not a deepfake model.

No trained deepfake classifier is present in this repository. The application does **not** run random weights or claim a deepfake result when it is absent. Supply a compatible trained checkpoint with `MODEL_PATH`, or supply a protected direct `MODEL_URL`; it is downloaded only when the local model is missing. If unavailable, deepfake detection is disabled while the remaining monitoring components continue.

MediaPipe Face Mesh is initialized from the installed MediaPipe package; it does not require a separate model file. A production deployment should use persistent storage or an artifact URL for any model too large for the Docker image.

Face Mesh gaze output is a heuristic observation, not a calibrated attention measure. There is no liveness challenge-response implementation, so liveness and the combined integrity score are reported as unavailable. Reports mark incomplete evidence as **Review Required**. Automated flags require human review and are not proof of misconduct.

## Troubleshooting

- If migrations fail, confirm the backend uses Render's PostgreSQL **internal** URL and that it is reachable from the backend service.
- If browser requests fail, check `VITE_API_URL`, `VITE_SOCKET_URL`, and the backend `FRONTEND_URLS` JSON value.
- If the room says **Disconnected**, make sure `VITE_SOCKET_URL` is the backend's public HTTPS origin (without `/api`) and redeploy the frontend.
- If Socket.IO is connected but either remote video stays blank, configure a TURN relay as above and verify both users joined the same meeting ID. STUN alone cannot relay media through every NAT or firewall.
- If camera access fails, use the deployed HTTPS frontend (browser camera and microphone access requires a secure context outside localhost).
- Report PDF files are container-local on Render unless you attach persistent storage or move them to object storage; database report records remain in PostgreSQL.

## WebRTC acceptance test

1. Deploy the frontend and backend over HTTPS, then open the same invitation in two separate browsers or devices on different networks (for example, one on Wi-Fi and one on a mobile hotspot).
2. Allow camera and microphone access on both devices. Confirm each participant sees the remote video as the main feed and their own video in the preview.
3. Speak and mute/unmute on each device in turn to verify audio in both directions. Check the room status separately for Socket.IO signaling and WebRTC media; a connected signaling socket alone does not mean media is flowing.
4. In Chromium, inspect `chrome://webrtc-internals` on both devices and confirm the peer connection reaches `connected` and that audio/video bytes increase in both directions.
5. Repeat with a TURN relay configured if direct ICE connectivity fails. Verify the selected candidate pair uses a relay candidate where expected. If TURN is unavailable or blocked by the network, cross-network media may not connect; do not treat a successful same-network test as proof of universal connectivity.
