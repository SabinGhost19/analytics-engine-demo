"""Analytics ingest API — accepts event batches, returns aggregates.

Kept intentionally tiny (FastAPI only) so the SBOM is bounded and the
image is mostly CVE-free relative to the Python base layer. Used as the
"Alert state" sample: Python base does carry some fix-able CVEs in
system libs (libc, openssl), and the SCA allows them with
`onVulnerabilityFound: Alert`.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="analytics-api", version="0.1.0")


class Event(BaseModel):
    kind: str
    value: float


class IngestRequest(BaseModel):
    events: list[Event]


class AggregateResponse(BaseModel):
    count: int
    sum: float
    received_at: str


@app.get("/health")
@app.get("/healthz")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "analytics-api"}


@app.post("/aggregate", response_model=AggregateResponse)
def aggregate(payload: IngestRequest) -> AggregateResponse:
    total = sum(event.value for event in payload.events)
    return AggregateResponse(
        count=len(payload.events),
        sum=total,
        received_at=datetime.now(timezone.utc).isoformat(),
    )


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8080")),
    )
