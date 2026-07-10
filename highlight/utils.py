"""Utility helpers for the PAIGE highlight generator.

This module is intentionally free of any web-framework dependencies
(no Streamlit) and free of LangChain. All LLM interaction now lives in the
FastAPI backend's Pydantic AI agent layer (``backend/app/agent.py``).

The helpers here cover:

* document ingestion (:func:`read_pdf`, :func:`read_text`)
* token counting (:func:`get_token_count`)
* Wikimedia Commons image search (:func:`search_wikimedia_commons`)
* PDF image extraction (:func:`extract_images_from_pdf`)
* user-prompt formatting (:func:`generate_prompt`)

It also defines the structured-output models :class:`ApproachPoints`
and :class:`ImpactPoints`.
"""

import io
import logging
import re
from typing import List

import fitz  # PyMuPDF
import requests
import tiktoken
from pydantic import BaseModel, Field
from pypdf import PdfReader

import highlight.prompts as prompts


WIKIMEDIA_API_ENDPOINT = "https://commons.wikimedia.org/w/api.php"


# --- Structured output models (used by the Pydantic AI agents) ---
class ApproachPoints(BaseModel):
    """Structured approach output."""

    points: List[str] = Field(
        description=(
            "List of 2-3 short bullet points describing the methodological "
            "approach using active verbs."
        )
    )


class ImpactPoints(BaseModel):
    """Structured impact output."""

    points: List[str] = Field(
        description=(
            "List of 3 concise bullet points stating key results/outcomes, "
            "highlighting profound or surprising findings."
        )
    )


def search_wikimedia_commons(query: str, limit: int = 9) -> list:
    """Search Wikimedia Commons for images matching the query.

    Args:
        query: The search phrase.
        limit: Maximum number of images to retrieve.

    Returns:
        A list of image metadata dictionaries.
    """
    logging.info("Searching Wikimedia Commons for: '%s' with limit %s", query, limit)
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": 6,
        "gsrlimit": limit,
        "prop": "imageinfo",
        "iiprop": "url|extmetadata|size|dimensions|mime",
        "iimetadataversion": "latest",
        "iiurlwidth": 200,
        "formatversion": 2,
    }
    results: list = []
    raw_data = None
    try:
        headers = {
            "User-Agent": (
                "PAIGE/1.0 (https://github.com/crvernon/highlight; "
                "chris.vernon@pnnl.gov)"
            )
        }
        response = requests.get(
            WIKIMEDIA_API_ENDPOINT, params=params, timeout=10, headers=headers
        )
        response.raise_for_status()
        raw_data = response.json()

        if "query" in raw_data and "pages" in raw_data["query"]:
            pages = raw_data["query"]["pages"]
            for page_data in pages:
                if page_data.get("missing", False) or "imageinfo" not in page_data:
                    continue

                image_info = page_data["imageinfo"][0]
                metadata = image_info.get("extmetadata", {})

                title = page_data.get("title", "Unknown Title")
                thumbnail_url = image_info.get("thumburl", None)
                full_url = image_info.get("url", None)
                description_url = image_info.get("descriptionurl", None)
                license_short = metadata.get("LicenseShortName", {}).get("value", "")
                artist_html = metadata.get("Artist", {}).get("value", "")
                license_url = metadata.get("LicenseUrl", {}).get("value", None)

                artist_plain = re.sub(r"<.*?>", "", artist_html).strip()
                artist_plain = (
                    artist_plain.replace("&amp;", "&")
                    .replace("&lt;", "<")
                    .replace("&gt;", ">")
                )
                artist_plain_final = artist_plain or "Unknown Artist"

                mime_type = image_info.get("mime", "application/octet-stream")

                if thumbnail_url:
                    results.append(
                        {
                            "id": page_data.get("pageid"),
                            "title": title,
                            "thumbnail_url": thumbnail_url,
                            "full_url": full_url,
                            "page_url": description_url,
                            "license": license_short,
                            "artist_html": artist_html,
                            "artist_plain": artist_plain_final,
                            "license_url": license_url,
                            "mime": mime_type,
                        }
                    )
        return results
    except Exception as exc:  # noqa: BLE001 - log and degrade gracefully
        logging.error("Error processing Wikimedia response: %s", exc, exc_info=True)
        if raw_data:
            logging.error("Raw data causing error: %s", raw_data)
        return []


def get_token_count(text: str, model: str = "gpt-4o") -> int:
    """Calculate the number of tokens in ``text`` for a given ``model``."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except Exception:  # noqa: BLE001 - fall back for unknown models (e.g. gpt-5)
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def read_pdf(file_object: object, reference_indicator: str = "References\n") -> dict:
    """Extract text from a PDF up to a reference indicator.

    Returns a dict with ``content`` and the ``n_pages``, ``n_characters``,
    ``n_words`` and ``n_tokens`` statistics.
    """
    content = ""
    n_pages = 0

    reader = PdfReader(file_object)

    for page in reader.pages:
        page_content = page.extract_text() or ""

        if reference_indicator in page_content:
            content_part, _, _ = page_content.partition(reference_indicator)
            content += content_part
            n_pages += 1
            break
        content += page_content
        n_pages += 1

    if reference_indicator in content:
        content = content.split(reference_indicator)[0]

    return {
        "content": content,
        "n_pages": n_pages,
        "n_characters": len(content),
        "n_words": len(content.split()),
        "n_tokens": get_token_count(content),
    }


def read_text(file_object: object) -> dict:
    """Read a text file object and return content plus statistics."""
    raw = file_object.read()
    if isinstance(raw, bytes):
        content = raw.decode("utf-8")
    else:
        content = raw

    return {
        "content": content,
        "n_pages": 1,
        "n_characters": len(content),
        "n_words": len(content.replace("\n", " ").split()),
        "n_tokens": get_token_count(content),
    }


def generate_prompt(
    content: str,
    prompt_name: str,
    additional_content: str = None,
) -> str:
    """Format the user-specific portion of a prompt.

    Args:
        content: The main document text.
        prompt_name: Key into :data:`highlight.prompts.prompt_queue`.
        additional_content: Extra content needed by some prompts (e.g. the
            title for the subtitle, the objective for the approach, or the
            figure identifier for a figure caption).

    Returns:
        The formatted user prompt string.
    """
    try:
        prompt_template_string = prompts.prompt_queue[prompt_name]
    except KeyError as exc:
        raise ValueError(f"Unknown prompt_name: '{prompt_name}'") from exc

    try:
        if prompt_name in ("objective",):
            return prompt_template_string.format(
                prompts.EXAMPLE_TEXT_ONE,
                prompts.EXAMPLE_TEXT_TWO,
                content,
            )
        if prompt_name in ("approach", "subtitle", "selected_figure_caption"):
            if additional_content is None:
                raise ValueError(
                    f"additional_content is required for prompt '{prompt_name}'"
                )
            return prompt_template_string.format(content, additional_content)
        return prompt_template_string.format(content)
    except Exception as exc:  # noqa: BLE001
        raise KeyError(
            f"Error formatting prompt '{prompt_name}': {exc}. "
            "Check prompt template and arguments."
        ) from exc


def extract_images_from_pdf(pdf_bytes: bytes) -> list:
    """Extract embedded images from PDF bytes.

    Returns a list of dicts with ``index``, ``page``, ``xref`` and ``bytes``.
    """
    images: list = []
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            image_list = page.get_images(full=True)
            for img_info in image_list:
                xref = img_info[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                images.append(
                    {
                        "index": len(images),
                        "page": page_num + 1,
                        "xref": xref,
                        "bytes": image_bytes,
                    }
                )
        doc.close()
        return images
    except Exception as exc:  # noqa: BLE001
        logging.error("Error extracting images from PDF: %s", exc, exc_info=True)
        return []
