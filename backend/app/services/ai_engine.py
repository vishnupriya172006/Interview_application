import os
import sys
import cv2
import numpy as np
from app.core.config import settings

# Ensure the project root is in Python path for training module imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load deepfake detector helper from training pipeline
DeepfakeDetector = None
try:
    from training.inference import DeepfakeDetector
    print("[MODELS] DeepfakeDetector imported successfully from training.inference")
except ImportError as e:
    print(f"[MODELS] WARNING: Could not import DeepfakeDetector from training.inference: {e}")
    # Attempt alternative import path
    try:
        from inference import DeepfakeDetector
        print("[MODELS] DeepfakeDetector imported from direct inference module")
    except ImportError as e2:
        print(f"[MODELS] WARNING: Could not import DeepfakeDetector from any source: {e2}")
        DeepfakeDetector = None

# Import MediaPipe & YOLO with better error handling
mp_face_mesh = None
mediapipe_available = False

try:
    import mediapipe as mp
    mp_face_mesh = mp.solutions.face_mesh.FaceMesh
    mediapipe_available = True

except ImportError as e1:
    print("[AI ENGINE] WARN: MediaPipe not installed or import failed")
    print(f"[AI ENGINE]   Install with: pip install mediapipe>=0.10.11")
    mp_face_mesh = None
    mediapipe_available = False

YOLO = None
try:
    from ultralytics import YOLO
    print("[MODELS] OK: YOLO (ultralytics) imported successfully")
except ImportError as e:
    print("[MODELS] WARN: YOLO library not installed; phone detection is unavailable")


class AIEngine:
    """
    Multimodal AI Processing Engine running:
    - PyTorch Deepfake Classifier
    - YOLOv8 Phone Detector
    - MediaPipe Gaze, Liveness (Smile/Blink/Head-pos) Estimation
    """
    def __init__(self):
        # 1. Initialize Deepfake Detector
        if DeepfakeDetector is not None:
            try:
                if os.path.exists(settings.DEEPFAKE_MODEL_PATH):
                    self.deepfake_detector = DeepfakeDetector(settings.DEEPFAKE_MODEL_PATH)
                    print("[AI ENGINE] OK: Deepfake Detector initialized successfully.")
                else:
                    print(f"[AI ENGINE] WARNING: Deepfake model file not found at {settings.DEEPFAKE_MODEL_PATH}")
                    self.deepfake_detector = None
            except Exception as e:
                print(f"[AI ENGINE] ERROR: Failed to initialize Deepfake Detector: {e}")
                self.deepfake_detector = None
        else:
            print("[AI ENGINE] WARNING: Deepfake Detector class not available. Deepfake detection will be disabled.")
            self.deepfake_detector = None

        # 2. Initialize YOLOv8 (Loads yolov8n.pt nano model)
        if YOLO is not None:
            try:
                if not os.path.isfile(settings.YOLO_MODEL_PATH):
                    raise FileNotFoundError("Configured YOLO weights are not present")
                self.yolo_model = YOLO(settings.YOLO_MODEL_PATH)
                print("[AI ENGINE] OK: YOLOv8 Phone Detector initialized successfully.")
            except Exception as e:
                print(f"[AI ENGINE] ERROR: Failed to initialize YOLOv8: {e}")
                self.yolo_model = None
        else:
            print("[AI ENGINE] WARNING: YOLOv8 library not available. Phone detection will be disabled.")
            self.yolo_model = None

        # 3. Initialize MediaPipe Face Mesh for eye/iris tracking
        if mediapipe_available and mp_face_mesh is not None:
            try:
                self.face_mesh = mp_face_mesh(
                    max_num_faces=1,
                    refine_landmarks=True,  # Enables iris detection (468-477)
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
                print("[AI ENGINE] OK: MediaPipe Face Mesh initialized successfully.")
            except Exception as e:
                print(f"[AI ENGINE] ERROR: Failed to initialize MediaPipe Face Mesh: {e}")
                import traceback
                traceback.print_exc()
                self.face_mesh = None
        else:
            if not mediapipe_available:
                print("[AI ENGINE] WARNING: MediaPipe library not available. Gaze and liveness detection will be disabled.")
            else:
                print("[AI ENGINE] WARNING: MediaPipe Face Mesh module not accessible. Gaze and liveness detection will be disabled.")
            self.face_mesh = None

    def process_frame(self, frame_bgr, interview_id=None, db_session=None):
        """
        Processes a single frame and returns integrity metrics.
        Saves logs to database if interview_id and db_session are provided.
        Returns a dict of metrics.
        """
        # Default results
        metrics = {
            "deepfake_score": None,
            "deepfake_status": "unavailable" if self.deepfake_detector is None else "pending",
            "liveness_status": None,
            "liveness_analysis_status": "unavailable",
            "gaze_direction": None,
            "gaze_analysis_status": "unavailable" if self.face_mesh is None else "pending",
            "looking_away": None,
            "phone_detected": None,
            "phone_analysis_status": "unavailable" if self.yolo_model is None else "pending",
            "phone_count": 0,
            "integrity_score": None,
            "bbox": None
        }

        # 1. Run YOLOv8 Phone Detection
        phone_conf = 0.0
        if self.yolo_model is not None:
            try:
                # Class 67 in COCO is "cell phone"
                results = self.yolo_model(frame_bgr, verbose=False)[0]
                phone_boxes = []
                for box in results.boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    if cls_id == 67 and conf > 0.4: # Cell phone class
                        xyxy = box.xyxy[0].tolist()
                        phone_boxes.append(xyxy)
                        phone_conf = max(phone_conf, conf)
                metrics["phone_detected"] = bool(phone_boxes)
                
                if len(phone_boxes) > 0:
                    metrics["phone_detected"] = True
                    metrics["phone_count"] = len(phone_boxes)
                    # Use first phone bounding box for display
                    metrics["bbox"] = [int(x) for x in phone_boxes[0]]
                metrics["phone_analysis_status"] = "analyzed"
            except Exception as e:
                metrics["phone_analysis_status"] = "failed"
                print(f"YOLO Processing error: {e}")

        # 2. Run PyTorch Deepfake detection
        deepfake_score = 0.0
        face_bbox = None
        if self.deepfake_detector is not None:
            try:
                deepfake_score, bbox = self.deepfake_detector.detect_face_and_predict(frame_bgr)
                if bbox is None:
                    # The detector returns zero when it cannot locate a face;
                    # that is missing evidence, not a real-face prediction.
                    metrics["deepfake_status"] = "uncertain"
                else:
                    metrics["deepfake_score"] = float(deepfake_score)
                    metrics["deepfake_status"] = "analyzed"
                    face_bbox = bbox
                    if not metrics["bbox"]:  # Prefer phone bounding box, fallback to face
                        metrics["bbox"] = face_bbox
            except Exception as e:
                metrics["deepfake_status"] = "failed"
                print(f"Deepfake Classifier error: {e}")

        # 3. Run MediaPipe Face Mesh / Gaze / Liveness
        if self.face_mesh is not None:
            try:
                # Convert BGR to RGB
                rgb_frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                h, w, _ = frame_bgr.shape
                results = self.face_mesh.process(rgb_frame)
                
                if results.multi_face_landmarks:
                    face_landmarks = results.multi_face_landmarks[0].landmark
                    
                    # Eye corners and iris are used only for a gaze observation.
                    p33 = np.array([face_landmarks[33].x * w, face_landmarks[33].y * h])
                    p133 = np.array([face_landmarks[133].x * w, face_landmarks[133].y * h])
                    
                    # Gaze Direction (Iris Tracking)
                    # Left Iris center landmark is 468, Left Eye corners: 33, 133
                    if len(face_landmarks) > 468:
                        p468 = np.array([face_landmarks[468].x * w, face_landmarks[468].y * h])
                        # Calculate relative horizontal position of iris center within eye corners
                        left_dist = np.linalg.norm(p468 - p33)
                        right_dist = np.linalg.norm(p468 - p133)
                        eye_width = max(np.linalg.norm(p33 - p133), 1e-6)
                        
                        ratio = left_dist / eye_width
                        
                        # Gaze classification
                        if ratio < 0.38:
                            metrics["gaze_direction"] = "left"
                            metrics["looking_away"] = True
                        elif ratio > 0.62:
                            metrics["gaze_direction"] = "right"
                            metrics["looking_away"] = True
                        else:
                            metrics["gaze_direction"] = "center"
                            metrics["looking_away"] = False
                            
                    if len(face_landmarks) > 468:
                        metrics["gaze_analysis_status"] = "analyzed"
                    else:
                        metrics["gaze_analysis_status"] = "uncertain"
                else:
                    metrics["gaze_analysis_status"] = "uncertain"
            except Exception as e:
                metrics["gaze_analysis_status"] = "failed"
                print(f"MediaPipe Face Mesh error: {e}")
                
        # 4. Save to PostgreSQL if DB Session is active
        if interview_id and db_session:
            try:
                from app.models.logs import (
                    DeepfakePrediction, EyeGazeLog, PhoneDetectionLog, MonitoringEvent
                )
                
                # Save Deepfake Log
                if metrics["deepfake_status"] == "analyzed":
                    df_log = DeepfakePrediction(
                    interview_id=interview_id,
                    score=metrics["deepfake_score"],
                    label="fake" if metrics["deepfake_score"] > 0.4 else "real")
                    db_session.add(df_log)
                
                # Save Eye Gaze Log
                if metrics["gaze_analysis_status"] == "analyzed":
                    g_log = EyeGazeLog(
                    interview_id=interview_id,
                    horizontal_gaze=0.0,
                    vertical_gaze=0.0,
                    gaze_direction=metrics["gaze_direction"],
                    looking_away=metrics["looking_away"],
                    attention_score=1.0 - (0.5 if metrics["looking_away"] else 0.0)
                )
                    db_session.add(g_log)
                
                # Save Phone Detection Log
                if metrics["phone_analysis_status"] == "analyzed":
                    p_log = PhoneDetectionLog(
                    interview_id=interview_id,
                    phone_detected=metrics["phone_detected"],
                    confidence=phone_conf,
                    count=metrics["phone_count"]
                )
                    db_session.add(p_log)
                
                # Generate high-severity events if needed
                if metrics["phone_detected"] is True:
                    evt = MonitoringEvent(
                        interview_id=interview_id,
                        event_type="phone_detected",
                        severity="high",
                        details="The object detector flagged a cell phone in a sampled camera frame."
                    )
                    db_session.add(evt)
                    
                if metrics["deepfake_score"] is not None and metrics["deepfake_score"] > 0.6:
                    evt = MonitoringEvent(
                        interview_id=interview_id,
                        event_type="deepfake_detected",
                        severity="high",
                        details=f"Elevated uncalibrated deepfake model output in a sampled frame (score: {metrics['deepfake_score']:.2f})."
                    )
                    db_session.add(evt)
                    
                if metrics["looking_away"] is True:
                    evt = MonitoringEvent(
                        interview_id=interview_id,
                        event_type="gaze_deviation",
                        severity="medium",
                        details="Candidate is looking away from the camera feed."
                    )
                    db_session.add(evt)
                    
                db_session.commit()
            except Exception as e:
                db_session.rollback()
                print(f"Database logging error: {e}")

        return metrics
