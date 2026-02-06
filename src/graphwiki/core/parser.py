"""Markdown parser with wiki link support."""

import re
from typing import Callable
from xml.etree.ElementTree import Element

from markdown import Markdown
from markdown.extensions import Extension
from markdown.inlinepatterns import InlineProcessor, SimpleTagInlineProcessor
from markdown.preprocessors import Preprocessor


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


# Pattern for MetaTable macro: <<MetaTable(...)>>
METATABLE_PATTERN = re.compile(r"<<MetaTable\((.+?)\)>>", re.DOTALL)


def _parse_metatable_args(args_str: str) -> tuple[list, list[str]]:
    """Parse MetaTable arguments into filters and columns.

    Args:
        args_str: e.g. "status=draft, ||name||status||author||"

    Returns:
        Tuple of (filter list, column names list).
    """
    from graphwiki.core.graph import GRAPH_ENGINE_AVAILABLE

    if not GRAPH_ENGINE_AVAILABLE:
        return [], []

    from graph_core import Filter

    filters = []
    columns: list[str] = []

    # Extract column spec: ||col1||col2||col3||
    col_match = re.search(r"\|\|(.+?)$", args_str)
    if col_match:
        col_str = col_match.group(0)
        args_str = args_str[: col_match.start()].strip().rstrip(",")
        columns = [c.strip() for c in col_str.split("||") if c.strip()]

    # Parse remaining filters
    if args_str.strip():
        for part in args_str.split(","):
            part = part.strip()
            if not part:
                continue
            if "~=" in part:
                key, value = part.split("~=", 1)
                filters.append(Filter.contains(key.strip(), value.strip()))
            elif "/=" in part:
                key, value = part.split("/=", 1)
                filters.append(Filter.matches(key.strip(), value.strip()))
            elif "=" in part:
                key, value = part.split("=", 1)
                filters.append(Filter.equals(key.strip(), value.strip()))

    return filters, columns


def _render_metatable(filters: list, columns: list[str]) -> str:
    """Render a MetaTable query as an HTML table.

    Args:
        filters: List of Filter objects.
        columns: Column names to display.

    Returns:
        HTML table string.
    """
    from graphwiki.core.graph import get_engine

    engine = get_engine()
    if engine is None:
        return (
            '<p class="metatable-unavailable">'
            "<em>MetaTable: graph engine not available</em></p>"
        )

    if not columns:
        columns = ["name"]

    try:
        result = engine.metatable(filters, columns)
    except Exception as e:
        return f'<p class="metatable-error"><em>MetaTable error: {e}</em></p>'

    if not result.rows:
        return '<p class="metatable-empty"><em>No matching pages found</em></p>'

    lines = ['<table class="metatable">']
    lines.append("<thead><tr>")
    for col in result.columns:
        lines.append(f"<th>{col}</th>")
    lines.append("</tr></thead>")
    lines.append("<tbody>")

    for row in result:
        lines.append("<tr>")
        for col in result.columns:
            values = row.get(col)
            if col == "name" and values:
                page_name = values[0]
                url_name = page_name.replace(" ", "_")
                cell = f'<a href="/page/{url_name}" class="wiki-link">{page_name}</a>'
            elif values:
                cell = ", ".join(values)
            else:
                cell = ""
            lines.append(f"<td>{cell}</td>")
        lines.append("</tr>")

    lines.append("</tbody></table>")
    return "\n".join(lines)


class MetaTablePreprocessor(Preprocessor):
    """Preprocessor that replaces <<MetaTable(...)>> macros with HTML tables."""

    def run(self, lines: list[str]) -> list[str]:
        """Process lines, replacing MetaTable macros."""
        from graphwiki.core.graph import GRAPH_ENGINE_AVAILABLE

        if not GRAPH_ENGINE_AVAILABLE:
            return lines

        text = "\n".join(lines)
        if "<<MetaTable(" not in text:
            return lines

        def replace_match(m: re.Match) -> str:
            args_str = m.group(1)
            filters, columns = _parse_metatable_args(args_str)
            return _render_metatable(filters, columns)

        text = METATABLE_PATTERN.sub(replace_match, text)
        return text.split("\n")


class MetaTableExtension(Extension):
    """Markdown extension for <<MetaTable(...)>> macros."""

    def extendMarkdown(self, md: Markdown) -> None:
        """Add MetaTable preprocessor."""
        md.preprocessors.register(
            MetaTablePreprocessor(md),
            "metatable",
            30,
        )


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
            # PyMdown extensions
            "pymdownx.tasklist",  # Task lists with checkboxes
            # Custom extensions
            StrikethroughExtension(),  # ~~strikethrough~~
            WikiLinkExtension(page_exists=page_exists),  # [[WikiLinks]]
            MetaTableExtension(),  # <<MetaTable(...)>>
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
