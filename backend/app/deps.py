"""Shared FastAPI dependencies and constants."""

from __future__ import annotations

from fastapi import HTTPException, status

from .session import Session, store


# Point-of-contact directory (ported from the original Streamlit app).
PROJECT_DICT: dict[str, str] = {
    "IM3": "Jennie Rice\nIM3 Principal Investigator\njennie.rice@pnnl.gov",
    "GCIMS": "Marshall Wise\nGCIMS Principal Investigator\nmarshall.wise@pnnl.gov",
    "COMPASS-GLM": "Robert Hetland\nCOMPASS-GLM Principal Investigator\nrobert.hetland@pnnl.gov",
    "ICoM": "Ian Kraucunas\nICoM Principal Investigator\nian.kraucunas@pnnl.gov",
    "Puget Sound": (
        "Ning Sun\nPuget Sound Scoping and Pilot Study Principal Investigator\n"
        "ning.sun@pnnl.gov"
    ),
    "Other": (
        "First and Last Name\nCorresponding Project Name with POC Credentials\n"
        "Email Address"
    ),
}


def require_session(session_id: str) -> Session:
    """Fetch a session or raise 401 if it is unknown/expired."""
    session = store.get(session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session. Please authenticate again.",
        )
    return session


def require_content(session: Session) -> str:
    """Ensure a document has been uploaded for the session."""
    if not session.content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No document uploaded for this session.",
        )
    return session.content
