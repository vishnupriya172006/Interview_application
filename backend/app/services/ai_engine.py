import os
import sys
import cv2
import numpy as np
from app.core.config import settings

# Ensure the project root is in Python path for training module imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class AIEngine:
    """
    Multimodal AI Processing Engine running:
    - PyTorch Deepfake Classifier
    - YOLOv8 Phone Detector
    - MediaPipe Gaze, Liveness (Smile/Blink/Head-pos) Estimation
    """
    def __init__(self):
        self.deepfake_detector = None
        self.yolo_model = None
        self.face_mesh = None

        # 1. Initialize Deepfake Detector lazily
        self._initialize_deepfake_detector()

        # 2. Initialize YOLOv8 Phone Detector lazily
        self._initialize_yolo()

        # 3. Initialize MediaPipe Face Mesh lazily
        self._initialize_mediapipe()

    def _initialize_deepfake_detector(self):
        try:
            from training.inference import DeepfakeDetector
            if os.path.exists(settings.DEEPFAKE_MODEL_PATH):
                self.deepfake_detector = DeepfakeDetector(settings.DEEPFAKE_MODEL_PATH)
                print("[AI ENGINE] ✓ Deepfake Detector initialized successfully.")
            else:
                print(f"[AI ENGINE] WARNING: Deepfake model file not found at {settings.DEEPFAKE_MODEL_PATH}")
                print("[AI ENGINE]   Initializing with random weights. Train a model and place it at the specified path.")
                self.deepfake_detector = DeepfakeDetector(settings.DEEPFAKE_MODEL_PATH)
        except ImportError as e:
            print(f"[AI ENGINE] WARNING: Could not import DeepfakeDetector: {e}")
            self.deepfake_detector = None
        except Exception as e:
            print(f"[AI ENGINE] ERROR: Failed to initialize Deepfake Detector: {e}")
            self.deepfake_detector = None

    def _initialize_yolo(self):
        try:
            from ultralytics import YOLO
            self.yolo_model = YOLO(settings.YOLO_MODEL_PATH)
            print("[AI ENGINE] ✓ YOLOv8 Phone Detector initialized successfully.")
        except ImportError:
            print("[AI ENGINE] WARNING: YOLO library not installed. Phone detection will be disabled.")
            self.yolo_model = None
        except Exception as e:
            print(f"[AI ENGINE] ERROR: Failed to initialize YOLOv8: {e}")
            self.yolo_model = None

    def _initialize_mediapipe(self):
        try:
            import mediapipe as mp
            from mediapipe.tasks.python import vision

            print("[AI ENGINE] ✓ MediaPipe detected")
            self.face_mesh = None

            # FaceLandmarker model file is not bundled in this repo. Use local model if available.
            model_path = os.path.join(os.getcwd(), "models", "face_landmarker.task")
            if os.path.exists(model_path):
                self.face_mesh = vision.FaceLandmarker.create(
                    model_path=model_path,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
                print("[AI ENGINE] ✓ MediaPipe Face Landmarker initialized successfully.")
            else:
                print("[AI ENGINE] WARNING: MediaPipe face_landmarker.task model file not found.")
                print("[AI ENGINE]   Place it at models/face_landmarker.task to enable gaze/liveness detection.")
                self.face_mesh = None
        except ImportError:
            print("[AI ENGINE] WARNING: MediaPipe not installed. Gaze and liveness detection will be disabled.")
            self.face_mesh = None
        except Exception as e:
            print(f"[AI ENGINE] ERROR: Failed to initialize MediaPipe Face Mesh: {e}")
            self.face_mesh = None

    def process_frame(self, frame_bgr, interview_id=None, db_session=None):
        """
        Processes a single frame and returns integrity metrics.
        Saves logs to database if interview_id and db_session are provided.
        Returns a dict of metrics.
        """
        # Default results
        metrics = {
            "deepfake_score": 0.0,
            "liveness_status": True,
            "gaze_direction": "center",
            "looking_away": False,
            "phone_detected": False,
            "phone_count": 0,
            "integrity_score": 100.0,
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
                
                if len(phone_boxes) > 0:
                    metrics["phone_detected"] = True
                    metrics["phone_count"] = len(phone_boxes)
                    # Use first phone bounding box for display
                    metrics["bbox"] = [int(x) for x in phone_boxes[0]]
            except Exception as e:
                print(f"YOLO Processing error: {e}")

        # 2. Run PyTorch Deepfake detection
        deepfake_score = 0.0
        face_bbox = None
        if self.deepfake_detector is not None:
            try:
                deepfake_score, bbox = self.deepfake_detector.detect_face_and_predict(frame_bgr)
                metrics["deepfake_score"] = float(deepfake_score)
                if bbox:
                    face_bbox = bbox
                    if not metrics["bbox"]:  # Prefer phone bounding box, fallback to face
                        metrics["bbox"] = face_bbox
            except Exception as e:
                print(f"Deepfake Classifier error: {e}")

        # 3. Run MediaPipe Face Mesh / Gaze / Liveness
        blink_rate = 0.0
        head_movement = 0.0
        smile_score = 0.0
        is_live = True
        
        if self.face_mesh is not None:
            try:
                # Convert BGR to RGB
                rgb_frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                h, w, _ = frame_bgr.shape
                results = self.face_mesh.process(rgb_frame)
                
                if results.multi_face_landmarks:
                    face_landmarks = results.multi_face_landmarks[0].landmark
                    
                    # Blink Detection - Eye Aspect Ratio (EAR)
                    # Left Eye: top=159, bottom=145, left_corner=33, right_corner=133
                    p159 = np.array([face_landmarks[159].x * w, face_landmarks[159].y * h])
                    p145 = np.array([face_landmarks[145].x * w, face_landmarks[145].y * h])
                    p33 = np.array([face_landmarks[33].x * w, face_landmarks[33].y * h])
                    p133 = np.array([face_landmarks[133].x * w, face_landmarks[133].y * h])
                    
                    left_ear = np.linalg.norm(p159 - p145) / max(np.linalg.norm(p33 - p133), 1e-6)
                    blink_rate = float(left_ear)
                    
                    if left_ear < 0.15:
                        # Eye is closed (possible blink)
                        pass
                        
                    # Smile Detection - Mouth Corner Distance / Ratio
                    # Corners: 61, 291. Upper lip: 13, Lower lip: 14
                    p61 = np.array([face_landmarks[61].x * w, face_landmarks[61].y * h])
                    p291 = np.array([face_landmarks[291].x * w, face_landmarks[291].y * h])
                    p13 = np.array([face_landmarks[13].x * w, face_landmarks[13].y * h])
                    p14 = np.array([face_landmarks[14].x * w, face_landmarks[14].y * h])
                    
                    mouth_width = np.linalg.norm(p61 - p291)
                    mouth_height = np.linalg.norm(p13 - p14)
                    
                    # Normalize by face width (e.g., distance between outer eye corners 130 and 359)
                    p130 = np.array([face_landmarks[130].x * w, face_landmarks[130].y * h])
                    p359 = np.array([face_landmarks[359].x * w, face_landmarks[359].y * h])
                    face_width = np.linalg.norm(p130 - p359)
                    
                    smile_score = float(mouth_width / max(face_width, 1e-6))
                    
                    # Head Movement / Pose (Roll/Yaw/Pitch heuristics)
                    # Nose tip: 1, Chin: 152, Left eye: 33, Right eye: 263
                    pnose = np.array([face_landmarks[1].x, face_landmarks[1].y])
                    pchin = np.array([face_landmarks[152].x, face_landmarks[152].y])
                    head_vector = pnose - pchin
                    head_movement = float(np.linalg.norm(head_vector))
                    
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
                            
                    # Challenge response: if blink rate is extremely stable (like zero or flatlined), is_live could be False
                    if left_ear > 0.5: # Out of bound EAR
                        is_live = False
                        
                    metrics["liveness_status"] = is_live
            except Exception as e:
                print(f"MediaPipe Face Mesh error: {e}")
                
        # Calculate instantaneous integrity score
        penalty = 0.0
        if metrics["phone_detected"]:
            penalty += 30.0
        if metrics["looking_away"]:
            penalty += 15.0
        if deepfake_score > 0.4:
            penalty += (deepfake_score * 50)
        if not metrics["liveness_status"]:
            penalty += 20.0
            
        metrics["integrity_score"] = max(0.0, 100.0 - penalty)

        # 4. Save to PostgreSQL if DB Session is active
        if interview_id and db_session:
            try:
                from app.models.logs import (
                    DeepfakePrediction, EyeGazeLog, PhoneDetectionLog, LivenessLog, MonitoringEvent
                )
                
                # Save Deepfake Log
                df_log = DeepfakePrediction(
                    interview_id=interview_id,
                    score=metrics["deepfake_score"],
                    label="fake" if metrics["deepfake_score"] > 0.4 else "real"
                )
                db_session.add(df_log)
                
                # Save Eye Gaze Log
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
                p_log = PhoneDetectionLog(
                    interview_id=interview_id,
                    phone_detected=metrics["phone_detected"],
                    confidence=phone_conf,
                    count=metrics["phone_count"]
                )
                db_session.add(p_log)
                
                # Save Liveness Log
                l_log = LivenessLog(
                    interview_id=interview_id,
                    is_live=metrics["liveness_status"],
                    blink_rate=blink_rate,
                    head_movement_score=head_movement,
                    smile_score=smile_score
                )
                db_session.add(l_log)
                
                # Generate high-severity events if needed
                if metrics["phone_detected"]:
                    evt = MonitoringEvent(
                        interview_id=interview_id,
                        event_type="phone_detected",
                        severity="high",
                        details="A mobile phone was detected in candidate view."
                    )
                    db_session.add(evt)
                    
                if metrics["deepfake_score"] > 0.6:
                    evt = MonitoringEvent(
                        interview_id=interview_id,
                        event_type="deepfake_detected",
                        severity="high",
                        details=f"High-probability deepfake detected (Score: {metrics['deepfake_score']:.2f})."
                    )
                    db_session.add(evt)
                    
                if metrics["looking_away"]:
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
