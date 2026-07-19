import base64
import cv2
import numpy as np
import socketio
from app.core.database import SessionLocal
from app.models.interview import Interview

# Initialize Socket.IO Async Server
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')

# AI Engine will be initialized during application startup to avoid heavy imports during module import
ai_engine = None

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
        img_data = base64.b64decode(base64_str)
        nparr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return frame
    except Exception as e:
        print(f"Error decoding base64 frame: {e}")
        return None


@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")


@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")


@sio.event
async def join_room(sid, data):
    """
    Triggered when candidate or recruiter joins a meeting room.
    data: {"room": "123-456-789", "role": "candidate"|"recruiter"}
    """
    room = data.get("room")
    role = data.get("role", "candidate")
    
    await sio.enter_room(sid, room)
    print(f"Client {sid} ({role}) joined room {room}")
    
    # Notify other peers in room
    await sio.emit("user_joined", {"sid": sid, "role": role}, room=room, skip_sid=sid)


@sio.event
async def leave_room(sid, data):
    room = data.get("room")
    await sio.leave_room(sid, room)
    print(f"Client {sid} left room {room}")
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
    room = data.get("room")
    await sio.emit("rtc_offer", {"sdp": data.get("sdp"), "sender": sid}, room=room, skip_sid=sid)


@sio.event
async def rtc_answer(sid, data):
    """
    Forwards WebRTC Answer to the remote peer.
    data: {"room": "...", "sdp": ...}
    """
    room = data.get("room")
    await sio.emit("rtc_answer", {"sdp": data.get("sdp"), "sender": sid}, room=room, skip_sid=sid)


@sio.event
async def rtc_ice_candidate(sid, data):
    """
    Forwards WebRTC ICE Candidates.
    data: {"room": "...", "candidate": ...}
    """
    room = data.get("room")
    await sio.emit("rtc_ice_candidate", {"candidate": data.get("candidate"), "sender": sid}, room=room, skip_sid=sid)


# ==========================================
# Real-Time AI Stream Processing
# ==========================================

@sio.event
async def stream_frame(sid, data):
    """
    Triggered periodically by the candidate web browser with camera frames.
    data: {"room": "123-456-789", "frame": "base64_str_here"}
    """
    room = data.get("room")
    frame_b64 = data.get("frame")
    
    if not room or not frame_b64:
        return
        
    # 1. Decode base64 to numpy CV image
    frame = decode_base64_frame(frame_b64)
    if frame is None:
        return
        
    # 2. Extract database session
    db = SessionLocal()
    try:
        # Find active interview
        interview = db.query(Interview).filter(Interview.meeting_id == room).first()
        if not interview:
            return
            
        # 3. Process frame with AI Engine and save metrics inside DB
        results = initialize_ai_engine().process_frame(
            frame, interview_id=interview.id, db_session=db
        )
        
        # 4. Push results back to recruiter/room in real-time
        await sio.emit("metrics_update", results, room=room)
        
    except Exception as e:
        print(f"Error in stream_frame handler: {e}")
    finally:
        db.close()
