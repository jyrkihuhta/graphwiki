"""Data models for GraphWiki."""

from datetime import datetime

from pydantic import BaseModel, Field


class PageMetadata(BaseModel):
    """Metadata extracted from page frontmatter."""

    title: str | None = None
    tags: list[str] = Field(default_factory=list)
    created: datetime | None = None
    modified: datetime | None = None


class Page(BaseModel):
    """Represents a wiki page."""

    name: str
    content: str
    metadata: PageMetadata = Field(default_factory=PageMetadata)
    exists: bool = True

    @property
    def title(self) -> str:
        """Return title from metadata or derive from name."""
        return self.metadata.title or self.name.replace("_", " ")
