"""In-memory session store.

Suitable for a single-instance EC2 deployment. Each session holds the resolved
LLM credentials and the most recently uploaded document content so that
generation endpoints don't need to re-transmit the full document body.
"""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class Session:
    """Per-user session state."""

    session_id: str
    api_key: str
    base_url: str
    model: str
    active_project: str = "Other"
    # Uploaded document
    content: Optional[str] = None
    filename: Optional[str] = None
    stats: dict = field(default_factory=dict)
    # Raw PDF bytes retained for image extraction
    pdf_bytes: Optional[bytes] = None


class SessionStore:
    """Thread-safe in-memory session registry."""

    def __init__(self) -> None:
        self._sessions: Dict[str, Session] = {}
        self._lock = threading.Lock()

    def create(self, *, api_key: str, base_url: str, model: str, active_project: str) -> Session:
        session_id = uuid.uuid4().hex
        session = Session(
            session_id=session_id,
            api_key=api_key,
            base_url=base_url,
            model=model,
            active_project=active_project,
        )
        with self._lock:
            self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> Optional[Session]:
        with self._lock:
            return self._sessions.get(session_id)

    def delete(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)


# Module-level singleton
store = SessionStore()
