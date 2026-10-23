import asyncio

from app.sockets import handlers
from app.models.interview import Interview


class FakeQuery:
    def __init__(self, model, status):
        self.model = model
        self.status = status

    def filter(self, *_):
        return self

    def first(self):
        return Interview(recruiter_id="owner-id", status=self.status) if self.model is Interview else None


class FakeDB:
    status = "scheduled"

    def query(self, model):
        return FakeQuery(model, self.status)

    def close(self):
        pass


def test_join_sends_existing_peers_to_new_participant(monkeypatch):
    emitted_events = []
    monkeypatch.setattr(handlers, "room_participants", {})
    monkeypatch.setattr(handlers, "sid_rooms", {})
    monkeypatch.setattr(handlers, "sid_identities", {"recruiter-sid": "owner-id"})
    monkeypatch.setattr(handlers, "SessionLocal", FakeDB)

    async def enter_room(sid, room):
        return None

    async def emit(event, data, **kwargs):
        emitted_events.append((event, data, kwargs))

    monkeypatch.setattr(handlers.sio, "enter_room", enter_room)
    monkeypatch.setattr(handlers.sio, "emit", emit)

    async def join_in_candidate_first_order():
        await handlers.join_room("candidate-sid", {"room": "meeting-123", "role": "candidate"})
        await handlers.join_room("recruiter-sid", {"room": "meeting-123", "role": "recruiter"})

    asyncio.run(join_in_candidate_first_order())

    roster_event = next(event for event in emitted_events if event[0] == "room_peers")
    assert roster_event[1] == [{"sid": "candidate-sid", "role": "candidate"}]
    assert roster_event[2]["to"] == "recruiter-sid"


def test_recruiter_from_another_account_cannot_join(monkeypatch):
    monkeypatch.setattr(handlers, "room_participants", {})
    monkeypatch.setattr(handlers, "sid_rooms", {})
    monkeypatch.setattr(handlers, "sid_identities", {"attacker-sid": "other-owner"})
    monkeypatch.setattr(handlers, "SessionLocal", FakeDB)

    async def enter_room(*_):
        raise AssertionError("Unauthorized socket must not enter a room")

    monkeypatch.setattr(handlers.sio, "enter_room", enter_room)
    asyncio.run(handlers.join_room("attacker-sid", {"room": "meeting-123", "role": "recruiter"}))
    assert handlers.room_participants == {}


def test_signaling_cannot_be_forwarded_to_another_room(monkeypatch):
    emitted_events = []
    monkeypatch.setattr(handlers, "SessionLocal", FakeDB)
    monkeypatch.setattr(handlers, "room_participants", {"meeting-123": {"recruiter-sid": "recruiter"}})
    monkeypatch.setattr(handlers, "sid_rooms", {"recruiter-sid": "meeting-123"})

    async def emit(event, data, **kwargs):
        emitted_events.append((event, data, kwargs))

    monkeypatch.setattr(handlers.sio, "emit", emit)
    asyncio.run(handlers.rtc_offer("recruiter-sid", {"room": "other-meeting", "sdp": {"type": "offer", "sdp": "test"}}))
    assert emitted_events == []

    asyncio.run(handlers.rtc_offer("recruiter-sid", {"room": "meeting-123", "sdp": {"type": "offer", "sdp": "test"}}))
    assert emitted_events[0][2]["room"] == "meeting-123"


def test_invalid_sdp_and_ice_payloads_are_not_forwarded(monkeypatch):
    emitted_events = []
    monkeypatch.setattr(handlers, "room_participants", {
        "meeting-123": {"recruiter-sid": "recruiter", "candidate-sid": "candidate"},
    })
    monkeypatch.setattr(handlers, "sid_rooms", {
        "recruiter-sid": "meeting-123",
        "candidate-sid": "meeting-123",
    })

    async def emit(event, data, **kwargs):
        emitted_events.append((event, data, kwargs))

    monkeypatch.setattr(handlers.sio, "emit", emit)
    asyncio.run(handlers.rtc_offer("recruiter-sid", {"room": "meeting-123", "sdp": {"type": "answer", "sdp": "bad direction"}}))
    asyncio.run(handlers.rtc_ice_candidate("candidate-sid", {"room": "meeting-123", "candidate": {"candidate": 7}}))

    assert emitted_events == []


def test_completed_and_cancelled_interviews_reject_socket_joins(monkeypatch):
    for terminal_status in ("completed", "cancelled"):
        monkeypatch.setattr(handlers, "room_participants", {})
        monkeypatch.setattr(handlers, "sid_rooms", {})
        monkeypatch.setattr(handlers, "sid_identities", {"candidate-sid": None})
        monkeypatch.setattr(handlers, "SessionLocal", lambda status=terminal_status: _StatusDB(status))

        async def enter_room(*_args):
            raise AssertionError("Terminal interview must not accept a socket join")

        monkeypatch.setattr(handlers.sio, "enter_room", enter_room)
        asyncio.run(handlers.join_room(
            "candidate-sid", {"room": "meeting-terminal", "role": "candidate"}
        ))
        assert handlers.room_participants == {}
        assert handlers.sid_rooms == {}


def test_completed_and_cancelled_interviews_reject_existing_signaling(monkeypatch):
    for terminal_status in ("completed", "cancelled"):
        emitted = []
        monkeypatch.setattr(handlers, "room_participants", {
            "meeting-terminal": {"candidate-sid": "candidate"},
        })
        monkeypatch.setattr(handlers, "sid_rooms", {"candidate-sid": "meeting-terminal"})
        monkeypatch.setattr(handlers, "SessionLocal", lambda status=terminal_status: _StatusDB(status))

        async def emit(*args, **kwargs):
            emitted.append((args, kwargs))

        monkeypatch.setattr(handlers.sio, "emit", emit)
        asyncio.run(handlers.rtc_ice_candidate("candidate-sid", {
            "room": "meeting-terminal",
            "candidate": {"candidate": "candidate:1 1 UDP 1 192.0.2.1 1234 typ host"},
        }))
        assert emitted == []


def test_room_join_and_leave_logs_do_not_include_bearer_code(monkeypatch, capsys):
    meeting_code = "private-meeting-code-log-test"
    monkeypatch.setattr(handlers, "room_participants", {})
    monkeypatch.setattr(handlers, "sid_rooms", {})
    monkeypatch.setattr(handlers, "sid_identities", {"candidate-sid": None})
    monkeypatch.setattr(handlers, "SessionLocal", FakeDB)

    async def noop(*_args, **_kwargs):
        return None

    monkeypatch.setattr(handlers.sio, "enter_room", noop)
    monkeypatch.setattr(handlers.sio, "leave_room", noop)
    monkeypatch.setattr(handlers.sio, "emit", noop)
    asyncio.run(handlers.join_room("candidate-sid", {"room": meeting_code, "role": "candidate"}))
    asyncio.run(handlers.leave_room("candidate-sid", {"room": meeting_code}))

    assert meeting_code not in capsys.readouterr().out


class _StatusDB(FakeDB):
    def __init__(self, status):
        self.status = status
