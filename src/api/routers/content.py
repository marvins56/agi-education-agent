"""Content upload and search endpoints (stubs for Phase 1)."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/upload")
async def upload_content():
    """Upload educational content (stub)."""
    return {"status": "not_implemented", "message": "Content upload coming in Phase 2"}


@router.get("/search")
async def search_content(q: str = ""):
    """Search knowledge base (stub)."""
    return {"query": q, "results": []}
