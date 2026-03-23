from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


def now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


class PaperCreateResponse(BaseModel):
    paper_id: str
    ingestion_status: str
    extraction_status: str


class PaperListItem(BaseModel):
    id: str
    title: Optional[str] = None
    publication_year: Optional[int] = None
    journal: Optional[str] = None
    doi: Optional[str] = None
    created_at: str
    ingestion_status: str
    extraction_status: str


class PaperDetail(PaperListItem):
    authors_json: Optional[str] = None
    abstract_text: Optional[str] = None
    file_path: str
    raw_text: Optional[str] = None


class ExtractRequest(BaseModel):
    mode: Literal["metadata_only", "full"] = "full"


class JobStatus(BaseModel):
    job_id: str
    status: Literal["queued", "running", "succeeded", "failed"]
    progress: float = Field(0.0, ge=0.0, le=1.0)
    error_text: Optional[str] = None


class ClaimItem(BaseModel):
    id: str
    paper_id: str
    claim_text: str
    claim_type: Optional[str] = None
    evidence_type: Optional[str] = None
    supporting_section_id: Optional[str] = None
    supporting_excerpt: Optional[str] = None
    overclaim_risk: Optional[str] = None
    confidence_score: Optional[float] = None
    review_status: str = "unreviewed"
    review_note: Optional[str] = None
    created_at: str


class ClaimPatch(BaseModel):
    review_status: Optional[Literal["unreviewed", "accepted", "disputed", "rejected"]] = None
    review_note: Optional[str] = None
    overclaim_risk: Optional[Literal["low", "medium", "high"]] = None
    confidence_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class MinimalExtractionResult(BaseModel):
    title: Optional[str] = None
    doi: Optional[str] = None
    publication_year: Optional[int] = None
    journal: Optional[str] = None
    abstract_text: Optional[str] = None
    # We keep authors_json as a string for now (can evolve to structured JSON later).
    authors_json: Optional[str] = None


class SectionItem(BaseModel):
    id: str
    paper_id: str
    section_type: Optional[str] = None
    section_heading: Optional[str] = None
    section_order: Optional[int] = None
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    text: Optional[str] = None
    created_at: str
