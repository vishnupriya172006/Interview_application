import base64
import cv2
import numpy as np
import socketio
from app.core.database import SessionLocal
from app.models.interview import Interview
from app.models.user import User
from app.core.security import decode_access_token
from app.core.config import settings

# Initialize Socket.IO Async Server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=settings.FRONTEND_URLS + ['http://localhost:3000'],
)

# AI Engine will be initialized during application startup to avoid heavy imports during module import
ai_engine = None
room_participants = {}
sid_rooms = {}
sid_identities = {}

def initialize_ai_engine():
    global ai_engine
    if ai_engine is None:
        from app.services.ai_engine import AIEngine
        ai_engine = AIEngine()
    return ai_engine

def decode_base64_frame(base64_str: str):
    """
    Decodes base64 string image data into an OpenCV BGR frame.
    """
    try:
        if "," in base64_str:
            base64_str = base64_str.split(",")[1]
        img_data = base64.b64decode(base64_str, validate=True)
        nparr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return frame
    except Exception as e:
        print("Error decoding a camera frame.")
        return None


@sio.event
async def connect(sid, environ, auth=None):
    auth = auth or {}
    token = auth.get("token")
    subject = decode_access_token(token) if token else None
    identity = None
    if subject:
        db = SessionLocal()
        try:
            identity = db.query(User).filter(User.id == subject).first()
            if identity is None:
                identity = db.query(User).filter(User.email == subject).first()
        finally:
            db.close()
    sid_identities[sid] = identity.id if identity else None
    print(f"Client connected: {sid}")


@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")
    for room, participants in list(room_participants.items()):
        if sid in participants:
            participants.pop(sid)
            sid_rooms.pop(sid, None)
            await sio.emit("user_left", {"sid": sid}, room=room)
        if not participants:
            room_participants.pop(room, None)
    sid_identities.pop(sid, None)


def _authorized_room(sid, room, required_role=None):
    if not room or sid_rooms.get(sid) != room:
        return False
    participant = room_participants.get(room, {}).get(sid)
    return participant is not None and (required_role is None or participant == required_role)


def _interview_accepts_connections(room):
    """Reject new socket activity once an interview is completed or cancelled."""
    db = SessionLocal()
    try:
        interview = db.query(Interview).filter(Interview.meeting_id == room).first()
        return interview is not None and interview.status not in ("completed", "cancelled")
    finally:
        db.close()


@sio.event
async def join_room(sid, data):
    """
    Triggered when candidate or recruiter joins a meeting room.
    data: {"room": "123-456-789", "role": "candidate"|"recruiter"}
    """
    if not isinstance(data, dict):
        return
    room = data.get("room")
    role = data.get("role", "candidate")
    if not isinstance(room, str) or len(room) > 255 or role not in ("candidate", "recruiter"):
        return

    db = SessionLocal()
    try:
        interview = db.query(Interview).filter(Interview.meeting_id == room).first()
        if interview is None or interview.status in ("completed", "cancelled"):
            return
        authenticated_user_id = sid_identities.get(sid)
        if role == "recruiter" and interview.recruiter_id != authenticated_user_id:
            return
        if role == "candidate" and authenticated_user_id:
            return
    finally:
        db.close()

    old_room = sid_rooms.get(sid)
    if old_room and old_room != room:
        await leave_room(sid, {"room": old_room})

    participants = room_participants.setdefault(room, {})
    if sid in participants:
        return
    if any(existing_role == role for existing_role in participants.values()):
        return
    await sio.enter_room(sid, room)
    print(f"Client {sid} ({role}) joined an interview room.")

    if participants:
        await sio.emit(
            "room_peers",
            [{"sid": peer_sid, "role": peer_role} for peer_sid, peer_role in participants.items()],
            to=sid,
        )
    participants[sid] = role
    sid_rooms[sid] = room

    # Notify other peers in room
    await sio.emit("user_joined", {"sid": sid, "role": role}, room=room, skip_sid=sid)


@sio.event
async def leave_room(sid, data):
    if not isinstance(data, dict):
        return
    room = data.get("room")
    if not _authorized_room(sid, room):
        return
    await sio.leave_room(sid, room)
    participants = room_participants.get(room, {})
    participants.pop(sid, None)
    sid_rooms.pop(sid, None)
    if not participants:
        room_participants.pop(room, None)
    print(f"Client {sid} left an interview room.")
    await sio.emit("user_left", {"sid": sid}, room=room)


# ==========================================
# WebRTC Signaling Handlers
# ==========================================

@sio.event
async def rtc_offer(sid, data):
    """
    Forwards WebRTC Offer to the remote peer.
    data: {"room": "...", "sdp": ...}
    """
    if not isinstance(data, dict):
        return
    room = data.get("room")
    sdp = data.get("sdp")
    if not isinstance(sdp, dict) or sdp.get("type") != "offer" or not isinstance(sdp.get("sdp"), str) or len(sdp["sdp"]) > 100_000:
        return
    if not _authorized_room(sid, room, required_role="recruiter") or not _interview_accepts_connections(room):
        return
    await sio.emit("rtc_offer", {"sdp": data.get("sdp"), "sender": sid}, room=room, skip_sid=sid)


@sio.event
async def rtc_answer(sid, data):
    """
    Forwards WebRTC Answer to the remote peer.
    data: {"room": "...", "sdp": ...}
    """
    if not isinstance(data, dict):
        return
    room = data.get("room")
    sdp = data.get("sdp")
    if not isinstance(sdp, dict) or sdp.get("type") != "answer" or not isinstance(sdp.get("sdp"), str) or len(sdp["sdp"]) > 100_000:
        return
    if not _authorized_room(sid, room, required_role="candidate") or not _interview_accepts_connections(room):
        return
    await sio.emit("rtc_answer", {"sdp": data.get("sdp"), "sender": sid}, room=room, skip_sid=sid)


@sio.event
async def rtc_ice_candidate(sid, data):
    """
    Forwards WebRTC ICE Candidates.
    data: {"room": "...", "candidate": ...}
    """
    if not isinstance(data, dict):
        return
    room = data.get("room")
    candidate = data.get("candidate")
    if not isinstance(candidate, dict) or not isinstance(candidate.get("candidate"), str) or len(candidate["candidate"]) > 2048:
        return
    if not _authorized_room(sid, room) or not _interview_accepts_connections(room):
        return
    await sio.emit("rtc_ice_candidate", {"candidate": data.get("candidate"), "sender": sid}, room=room, skip_sid=sid)


@sio.event
async def rtc_ice_restart(sid, data):
    if not isinstance(data, dict):
        return
    room = data.get("room")
    if not _authorized_room(sid, room) or not _interview_accepts_connections(room):
        return
    participant_role = room_participants[room][sid]
    if participant_role != "candidate":
        return
    await sio.emit("rtc_ice_restart", {"sender": sid}, room=room, skip_sid=sid)


# ==========================================
# Real-Time AI Stream Processing
# ==========================================

@sio.event
async def stream_frame(sid, data):
    """
    Triggered periodically by the candidate web browser with camera frames.
    data: {"room": "123-456-789", "frame": "base64_str_here"}
    """
    if not isinstance(data, dict):
        return
    room = data.get("room")
    frame_b64 = data.get("frame")
    
    if not _authorized_room(sid, room, required_role="candidate") or not isinstance(frame_b64, str) or len(frame_b64) > 2_000_000:
        return
        
    # 1. Decode base64 to numpy CV image
    frame = decode_base64_frame(frame_b64)
    if frame is None:
        return
        
    # 2. Extract database session
    db = SessionLocal()
    try:
        # Find active interview
        interview = db.query(Interview).filter(
            Interview.meeting_id == room,
            Interview.status.notin_(("completed", "cancelled")),
        ).first()
        if not interview:
            return
            
        # 3. Process frame with AI Engine and save metrics inside DB
        results = initialize_ai_engine().process_frame(
            frame, interview_id=interview.id, db_session=db
        )
        
        # 4. Push results back to recruiter/room in real-time
        await sio.emit("metrics_update", results, room=room)
        
    except Exception as e:
        print("Error processing a camera frame.")
    finally:
        db.close()
