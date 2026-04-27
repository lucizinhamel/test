from __future__ import annotations

import mimetypes
from contextlib import asynccontextmanager
from datetime import date, timedelta
from typing import Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .db import get_session
from .models import Document, DocumentLink, Entity, TaxObligation
from .schemas import (
    DocumentLinkIn,
    DocumentLinkOut,
    DocumentOut,
    EntityOut,
    TaxObligationOut,
)
from .seed.bootstrap import bootstrap
from .storage import open_for_read, store_stream


@asynccontextmanager
async def lifespan(_app: FastAPI):
    bootstrap()
    yield


app = FastAPI(title="SNT-FOS API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


@app.get("/api/entities", response_model=list[EntityOut])
def list_entities(db: Session = Depends(get_session)) -> list[Entity]:
    return db.query(Entity).filter_by(active=True).order_by(Entity.code).all()


@app.get("/api/tax-calendar", response_model=list[TaxObligationOut])
def list_tax_obligations(
    entity_id: Optional[str] = None,
    upcoming_days: Optional[int] = None,
    include_past_days: int = 30,
    status: Optional[str] = None,
    modelo: Optional[str] = None,
    db: Session = Depends(get_session),
) -> list[TaxObligationOut]:
    """Tax calendar entries.

    By default returns the rolling window: from `today - include_past_days` to
    `today + upcoming_days` (no upper bound if `upcoming_days` is None).
    """
    q = db.query(TaxObligation, Entity).join(Entity, TaxObligation.entity_id == Entity.id)
    if entity_id:
        q = q.filter(TaxObligation.entity_id == entity_id)
    if status:
        q = q.filter(TaxObligation.status == status)
    if modelo:
        q = q.filter(TaxObligation.modelo == modelo)

    today = date.today()
    if include_past_days is not None:
        q = q.filter(TaxObligation.due_date >= today - timedelta(days=include_past_days))
    if upcoming_days is not None:
        q = q.filter(TaxObligation.due_date <= today + timedelta(days=upcoming_days))

    rows = q.order_by(TaxObligation.due_date.asc()).all()
    out: list[TaxObligationOut] = []
    for tax, ent in rows:
        item = TaxObligationOut.model_validate(tax)
        item.entity_code = ent.code
        out.append(item)
    return out


@app.patch("/api/tax-calendar/{obligation_id}/status", response_model=TaxObligationOut)
def update_obligation_status(
    obligation_id: str, status: str = Form(...), db: Session = Depends(get_session)
) -> TaxObligationOut:
    if status not in {"upcoming", "in_prep", "filed", "paid", "na"}:
        raise HTTPException(400, "invalid status")
    obj = db.get(TaxObligation, obligation_id)
    if obj is None:
        raise HTTPException(404, "not found")
    obj.status = status
    db.commit()
    db.refresh(obj)
    return TaxObligationOut.model_validate(obj)


# --- Documents ---------------------------------------------------------------


@app.post("/api/documents", response_model=DocumentOut)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_session),
) -> DocumentOut:
    sha, size, _ = store_stream(file.file)
    existing = db.query(Document).filter_by(sha256=sha).one_or_none()
    if existing is not None:
        return DocumentOut.model_validate(existing)

    mime = file.content_type or mimetypes.guess_type(file.filename or "")[0] or "application/octet-stream"
    doc = Document(
        sha256=sha,
        mime_type=mime,
        byte_size=size,
        original_filename=file.filename or "unnamed",
        stored_path=str(open_for_read(sha)),
        title=title,
        notes=notes,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return DocumentOut.model_validate(doc)


@app.get("/api/documents", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_session)) -> list[Document]:
    return db.query(Document).order_by(Document.uploaded_at.desc()).all()


@app.get("/api/documents/{document_id}/download")
def download_document(document_id: str, db: Session = Depends(get_session)) -> FileResponse:
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(404, "not found")
    return FileResponse(
        path=doc.stored_path,
        media_type=doc.mime_type,
        filename=doc.original_filename,
    )


@app.post("/api/documents/{document_id}/links", response_model=DocumentLinkOut)
def link_document(
    document_id: str, payload: DocumentLinkIn, db: Session = Depends(get_session)
) -> DocumentLinkOut:
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(404, "document not found")
    link = DocumentLink(
        document_id=document_id,
        target_type=payload.target_type,
        target_id=payload.target_id,
        role=payload.role,
        notes=payload.notes,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return DocumentLinkOut.model_validate(link)


@app.get("/api/documents/links", response_model=list[DocumentLinkOut])
def list_links(
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    db: Session = Depends(get_session),
) -> list[DocumentLink]:
    q = db.query(DocumentLink)
    if target_type:
        q = q.filter(DocumentLink.target_type == target_type)
    if target_id:
        q = q.filter(DocumentLink.target_id == target_id)
    return q.order_by(DocumentLink.created_at.desc()).all()
