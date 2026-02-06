"""GraphWiki FastAPI application."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from graphwiki.config import settings
from graphwiki.core.graph import get_engine, init_engine, shutdown_engine
from graphwiki.core.ws_manager import manager
from graphwiki.core.models import Page
from graphwiki.core.parser import parse_wiki_content
from graphwiki.core.storage import FileStorage


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize and shutdown graph engine."""
    init_engine(settings.data_dir, watch=settings.graph_watch)
    manager.start_polling()
    yield
    manager.stop_polling()
    shutdown_engine()


# Initialize app
app = FastAPI(
    title=settings.app_title,
    debug=settings.debug,
    lifespan=lifespan,
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
    """Synchronous check if page exists (for parser callback).

    Uses graph engine if available, falls back to filesystem.
    """
    engine = get_engine()
    if engine is not None:
        try:
            return engine.page_exists(name)
        except Exception:
            pass
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

    # Get backlinks from graph engine
    backlinks: list[str] = []
    engine = get_engine()
    if engine is not None:
        try:
            backlinks = sorted(engine.get_backlinks(name))
        except Exception:
            pass

    return templates.TemplateResponse(
        "page/view.html",
        get_context(request, page=page, html_content=html_content, backlinks=backlinks),
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
async def save_page(request: Request, name: str, content: str = Form("")):
    """Save page content."""
    page = await storage.save_page(name, content)

    # Check if this is an HTMX request
    if request.headers.get("HX-Request"):
        # Return just the content area for HTMX swap
        html_content = parse_wiki_content(page.content, page_exists=page_exists_sync)
        backlinks: list[str] = []
        engine = get_engine()
        if engine is not None:
            try:
                backlinks = sorted(engine.get_backlinks(name))
            except Exception:
                pass
        return templates.TemplateResponse(
            "page/view.html",
            get_context(request, page=page, html_content=html_content, backlinks=backlinks),
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


# ========== Graph visualization ==========


@app.get("/graph", response_class=HTMLResponse)
async def graph_view(request: Request):
    """Graph visualization page."""
    return templates.TemplateResponse(
        "graph.html",
        get_context(request),
    )


@app.get("/api/graph")
async def api_graph():
    """Return full graph as JSON for visualization."""
    engine = get_engine()
    if engine is None:
        return {"nodes": [], "links": []}

    pages = engine.list_pages()
    nodes = [{"id": p.name} for p in pages]

    links = []
    for page in pages:
        for target in engine.get_outlinks(page.name):
            links.append({"source": page.name, "target": target})

    return {"nodes": nodes, "links": links}


@app.websocket("/ws/graph")
async def ws_graph(websocket: WebSocket):
    """WebSocket endpoint for real-time graph events."""
    await websocket.accept()
    client_id, queue = manager.connect()
    try:
        while True:
            msg = await queue.get()
            await websocket.send_json(msg)
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(client_id)
