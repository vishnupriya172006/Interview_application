# InterviewGuard AI
> **A Multimodal Framework for Real-Time Deepfake Detection and Interview Integrity Assessment in Live Video Interviews**

InterviewGuard AI is an end-to-end, production-ready full-stack application designed to secure online video interviews. It uses a multimodal deep learning and computer vision framework to continuously evaluate candidate integrity in real-time, detecting face deepfake injects, monitoring gaze offsets, assessing physical liveness indicators, and identifying unauthorized mobile device presence.

---

## 🏛️ System Architecture

The application is structured into decoupled frontend, backend, and machine learning components:

```mermaid
graph TD
    subgraph Client [Browser Clients]
        Recruiter[Recruiter Dashboard]
        Candidate[Candidate Lobby & Room]
    end

    subgraph Backend [FastAPI Server]
        API[REST Routing & Auth]
        Socket[Socket.IO Server]
        AIEngine[Multimodal AI Engine]
        PDFGen[ReportLab PDF Service]
    end

    subgraph MLPipeline [ML Models & CV]
        PyTorch[Deepfake Classifier - EfficientNet]
        YOLO[YOLOv8 Object Detector]
        FaceMesh[MediaPipe Face Mesh]
    end

    subgraph DB [Database Layer]
        Postgres[(PostgreSQL)]
    end

    Candidate -- "1. Video call (P2P stream)" --- Recruiter
    Candidate -- "2. Socket.IO base64 frame stream" --> Socket
    Socket --> AIEngine
    AIEngine --> PyTorch
    AIEngine --> YOLO
    AIEngine --> FaceMesh
    AIEngine -- "3. Telemetry Updates" --> Socket
    Socket -- "4. Real-time Metrics & Alarms" --> Recruiter
    AIEngine -- "5. Logs Transactions" --> Postgres
    Recruiter -- "6. Finalizes session" --> API
    API --> PDFGen
    PDFGen --> Postgres
    PDFGen -- "7. Compiles PDF Certificate" --> Recruiter
```

---

## 📊 Database Design (ER Diagram)

The PostgreSQL database holds the following schemas and connections:

```mermaid
erDiagram
    USERS ||--o{ INTERVIEWS : conducts
    INTERVIEWS ||--o{ MONITORING_EVENTS : logs
    INTERVIEWS ||--o{ DEEPFAKE_PREDICTIONS : predicts
    INTERVIEWS ||--o{ EYE_GAZE_LOGS : tracks
    INTERVIEWS ||--o{ PHONE_DETECTION_LOGS : scans
    INTERVIEWS ||--o{ LIVENESS_LOGS : verifies
    INTERVIEWS ||--o{ REPORTS : compiles

    USERS {
        string id PK
        string email UK
        string hashed_password
        string full_name
        string company_name
        timestamp created_at
    }

    INTERVIEWS {
        string id PK
        string recruiter_id FK
        string candidate_name
        string candidate_email
        string meeting_id UK
        timestamp scheduled_at
        integer duration_minutes
        string status
        float integrity_score
        string risk_level
        timestamp created_at
    }

    MONITORING_EVENTS {
        string id PK
        string interview_id FK
        timestamp timestamp
        string event_type
        string severity
        string details
    }

    DEEPFAKE_PREDICTIONS {
        string id PK
        string interview_id FK
        timestamp timestamp
        float score
        string label
    }

    EYE_GAZE_LOGS {
        string id PK
        string interview_id FK
        timestamp timestamp
        float horizontal_gaze
        float vertical_gaze
        string gaze_direction
        boolean looking_away
        float attention_score
    }

    PHONE_DETECTION_LOGS {
        string id PK
        string interview_id FK
        timestamp timestamp
        boolean phone_detected
        float confidence
        integer count
    }

    LIVENESS_LOGS {
        string id PK
        string interview_id FK
        timestamp timestamp
        boolean is_live
        float blink_rate
        float head_movement_score
        float smile_score
    }

    REPORTS {
        string id PK
        string interview_id FK
        string pdf_path
        float integrity_score
        string risk_level
        timestamp generated_at
    }
```

---

## 🔄 Sequence Flow Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Candidate
    actor Recruiter
    participant Socket as Socket.IO Server
    participant AI as AI Engine
    participant DB as PostgreSQL DB

    Recruiter->>Socket: Join meeting room (role: recruiter)
    Candidate->>Socket: Join meeting room (role: candidate)
    Socket->>Recruiter: Alert: Candidate joined lobby

    Note over Candidate, Recruiter: WebRTC handshakes (signaled via Socket.IO)
    Recruiter->>Socket: Send RTC Offer
    Socket->>Candidate: Forward RTC Offer
    Candidate->>Socket: Send RTC Answer
    Socket->>Recruiter: Forward RTC Answer
    Note over Candidate, Recruiter: WebRTC P2P Call Connected

    loop Continuous AI Assessment (5 FPS)
        Candidate->>Socket: stream_frame (Base64 JPEG)
        Socket->>AI: Decode & run models (YOLOv8 + MediaPipe + PyTorch)
        AI->>DB: Log frame coordinates & alert incidents
        AI->>Socket: Broadcast real-time metrics payload
        Socket->>Recruiter: metrics_update (deepfake %, gaze, phone alerts, overlay box)
    end

    Recruiter->>Socket: Clicks "End Session"
    Socket->>AI: Trigger final report assembly
    AI->>DB: Query session logs & calculate final metrics
    AI->>DB: Generate Report PDF via ReportLab
    AI->>Recruiter: Complete report and display PDF download
```

---

## 🛠️ Installation & Quickstart

InterviewGuard AI can be deployed instantly using Docker Compose or built locally.

### Method 1: Docker Compose (Recommended)

One command spins up the Postgres Database, FastAPI application, and React Client:

```bash
docker-compose up --build
```

- **Frontend Client**: Access at [http://localhost:5173](http://localhost:5173)
- **FastAPI Core**: Access at [http://localhost:8000](http://localhost:8000)
- **Swagger Documentation**: Access at [http://localhost:8000/docs](http://localhost:8000/docs)

### Method 2: Manual Local Build

#### 1. Backend Setup
Make sure Python 3.12+ is installed:

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python app/main.py
```

*Note: On first startup, the server automatically downloads the COCO-pre-trained YOLOv8 weights (`yolov8n.pt`) and initializes local SQLite database tables if PostgreSQL credentials are left blank.*

#### 2. Frontend Setup
Make sure Node.js is installed:

```bash
cd frontend
npm install
npm run dev
```

---

## 🧠 Multimodal DL Model Pipelines

1. **Face Deepfake Classification (`training/`)**:
   - Model weights training scripts are structured under `training/dataset.py` and `training/train.py`.
   - Incorporates a PyTorch `DeepfakeClassifier` custom CNN backbone which can wrap pre-trained ResNet/EfficientNet models.
   - Evaluates frame inputs returning a decimal float percentage of spoof confidence.
2. **Device Detection (YOLOv8)**:
   - Uses `ultralytics` YOLOv8 nano detector.
   - Filters target detection for COCO class index 67 ("cell phone") with custom confidence thresholds (> 0.4).
3. **Blink, Gaze & Smile Liveness (MediaPipe)**:
   - Uses refined Iris landmarks to track eye aspect ratio (EAR) and gaze vectors (left/right/center).
   - Measures distance deltas for candidate smiles to confirm presence of dynamic expressions.
