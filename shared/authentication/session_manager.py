from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(slots=True)
class SessionRecord:
    session_id: str
    user_id: str
    created_at: float
    expires_at: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class SessionManager:
    """A lightweight, signed session manager for service-to-service usage."""

    def __init__(self, secret_key: str, ttl_seconds: int = 3600) -> None:
        if not secret_key:
            raise ValueError("secret_key must not be empty")
        self.secret_key = secret_key
        self.ttl_seconds = ttl_seconds
        self._sessions: Dict[str, SessionRecord] = {}

    def create_session(self, user_id: str, *, metadata: Optional[Dict[str, Any]] = None, ttl_seconds: Optional[int] = None) -> str:
        if not user_id:
            raise ValueError("user_id must not be empty")
        now = time.time()
        ttl = ttl_seconds or self.ttl_seconds
        session_id = self._generate_token(user_id, now)
        self._sessions[session_id] = SessionRecord(
            session_id=session_id,
            user_id=user_id,
            created_at=now,
            expires_at=now + ttl,
            metadata=metadata or {},
        )
        return session_id

    def get_session(self, session_id: str) -> Optional[SessionRecord]:
        session = self._sessions.get(session_id)
        if not session:
            return None
        if time.time() >= session.expires_at:
            self._sessions.pop(session_id, None)
            return None
        return session

    def invalidate_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def _generate_token(self, user_id: str, created_at: float) -> str:
        payload = json.dumps({"user_id": user_id, "created_at": created_at}, separators=(",", ":"))
        signature = hmac.new(self.secret_key.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
        return f"{signature}:{payload}"
