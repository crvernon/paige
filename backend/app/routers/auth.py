"""Authentication router.

Access is granted either by the shared unlock password (``IM3_ACCESS`` in the
environment, e.g. ``phase3``) or by a user supplying their own OpenAI-compatible
API key together with a base URL.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from ..agent import verify_credentials
from ..config import get_settings
from ..schemas import AuthRequest, AuthResponse
from ..session import store

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("", response_model=AuthResponse)
def authenticate(payload: AuthRequest) -> AuthResponse:
    settings = get_settings()

    # Path 1: shared password unlocks the .env-configured endpoint.
    if payload.password:
        if payload.password.strip() == settings.im3_access:
            session = store.create(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                model=settings.openai_model,
                active_project="IM3",
            )
            return AuthResponse(
                session_id=session.session_id,
                active_project=session.active_project,
                model=session.model,
                max_allowable_tokens=settings.max_allowable_tokens,
            )
        # If the password didn't match, fall through to try key-based auth
        # only when an explicit api_key was also provided.
        if not payload.api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid password. Please provide a valid entry.",
            )

    # Path 2: user-supplied OpenAI key + base URL.
    if payload.api_key:
        base_url = payload.base_url or settings.openai_base_url
        model = payload.model or settings.openai_model
        if not verify_credentials(payload.api_key, base_url, model):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key or base URL. Please provide a valid entry.",
            )
        session = store.create(
            api_key=payload.api_key,
            base_url=base_url,
            model=model,
            active_project="OpenAI",
        )
        return AuthResponse(
            session_id=session.session_id,
            active_project=session.active_project,
            model=session.model,
            max_allowable_tokens=settings.max_allowable_tokens,
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Provide either a project password or an API key with base URL.",
    )
