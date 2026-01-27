"""Storage abstraction for wiki pages."""

import re
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

import yaml

from graphwiki.core.models import Page, PageMetadata


class Storage(ABC):
    """Abstract base class for page storage."""

    @abstractmethod
    async def get_page(self, name: str) -> Page | None:
        """Get a page by name. Returns None if not found."""
        ...

    @abstractmethod
    async def save_page(self, name: str, content: str) -> Page:
        """Save a page. Creates if doesn't exist."""
        ...

    @abstractmethod
    async def delete_page(self, name: str) -> bool:
        """Delete a page. Returns True if deleted, False if not found."""
        ...

    @abstractmethod
    async def list_pages(self) -> list[str]:
        """List all page names."""
        ...

    @abstractmethod
    async def page_exists(self, name: str) -> bool:
        """Check if a page exists."""
        ...


class FileStorage(Storage):
    """File-based storage implementation.

    Pages are stored as Markdown files with optional YAML frontmatter.
    File naming: PageName.md (spaces converted to underscores)
    """

    FRONTMATTER_PATTERN = re.compile(
        r"^---\s*\n(.*?)\n---\s*\n",
        re.DOTALL,
    )

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _name_to_filename(self, name: str) -> str:
        """Convert page name to filename."""
        return name.replace(" ", "_") + ".md"

    def _filename_to_name(self, filename: str) -> str:
        """Convert filename to page name."""
        return filename.removesuffix(".md").replace("_", " ")

    def _get_path(self, name: str) -> Path:
        """Get full path for a page."""
        return self.base_path / self._name_to_filename(name)

    def _parse_frontmatter(self, content: str) -> tuple[PageMetadata, str]:
        """Parse YAML frontmatter from content.

        Returns (metadata, content_without_frontmatter).
        """
        match = self.FRONTMATTER_PATTERN.match(content)
        if match:
            try:
                frontmatter = yaml.safe_load(match.group(1)) or {}
                metadata = PageMetadata(**frontmatter)
                content = content[match.end() :]
                return metadata, content
            except (yaml.YAMLError, TypeError):
                pass
        return PageMetadata(), content

    def _create_frontmatter(self, metadata: PageMetadata) -> str:
        """Create YAML frontmatter string from metadata."""
        data = metadata.model_dump(exclude_none=True, exclude_defaults=True)
        if not data:
            return ""
        # Convert datetime to ISO format string
        if "created" in data:
            data["created"] = data["created"].isoformat()
        if "modified" in data:
            data["modified"] = data["modified"].isoformat()
        return f"---\n{yaml.dump(data, default_flow_style=False)}---\n\n"

    async def get_page(self, name: str) -> Page | None:
        """Get a page by name."""
        path = self._get_path(name)
        if not path.exists():
            return None

        content = path.read_text(encoding="utf-8")
        metadata, content = self._parse_frontmatter(content)

        return Page(
            name=name,
            content=content,
            metadata=metadata,
            exists=True,
        )

    async def save_page(self, name: str, content: str) -> Page:
        """Save a page."""
        path = self._get_path(name)

        # Parse any frontmatter from the content
        metadata, body = self._parse_frontmatter(content)

        # Update modification time
        now = datetime.now()
        if not metadata.created:
            metadata.created = now
        metadata.modified = now

        # Write with frontmatter
        frontmatter = self._create_frontmatter(metadata)
        path.write_text(frontmatter + body, encoding="utf-8")

        return Page(
            name=name,
            content=body,
            metadata=metadata,
            exists=True,
        )

    async def delete_page(self, name: str) -> bool:
        """Delete a page."""
        path = self._get_path(name)
        if path.exists():
            path.unlink()
            return True
        return False

    async def list_pages(self) -> list[str]:
        """List all page names."""
        pages = []
        for path in self.base_path.glob("*.md"):
            pages.append(self._filename_to_name(path.name))
        return sorted(pages)

    async def page_exists(self, name: str) -> bool:
        """Check if a page exists."""
        return self._get_path(name).exists()
