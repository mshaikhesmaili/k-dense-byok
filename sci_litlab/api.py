from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, UploadFile

from sci_litlab.extraction import extract_text_from_file, naive_split_into_sections
from sci_litlab.models import (
    ClaimItem,
    ClaimPatch,
    PaperCreateResponse,
    PaperDetail,
    PaperListItem,
)
from sci_litlab.store import (
    create_paper,
    delete_paper,
    get_paper,
    list_claims,
    list_papers,
    list_sections,
    patch_claim,
    update_paper_fields,
    upsert_sections,
)

router = APIRouter(tags=["sci_litlab"])

SANDBOX_ROOT = Path("sandbox").resolve()
UPLOAD_DIR = SANDBOX_ROOT / "sci_litlab" / "papers"


@router.get("/health")
def litlab_health():
    return {"status": "ok", "service": "sci_litlab"}


@router.post("/papers/upload", response_model=PaperCreateResponse)
async def upload_paper(file: UploadFile):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename).name
    if not safe_name:
        raise HTTPException(status_code=400, detail="Bad filename")

    # Store under a UUID folder to avoid collisions
    tmp_path = UPLOAD_DIR / safe_name
    content = await file.read()
    tmp_path.write_bytes(content)

    paper_id = create_paper(str(tmp_path.relative_to(SANDBOX_ROOT)))

    return PaperCreateResponse(
        paper_id=paper_id,
        ingestion_status="uploaded",
        extraction_status="pending",
    )


@router.get("/papers", response_model=list[PaperListItem])
def papers(q: Optional[str] = Query(default=None), limit: int = 50, offset: int = 0):
    return list_papers(q=q, limit=limit, offset=offset)


@router.get("/papers/{paper_id}", response_model=PaperDetail)
def paper_detail(paper_id: str):
    p = get_paper(paper_id)
    if not p:
        raise HTTPException(status_code=404, detail="Paper not found")
    return p


@router.delete("/papers/{paper_id}")
def paper_delete(paper_id: str):
    p = get_paper(paper_id)
    if not p:
        raise HTTPException(status_code=404, detail="Paper not found")
    delete_paper(paper_id)
    return {"deleted": paper_id}


@router.post("/papers/{paper_id}/extract")
def paper_extract(paper_id: str):
    """Run minimal extraction synchronously for MVP.

    - Extract markdown-like text from the PDF.
    - Naively split into sections.

    Later: move to async jobs + structured extraction.
    """
    p = get_paper(paper_id)
    if not p:
        raise HTTPException(status_code=404, detail="Paper not found")

    rel_path = p.get("file_path")
    if not rel_path:
        raise HTTPException(status_code=400, detail="Paper has no file_path")

    abs_path = (SANDBOX_ROOT / rel_path).resolve()
    if not abs_path.is_file():
        raise HTTPException(status_code=404, detail="Stored PDF not found")

    try:
        raw_text = extract_text_from_file(str(abs_path))
    except Exception as e:
        update_paper_fields(paper_id, {"extraction_status": "failed"})
        raise HTTPException(status_code=500, detail=f"Extraction failed: {e}")

    update_paper_fields(paper_id, {"raw_text": raw_text, "extraction_status": "extracted"})

    # Sections
    sections = naive_split_into_sections(raw_text)
    upsert_sections(
        paper_id,
        [
            {
                "section_type": s.section_type,
                "section_heading": s.heading,
                "section_order": s.order,
                "page_start": None,
                "page_end": None,
                "text": s.text,
            }
            for s in sections
        ],
    )

    return {
        "paper_id": paper_id,
        "extraction_status": "extracted",
        "sections": len(sections),
    }


@router.get("/papers/{paper_id}/sections")
def paper_sections(paper_id: str):
    p = get_paper(paper_id)
    if not p:
        raise HTTPException(status_code=404, detail="Paper not found")
    return list_sections(paper_id)


@router.get("/papers/{paper_id}/fulltext")
def paper_fulltext(paper_id: str):
    p = get_paper(paper_id)
    if not p:
        raise HTTPException(status_code=404, detail="Paper not found")
    return {"paper_id": paper_id, "raw_text": p.get("raw_text") or ""}


@router.get("/papers/{paper_id}/claims", response_model=list[ClaimItem])
def paper_claims(paper_id: str):
    p = get_paper(paper_id)
    if not p:
        raise HTTPException(status_code=404, detail="Paper not found")
    return list_claims(paper_id)


@router.patch("/papers/{paper_id}/claims/{claim_id}", response_model=ClaimItem)
def claim_patch(paper_id: str, claim_id: str, patch: ClaimPatch):
    p = get_paper(paper_id)
    if not p:
        raise HTTPException(status_code=404, detail="Paper not found")

    updated = patch_claim(paper_id, claim_id, patch.model_dump())
    if not updated:
        raise HTTPException(status_code=404, detail="Claim not found")
    return updated
