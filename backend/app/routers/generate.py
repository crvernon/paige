"""Generation router: all LLM-backed text and structured endpoints."""

from __future__ import annotations

import highlight as hlt
import highlight.prompts as prompts
from fastapi import APIRouter, HTTPException, status

from ..agent import generate_structured, generate_text
from ..deps import require_content, require_session
from ..schemas import (
    FigureListResponse,
    GenerateRequest,
    GenerateResponse,
    StructuredResponse,
)
from ..session import Session

router = APIRouter(prefix="/generate", tags=["generate"])


def _resolve_input(session: Session, req: GenerateRequest) -> str:
    """Return the text the prompt should operate on."""
    if req.content_override is not None:
        return req.content_override
    return require_content(session)


def _maybe_reduce_wordcount(
    session: Session,
    text: str,
    max_word_count: int | None,
    min_word_count: int | None,
) -> str:
    """Reduce an oversized response to the requested word window."""
    if not max_word_count:
        return text
    if len(text.split()) <= max_word_count:
        return text
    reduction_prompt = prompts.prompt_queue["reduce_wordcount"].format(
        min_word_count or 0, max_word_count, text
    )
    try:
        return generate_text(
            reduction_prompt,
            api_key=session.api_key,
            base_url=session.base_url,
            model=session.model,
        )
    except Exception:  # noqa: BLE001 - keep the original text on failure
        return text


def _run_text_prompt(
    session: Session,
    req: GenerateRequest,
    prompt_name: str,
) -> GenerateResponse:
    content = _resolve_input(session, req)
    try:
        user_prompt = hlt.generate_prompt(
            content=content,
            prompt_name=prompt_name,
            additional_content=req.additional_content,
        )
        text = generate_text(
            user_prompt,
            api_key=session.api_key,
            base_url=session.base_url,
            model=session.model,
        )
        text = _maybe_reduce_wordcount(
            session, text, req.max_word_count, req.min_word_count
        )
        return GenerateResponse(text=text, word_count=len(text.split()))
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Generation failed for '{prompt_name}': {exc}",
        ) from exc


# --- Simple text endpoints ---
@router.post("/title", response_model=GenerateResponse)
def gen_title(req: GenerateRequest) -> GenerateResponse:
    return _run_text_prompt(require_session(req.session_id), req, "title")


@router.post("/subtitle", response_model=GenerateResponse)
def gen_subtitle(req: GenerateRequest) -> GenerateResponse:
    return _run_text_prompt(require_session(req.session_id), req, "subtitle")


@router.post("/science", response_model=GenerateResponse)
def gen_science(req: GenerateRequest) -> GenerateResponse:
    return _run_text_prompt(require_session(req.session_id), req, "science")


@router.post("/impact", response_model=GenerateResponse)
def gen_impact(req: GenerateRequest) -> GenerateResponse:
    return _run_text_prompt(require_session(req.session_id), req, "impact")


@router.post("/summary", response_model=GenerateResponse)
def gen_summary(req: GenerateRequest) -> GenerateResponse:
    return _run_text_prompt(require_session(req.session_id), req, "summary")


@router.post("/citation", response_model=GenerateResponse)
def gen_citation(req: GenerateRequest) -> GenerateResponse:
    resp = _run_text_prompt(require_session(req.session_id), req, "citation")
    resp.text = resp.text.replace('"', "")
    resp.word_count = len(resp.text.split())
    return resp


@router.post("/funding", response_model=GenerateResponse)
def gen_funding(req: GenerateRequest) -> GenerateResponse:
    resp = _run_text_prompt(require_session(req.session_id), req, "funding")
    resp.text = resp.text.replace('"', "")
    resp.word_count = len(resp.text.split())
    return resp


@router.post("/objective", response_model=GenerateResponse)
def gen_objective(req: GenerateRequest) -> GenerateResponse:
    return _run_text_prompt(require_session(req.session_id), req, "objective")


@router.post("/search-strings", response_model=GenerateResponse)
def gen_search_strings(req: GenerateRequest) -> GenerateResponse:
    # Uses the 'figure' prompt; input is typically the general summary.
    return _run_text_prompt(require_session(req.session_id), req, "figure")


@router.post("/image-caption", response_model=GenerateResponse)
def gen_image_caption(req: GenerateRequest) -> GenerateResponse:
    return _run_text_prompt(require_session(req.session_id), req, "figure_caption")


@router.post("/figure-caption", response_model=GenerateResponse)
def gen_figure_caption(req: GenerateRequest) -> GenerateResponse:
    # additional_content carries the selected figure identifier.
    return _run_text_prompt(
        require_session(req.session_id), req, "selected_figure_caption"
    )


# --- Figure list (parsed into a dict) ---
@router.post("/figure-list", response_model=FigureListResponse)
def gen_figure_list(req: GenerateRequest) -> FigureListResponse:
    session = require_session(req.session_id)
    content = _resolve_input(session, req)
    try:
        user_prompt = hlt.generate_prompt(content=content, prompt_name="figure_list")
        raw = generate_text(
            user_prompt,
            api_key=session.api_key,
            base_url=session.base_url,
            model=session.model,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Figure list generation failed: {exc}",
        ) from exc

    figures: dict[str, str] = {}
    for line in raw.strip().split("\n"):
        if line.strip().lower().startswith("table"):
            continue
        if " :: " in line:
            identifier, description = line.split(" :: ", 1)
            identifier = identifier.strip()
            description = description.strip()
            if identifier and description and not identifier.lower().startswith("table"):
                figures[identifier] = description
    return FigureListResponse(figures=figures)


# --- Structured endpoints ---
@router.post("/approach", response_model=StructuredResponse)
def gen_approach(req: GenerateRequest) -> StructuredResponse:
    session = require_session(req.session_id)
    content = _resolve_input(session, req)
    if not req.additional_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The objective statement is required to generate the approach.",
        )
    try:
        user_prompt = hlt.generate_prompt(
            content=content,
            prompt_name="approach",
            additional_content=req.additional_content,
        )
        result = generate_structured(
            user_prompt,
            hlt.ApproachPoints,
            api_key=session.api_key,
            base_url=session.base_url,
            model=session.model,
        )
        return StructuredResponse(points=result.points)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Approach generation failed: {exc}",
        ) from exc


@router.post("/ppt-impact", response_model=StructuredResponse)
def gen_ppt_impact(req: GenerateRequest) -> StructuredResponse:
    session = require_session(req.session_id)
    content = _resolve_input(session, req)
    try:
        user_prompt = hlt.generate_prompt(content=content, prompt_name="ppt_impact")
        result = generate_structured(
            user_prompt,
            hlt.ImpactPoints,
            api_key=session.api_key,
            base_url=session.base_url,
            model=session.model,
        )
        return StructuredResponse(points=result.points)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Impact points generation failed: {exc}",
        ) from exc
