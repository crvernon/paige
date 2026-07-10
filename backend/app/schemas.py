"""Pydantic request/response schemas for the PAIGE API."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


# --- Auth ---
class AuthRequest(BaseModel):
    """Either a shared password OR a user-supplied OpenAI key + base URL."""

    password: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None


class AuthResponse(BaseModel):
    session_id: str
    active_project: str
    model: str
    max_allowable_tokens: int


# --- Upload ---
class UploadResponse(BaseModel):
    filename: str
    n_pages: int
    n_characters: int
    n_words: int
    n_tokens: int
    max_allowable_tokens: int
    exceeds_limit: bool
    has_pdf_images: bool


# --- Text generation ---
class GenerateRequest(BaseModel):
    session_id: str
    # Optional extra context (e.g. title for subtitle, objective for approach,
    # figure id for a figure caption, or a summary/text override for the input).
    additional_content: Optional[str] = None
    # When provided, use this text as the LLM input instead of the uploaded doc.
    content_override: Optional[str] = None
    max_word_count: Optional[int] = None
    min_word_count: Optional[int] = None


class GenerateResponse(BaseModel):
    text: str
    word_count: int


class StructuredResponse(BaseModel):
    points: List[str]


# --- Wikimedia ---
class WikimediaImage(BaseModel):
    id: Optional[int] = None
    title: str
    thumbnail_url: Optional[str] = None
    full_url: Optional[str] = None
    page_url: Optional[str] = None
    license: str = ""
    artist_html: str = ""
    artist_plain: str = "Unknown Artist"
    license_url: Optional[str] = None
    mime: str = "application/octet-stream"


class WikimediaSearchResponse(BaseModel):
    results: List[WikimediaImage]


# --- PDF image extraction ---
class PdfImageInfo(BaseModel):
    index: int
    page: int
    # Base64-encoded image bytes for preview/transport.
    data_url: str
    mime: str = "image/png"


class PdfImagesResponse(BaseModel):
    images: List[PdfImageInfo]


# --- Exports ---
class SelectedImage(BaseModel):
    """A chosen Wikimedia image plus attribution used in the Word doc."""

    full_url: Optional[str] = None
    page_url: Optional[str] = None
    artist_plain: Optional[str] = None
    license: Optional[str] = None
    license_url: Optional[str] = None


class WordExportRequest(BaseModel):
    session_id: str
    title: Optional[str] = ""
    subtitle: Optional[str] = ""
    image_caption: Optional[str] = ""
    science: Optional[str] = ""
    impact: Optional[str] = ""
    summary: Optional[str] = ""
    funding: Optional[str] = ""
    citation: Optional[str] = ""
    related_links: Optional[str] = ""
    point_of_contact: Optional[str] = ""
    # Selected editorial image (fetched server-side from full_url)
    selected_image: Optional[SelectedImage] = None


class PptExportRequest(BaseModel):
    session_id: str
    title: str = ""
    objective: str = ""
    citation: str = ""
    figure_caption: str = ""
    approach_points: List[str] = Field(default_factory=list)
    impact_points: List[str] = Field(default_factory=list)
    # Index into the extracted PDF images to embed in the slide (optional).
    figure_image_index: Optional[int] = None


class FigureListResponse(BaseModel):
    figures: dict[str, str]
