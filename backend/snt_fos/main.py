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
from .ledger import (
    LedgerError,
    PostingInput,
    TransactionInput,
    create_draft,
    post_transaction,
    trial_balance as compute_trial_balance,
    void_transaction,
)
from .models import (
    Account,
    Counterparty,
    Document,
    DocumentLink,
    Entity,
    LedgerTransaction,
    Posting,
    TaxObligation,
)
from .schemas import (
    AccountOut,
    CounterpartyIn,
    CounterpartyOut,
    DocumentLinkIn,
    DocumentLinkOut,
    DocumentOut,
    EntityOut,
    PostingOut,
    TaxObligationOut,
    TransactionIn,
    TransactionOut,
    TrialBalanceRow,
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


# --- Accounts ----------------------------------------------------------------


@app.get("/api/accounts", response_model=list[AccountOut])
def list_accounts(
    entity_id: Optional[str] = None,
    group_code: Optional[str] = None,
    db: Session = Depends(get_session),
) -> list[Account]:
    q = db.query(Account).filter(Account.active == True)  # noqa: E712
    if entity_id:
        q = q.filter(Account.entity_id == entity_id)
    if group_code:
        q = q.filter(Account.group_code == group_code)
    return q.order_by(Account.entity_id, Account.sort_order, Account.code).all()


@app.get("/api/trial-balance", response_model=list[TrialBalanceRow])
def trial_balance(
    entity_id: str,
    as_of: Optional[date] = None,
    db: Session = Depends(get_session),
) -> list[dict]:
    return compute_trial_balance(db, entity_id, as_of=as_of)


# --- Counterparties ----------------------------------------------------------


@app.get("/api/counterparties", response_model=list[CounterpartyOut])
def list_counterparties(
    is_client: Optional[bool] = None,
    is_supplier: Optional[bool] = None,
    db: Session = Depends(get_session),
) -> list[Counterparty]:
    q = db.query(Counterparty).filter(Counterparty.active == True)  # noqa: E712
    if is_client is not None:
        q = q.filter(Counterparty.is_client == is_client)
    if is_supplier is not None:
        q = q.filter(Counterparty.is_supplier == is_supplier)
    return q.order_by(Counterparty.name).all()


@app.post("/api/counterparties", response_model=CounterpartyOut)
def create_counterparty(payload: CounterpartyIn, db: Session = Depends(get_session)) -> Counterparty:
    cp = Counterparty(**payload.model_dump())
    db.add(cp)
    db.commit()
    db.refresh(cp)
    return cp


@app.patch("/api/counterparties/{cp_id}", response_model=CounterpartyOut)
def update_counterparty(
    cp_id: str, payload: CounterpartyIn, db: Session = Depends(get_session)
) -> Counterparty:
    cp = db.get(Counterparty, cp_id)
    if cp is None:
        raise HTTPException(404, "not found")
    for k, v in payload.model_dump().items():
        setattr(cp, k, v)
    db.commit()
    db.refresh(cp)
    return cp


# --- Ledger transactions -----------------------------------------------------


def _serialize_transaction(tx: LedgerTransaction, db: Session) -> TransactionOut:
    # Pre-fetch account codes once
    account_ids = [p.account_id for p in tx.postings]
    accs = {a.id: a for a in db.query(Account).filter(Account.id.in_(account_ids)).all()} if account_ids else {}
    out = TransactionOut.model_validate(tx)
    ent = db.get(Entity, tx.entity_id)
    out.entity_code = ent.code if ent else None
    out.counterparty_name = tx.counterparty.name if tx.counterparty else None
    out.postings = []
    total = Decimal("0")
    for p in tx.postings:
        po = PostingOut.model_validate(p)
        a = accs.get(p.account_id)
        po.account_code = a.code if a else None
        po.account_name_es = a.name_es if a else None
        out.postings.append(po)
        total += p.debit
    out.total = total
    return out


@app.get("/api/transactions", response_model=list[TransactionOut])
def list_transactions(
    entity_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_session),
) -> list[TransactionOut]:
    q = db.query(LedgerTransaction)
    if entity_id:
        q = q.filter(LedgerTransaction.entity_id == entity_id)
    if status:
        q = q.filter(LedgerTransaction.status == status)
    q = q.order_by(LedgerTransaction.txn_date.desc(), LedgerTransaction.created_at.desc()).limit(limit)
    return [_serialize_transaction(tx, db) for tx in q.all()]


@app.get("/api/transactions/{tx_id}", response_model=TransactionOut)
def get_transaction(tx_id: str, db: Session = Depends(get_session)) -> TransactionOut:
    tx = db.get(LedgerTransaction, tx_id)
    if tx is None:
        raise HTTPException(404, "not found")
    return _serialize_transaction(tx, db)


@app.post("/api/transactions", response_model=TransactionOut)
def create_transaction(payload: TransactionIn, db: Session = Depends(get_session)) -> TransactionOut:
    try:
        tx = create_draft(
            db,
            TransactionInput(
                entity_id=payload.entity_id,
                txn_date=payload.txn_date,
                description=payload.description,
                postings=[
                    PostingInput(
                        account_code=p.account_code,
                        debit=p.debit,
                        credit=p.credit,
                        description=p.description,
                        iva_code=p.iva_code,
                        iva_rate=p.iva_rate,
                        iva_amount=p.iva_amount,
                        retention_code=p.retention_code,
                        retention_amount=p.retention_amount,
                    )
                    for p in payload.postings
                ],
                currency=payload.currency,
                fx_rate_to_base=payload.fx_rate_to_base,
                counterparty_id=payload.counterparty_id,
                reference_type=payload.reference_type,
                reference_id=payload.reference_id,
                project_tag=payload.project_tag,
                brand_tag=payload.brand_tag,
                value_date=payload.value_date,
            ),
        )
    except LedgerError as e:
        raise HTTPException(400, str(e))
    return _serialize_transaction(tx, db)


@app.post("/api/transactions/{tx_id}/post", response_model=TransactionOut)
def post_tx(tx_id: str, db: Session = Depends(get_session)) -> TransactionOut:
    try:
        tx = post_transaction(db, tx_id)
    except LedgerError as e:
        raise HTTPException(400, str(e))
    return _serialize_transaction(tx, db)


@app.post("/api/transactions/{tx_id}/void", response_model=TransactionOut)
def void_tx(tx_id: str, db: Session = Depends(get_session)) -> TransactionOut:
    try:
        tx = void_transaction(db, tx_id)
    except LedgerError as e:
        raise HTTPException(400, str(e))
    return _serialize_transaction(tx, db)


# Ensure Decimal import is in scope for _serialize_transaction
from decimal import Decimal  # noqa: E402
