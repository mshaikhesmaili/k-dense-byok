# SCI LitLab (MVP) — running inside K-Dense BYOK

This branch adds a narrow, citation-grounded literature workspace API **without** removing the original Kady agent.

## What you get in this MVP

- Upload PDFs into the local sandbox
- Store papers in a local SQLite DB (`sandbox/sci_litlab.db`)
- Extract text from PDFs via `markitdown`
- Naively split text into Markdown-heading sections (for stable anchors)
- List papers, view full text, view sections
- Claim review endpoints (CRUD-lite; extraction is stubbed)

## Start

```bash
./start_sci_litlab.sh
```

Then verify:

- UI: http://localhost:3000
- API health: http://localhost:8000/api/health

## Key endpoints

- `POST /api/papers/upload` (multipart form file)
- `POST /api/papers/{paper_id}/extract`
- `GET /api/papers`
- `GET /api/papers/{paper_id}`
- `GET /api/papers/{paper_id}/fulltext`
- `GET /api/papers/{paper_id}/sections`
- `GET /api/papers/{paper_id}/claims`
- `PATCH /api/papers/{paper_id}/claims/{claim_id}`

## Notes

- This is intentionally minimal and synchronous. Next steps are:
  1) async jobs table + background worker
  2) structured metadata extraction + citations (value + excerpt)
  3) UI pages for Library and Paper Detail that call these endpoints
