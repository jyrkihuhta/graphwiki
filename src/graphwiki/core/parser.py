"""Markdown parser with wiki link support."""

import re
from typing import Callable
from xml.etree.ElementTree import Element

from markdown import Markdown
from markdown.extensions import Extension
from markdown.inlinepatterns import InlineProcessor, SimpleTagInlineProcessor


# Pattern for wiki links: [[PageName]] or [[PageName|Display Text]]
WIKI_LINK_PATTERN = r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]"

# Pattern for strikethrough: ~~text~~
# Group 2 must contain the text (SimpleTagInlineProcessor expectation)
STRIKETHROUGH_PATTERN = r"(~~)(.*?)~~"


class StrikethroughExtension(Extension):
    """Markdown extension for ~~strikethrough~~ text."""

    def extendMarkdown(self, md: Markdown) -> None:
        """Add strikethrough pattern to markdown parser."""
        md.inlinePatterns.register(
            SimpleTagInlineProcessor(STRIKETHROUGH_PATTERN, "del"),
            "strikethrough",
            50,
        )


class WikiLinkInlineProcessor(InlineProcessor):
    """Inline processor for wiki links."""

    def __init__(self, pattern: str, md: Markdown, page_exists: Callable[[str], bool]):
        super().__init__(pattern, md)
        self.page_exists = page_exists

    def handleMatch(self, m: re.Match, data: str) -> tuple[Element | None, int, int]:
        """Convert wiki link match to HTML anchor element."""
        page_name = m.group(1).strip()
        display_text = m.group(2)
        if display_text:
            display_text = display_text.strip()
        else:
            display_text = page_name

        # Create anchor element
        el = Element("a")
        el.text = display_text
        el.set("href", f"/page/{page_name.replace(' ', '_')}")

        # Add class based on whether page exists
        if self.page_exists(page_name):
            el.set("class", "wiki-link")
        else:
            el.set("class", "wiki-link wiki-link-missing")

        return el, m.start(0), m.end(0)


class WikiLinkExtension(Extension):
    """Markdown extension for wiki links."""

    def __init__(self, page_exists: Callable[[str], bool] | None = None, **kwargs):
        self.page_exists = page_exists or (lambda x: True)
        super().__init__(**kwargs)

    def extendMarkdown(self, md: Markdown) -> None:
        """Add wiki link pattern to markdown parser."""
        wiki_link_processor = WikiLinkInlineProcessor(
            WIKI_LINK_PATTERN,
            md,
            self.page_exists,
        )
        md.inlinePatterns.register(wiki_link_processor, "wiki_link", 75)


def create_parser(page_exists: Callable[[str], bool] | None = None) -> Markdown:
    """Create a Markdown parser with wiki link support.

    Args:
        page_exists: Callback to check if a page exists.
                    Used to style missing page links differently.

    Returns:
        Configured Markdown parser instance.
    """
    return Markdown(
        extensions=[
            # Core formatting
            "extra",  # Includes: abbreviations, attr_list, def_list, fenced_code, footnotes, md_in_html, tables
            "sane_lists",  # Better list handling
            "smarty",  # Smart quotes and dashes
            "toc",  # Table of contents
            # Custom extensions
            StrikethroughExtension(),  # ~~strikethrough~~
            WikiLinkExtension(page_exists=page_exists),  # [[WikiLinks]]
        ]
    )


def parse_wiki_content(
    content: str,
    page_exists: Callable[[str], bool] | None = None,
) -> str:
    """Parse wiki content (Markdown + wiki links) to HTML.

    Args:
        content: Markdown content with wiki links.
        page_exists: Callback to check if a page exists.

    Returns:
        HTML string.
    """
    parser = create_parser(page_exists)
    return parser.convert(content)


def extract_wiki_links(content: str) -> list[str]:
    """Extract all wiki links from content.

    Args:
        content: Markdown content with wiki links.

    Returns:
        List of page names referenced in wiki links.
    """
    matches = re.findall(WIKI_LINK_PATTERN, content)
    return [m[0].strip() for m in matches]
