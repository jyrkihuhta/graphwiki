"""Utility functions for MeshWiki."""

from __future__ import annotations

import re


def slugify(text: str) -> str:
    """Convert text to a URL-safe slug.

    - Lowercase the input
    - Replace spaces and underscores with hyphens
    - Strip any character that is not alphanumeric or a hyphen
    - Collapse multiple consecutive hyphens into one
    - Strip leading/trailing hyphens

    Example: slugify("Hello World!") → "hello-world"
    """
    text = text.lower()
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"[^a-z0-9-]", "", text)
    text = re.sub(r"-+", "-", text)
    text = text.strip("-")
    return text
