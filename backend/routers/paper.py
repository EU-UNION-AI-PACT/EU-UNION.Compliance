"""Concept paper CRUD + full-text search."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from database import get_db
from models import PaperChapter, PaperSearchResult

router = APIRouter(prefix="/paper", tags=["Concept Paper"])


@router.get("/chapters", response_model=list[PaperChapter])
async def list_chapters() -> list[PaperChapter]:
    cur = get_db().paper_chapters.find({}, {"_id": 0}).sort("number", 1)
    docs = await cur.to_list(50)
    return [PaperChapter(**d) for d in docs]


@router.get("/chapters/{slug}", response_model=PaperChapter)
async def get_chapter(slug: str) -> PaperChapter:
    doc = await get_db().paper_chapters.find_one({"slug": slug}, {"_id": 0})
    if not doc:
        raise HTTPException(404, f"chapter {slug} not found")
    return PaperChapter(**doc)


@router.get("/search", response_model=list[PaperSearchResult])
async def search_chapters(q: str = Query(..., min_length=2)) -> list[PaperSearchResult]:
    cur = (
        get_db()
        .paper_chapters.find(
            {"$text": {"$search": q}},
            {"_id": 0, "slug": 1, "number": 1, "title": 1, "body": 1, "score": {"$meta": "textScore"}},
        )
        .sort([("score", {"$meta": "textScore"})])
        .limit(10)
    )
    results = []
    async for d in cur:
        body: str = d.get("body", "")
        idx = body.lower().find(q.lower())
        start = max(0, idx - 40) if idx >= 0 else 0
        excerpt = body[start : start + 200].strip() + "…"
        results.append(
            PaperSearchResult(
                slug=d["slug"],
                number=d["number"],
                title=d["title"],
                excerpt=excerpt,
                score=d.get("score", 0.0),
            )
        )
    return results
