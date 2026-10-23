from types import SimpleNamespace
from contextlib import nullcontext
import importlib.util
from pathlib import Path
import sys
from unittest.mock import patch

import numpy as np

from app.core.config import settings
from app.models.interview import Interview
from app.models.report import Report
from app.services.ai_engine import AIEngine
from app.services.pdf_generator import calculate_integrity


def test_missing_evidence_has_no_score_and_requires_review():
    score, risk, _ = calculate_integrity([], [], [], [])

    assert score is None
    assert risk == "Review Required"


def test_a_measured_zero_is_distinct_from_an_unavailable_score():
    deepfake = [SimpleNamespace(score=1.0)]
    gaze = [SimpleNamespace(looking_away=True)]
    phone = [SimpleNamespace(phone_detected=True)]
    liveness = [SimpleNamespace(is_live=False)]

    score, risk, _ = calculate_integrity(deepfake, gaze, phone, liveness)

    assert score == 0.0
    assert risk == "High Risk"


def test_ai_engine_reports_missing_models_and_liveness_as_unavailable():
    engine = AIEngine.__new__(AIEngine)
    engine.deepfake_detector = None
    engine.yolo_model = None
    engine.face_mesh = None

    result = engine.process_frame(np.zeros((32, 32, 3), dtype=np.uint8))

    assert result["integrity_score"] is None
    assert result["deepfake_status"] == "unavailable"
    assert result["phone_analysis_status"] == "unavailable"
    assert result["gaze_analysis_status"] == "unavailable"
    assert result["liveness_status"] is None
    assert result["liveness_analysis_status"] == "unavailable"


def test_successful_object_detection_reports_no_phone_only_for_that_sample():
    class EmptyYolo:
        def __call__(self, *_args, **_kwargs):
            return [SimpleNamespace(boxes=[])]

    engine = AIEngine.__new__(AIEngine)
    engine.deepfake_detector = None
    engine.yolo_model = EmptyYolo()
    engine.face_mesh = None

    result = engine.process_frame(np.zeros((32, 32, 3), dtype=np.uint8))

    assert result["phone_analysis_status"] == "analyzed"
    assert result["phone_detected"] is False
    assert result["integrity_score"] is None


def test_failed_model_inference_is_reported_as_failed():
    class FailingYolo:
        def __call__(self, *_args, **_kwargs):
            raise RuntimeError("model failure")

    class FailingDeepfake:
        def detect_face_and_predict(self, _frame):
            raise RuntimeError("model failure")

    class FailingFaceMesh:
        def process(self, _frame):
            raise RuntimeError("model failure")

    engine = AIEngine.__new__(AIEngine)
    engine.deepfake_detector = FailingDeepfake()
    engine.yolo_model = FailingYolo()
    engine.face_mesh = FailingFaceMesh()

    result = engine.process_frame(np.zeros((32, 32, 3), dtype=np.uint8))

    assert result["integrity_score"] is None
    assert result["deepfake_status"] == "failed"
    assert result["phone_analysis_status"] == "failed"
    assert result["gaze_analysis_status"] == "failed"
    assert result["liveness_analysis_status"] == "unavailable"


def test_face_mesh_gaze_does_not_claim_liveness():
    landmarks = [SimpleNamespace(x=0.5, y=0.5) for _ in range(469)]
    landmarks[33] = SimpleNamespace(x=0.4, y=0.5)
    landmarks[133] = SimpleNamespace(x=0.6, y=0.5)
    landmarks[468] = SimpleNamespace(x=0.5, y=0.5)

    class FaceMesh:
        def process(self, _frame):
            return SimpleNamespace(multi_face_landmarks=[SimpleNamespace(landmark=landmarks)])

    engine = AIEngine.__new__(AIEngine)
    engine.deepfake_detector = None
    engine.yolo_model = None
    engine.face_mesh = FaceMesh()

    result = engine.process_frame(np.zeros((32, 32, 3), dtype=np.uint8))

    assert result["gaze_analysis_status"] == "analyzed"
    assert result["gaze_direction"] == "center"
    assert result["liveness_status"] is None
    assert result["liveness_analysis_status"] == "unavailable"


def test_deepfake_predict_uses_initialized_torch_reference():
    class Tensor:
        def unsqueeze(self, _dimension):
            return self

        def to(self, _device):
            return self

    class Score:
        def item(self):
            return 0.75

    class Probabilities:
        def __getitem__(self, index):
            assert index == (0, 1)
            return Score()

    fake_transforms = SimpleNamespace(
        Compose=lambda _items: lambda _image: Tensor(),
        Resize=lambda *_args, **_kwargs: object(),
        ToTensor=lambda: object(),
        Normalize=lambda *_args, **_kwargs: object(),
    )
    fake_torchvision = SimpleNamespace(transforms=fake_transforms)
    inference_path = Path(__file__).resolve().parents[2] / "training" / "inference.py"
    spec = importlib.util.spec_from_file_location("test_training_inference", inference_path)
    inference = importlib.util.module_from_spec(spec)

    with patch.dict(sys.modules, {"torchvision": fake_torchvision}):
        spec.loader.exec_module(inference)

    detector = inference.DeepfakeDetector.__new__(inference.DeepfakeDetector)
    detector.torch = SimpleNamespace(
        no_grad=nullcontext,
        softmax=lambda _output, dim: Probabilities() if dim == 1 else None,
    )
    detector.device = "cpu"
    detector.transform = lambda _image: Tensor()
    detector.model = lambda _tensor: object()

    assert detector.predict_face(np.zeros((8, 8, 3), dtype=np.uint8)) == 0.75


def test_report_api_distinguishes_unavailable_from_measured_zero(client, db_session):
    client.post(f"{settings.API_V1_STR}/auth/register", json={
        "email": "scores@company.com",
        "password": "secure_password123",
        "full_name": "Score Reviewer",
    })
    token = client.post(f"{settings.API_V1_STR}/auth/login", json={
        "email": "scores@company.com",
        "password": "secure_password123",
    }).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    scheduled = client.post(
        f"{settings.API_V1_STR}/interviews/schedule",
        json={
            "candidate_name": "Jane Candidate",
            "candidate_email": "jane@example.com",
            "scheduled_at": "2026-07-10T14:30:00Z",
        },
        headers=headers,
    )
    interview = db_session.query(Interview).filter_by(meeting_id=scheduled.json()["meeting_id"]).one()
    interview.integrity_score = None
    interview.risk_level = "review_required"
    report = Report(
        interview_id=interview.id,
        pdf_path="unavailable.pdf",
        integrity_score=None,
        risk_level="review_required",
    )
    db_session.add(report)
    db_session.commit()

    unavailable = client.get(f"{settings.API_V1_STR}/reports/{report.id}", headers=headers).json()
    assert unavailable["report"]["integrity_score"] is None
    assert unavailable["report"]["risk_level"] == "review_required"
    assert unavailable["interview"]["integrity_score"] is None
    assert unavailable["interview"]["risk_level"] == "review_required"

    client.post(f"{settings.API_V1_STR}/auth/register", json={
        "email": "other-scores@company.com",
        "password": "secure_password123",
        "full_name": "Other Reviewer",
    })
    other_token = client.post(f"{settings.API_V1_STR}/auth/login", json={
        "email": "other-scores@company.com",
        "password": "secure_password123",
    }).json()["access_token"]
    forbidden_detail = client.get(
        f"{settings.API_V1_STR}/reports/{report.id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert forbidden_detail.status_code == 404

    interview.integrity_score = 0.0
    interview.risk_level = "high"
    report.integrity_score = 0.0
    report.risk_level = "high"
    db_session.commit()

    measured_zero = client.get(f"{settings.API_V1_STR}/reports/{report.id}", headers=headers).json()
    assert measured_zero["report"]["integrity_score"] == 0.0
    assert measured_zero["report"]["risk_level"] == "high"
    assert measured_zero["interview"]["integrity_score"] == 0.0
    assert measured_zero["interview"]["risk_level"] == "high"
