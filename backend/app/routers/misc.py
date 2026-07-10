"""Miscellaneous router: health check and logo asset."""

from __future__ import annotations

import importlib.resources

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response

router = APIRouter(tags=["misc"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/logo")
def logo() -> Response:
    """Serve the IM3 logo used in the app header."""
    try:
        logo_path = importlib.resources.files("highlight.data").joinpath("im3.png")
        with logo_path.open("rb") as handle:
            data = handle.read()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Logo file not found.",
        ) from exc
    return Response(content=data, media_type="image/png")
