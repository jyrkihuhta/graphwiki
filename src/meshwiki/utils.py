"""Utility functions for MeshWiki."""

import re


def slugify(text: str) -> str:
    """Convert text to a URL-safe slug.

    Args:
        text: The input text to slugify.

    Returns:
        A lowercase slug with hyphens separating words,
        multiple consecutive hyphens collapsed, and
        leading/trailing hyphens stripped.
    """
    slug = text.lower()
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"[^a-z0-9\-]", "", slug)
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")
    return slug
