"""Data models for MeshWiki."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PageMetadata(BaseModel):
    """Metadata extracted from page frontmatter."""

    model_config = ConfigDict(extra="allow")

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

    @property
    def word_count(self) -> int:
        """Approximate word count of page content."""
        return len(self.content.split())
