"""SCI LitLab backend wrapper.

This file keeps the original K-Dense BYOK app intact, but adds a new, narrow
API surface for SCI LitLab under /api.

Run with:
  uv run uvicorn server_sci_litlab:app --reload --port 8000

(Or use start_sci_litlab.sh)
"""

from server import app  # reuse the existing FastAPI app (health, sandbox, ADK agent)

from sci_litlab.api import router as sci_litlab_router

# Mount SCI LitLab routes under /api
app.include_router(sci_litlab_router, prefix="/api")
