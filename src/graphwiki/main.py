"""GraphWiki FastAPI application."""

from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from graphwiki.config import settings
from graphwiki.core.models import Page
from graphwiki.core.parser import parse_wiki_content
from graphwiki.core.storage import FileStorage

# Initialize app
app = FastAPI(
    title=settings.app_title,
    debug=settings.debug,
)

# Setup templates and static files
templates_path = Path(__file__).parent / "templates"
static_path = Path(__file__).parent / "static"

templates = Jinja2Templates(directory=str(templates_path))
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Initialize storage
storage = FileStorage(settings.data_dir)


# Template context helper
def get_context(request: Request, **kwargs) -> dict:
    """Create base context for templates."""
    return {
        "request": request,
        "app_title": settings.app_title,
        **kwargs,
    }


# Page existence checker for parser
def page_exists_sync(name: str) -> bool:
    """Synchronous check if page exists (for parser callback)."""
    return storage._get_path(name).exists()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Home page - list all pages."""
    pages = await storage.list_pages()
    return templates.TemplateResponse(
        "page/list.html",
        get_context(request, pages=pages),
    )


@app.get("/page/{name}", response_class=HTMLResponse)
async def view_page(request: Request, name: str):
    """View a wiki page."""
    page = await storage.get_page(name)

    if page is None:
        # Page doesn't exist - redirect to edit to create it
        return RedirectResponse(url=f"/page/{name}/edit", status_code=302)

    # Parse content with wiki links
    html_content = parse_wiki_content(page.content, page_exists=page_exists_sync)

    return templates.TemplateResponse(
        "page/view.html",
        get_context(request, page=page, html_content=html_content),
    )


@app.get("/page/{name}/edit", response_class=HTMLResponse)
async def edit_page(request: Request, name: str):
    """Edit page form."""
    page = await storage.get_page(name)

    if page is None:
        # New page
        page = Page(name=name, content="", exists=False)

    return templates.TemplateResponse(
        "page/edit.html",
        get_context(request, page=page),
    )


@app.post("/page/{name}", response_class=HTMLResponse)
async def save_page(request: Request, name: str, content: str = Form(...)):
    """Save page content."""
    page = await storage.save_page(name, content)

    # Check if this is an HTMX request
    if request.headers.get("HX-Request"):
        # Return just the content area for HTMX swap
        html_content = parse_wiki_content(page.content, page_exists=page_exists_sync)
        return templates.TemplateResponse(
            "page/view.html",
            get_context(request, page=page, html_content=html_content),
        )

    # Regular form submit - redirect to view
    return RedirectResponse(url=f"/page/{name}", status_code=302)


@app.get("/page/{name}/raw")
async def raw_page(name: str):
    """Get raw markdown content."""
    page = await storage.get_page(name)
    if page is None:
        raise HTTPException(status_code=404, detail="Page not found")
    return {"content": page.content}


@app.post("/page/{name}/delete")
async def delete_page(name: str):
    """Delete a page."""
    deleted = await storage.delete_page(name)
    if not deleted:
        raise HTTPException(status_code=404, detail="Page not found")
    return RedirectResponse(url="/", status_code=302)
