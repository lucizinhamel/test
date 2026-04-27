"""Ledger domain logic. Centralizes the double-entry invariants so the API
and any future importers all enforce the same rules.

Invariants enforced here:
  1. Sum of debits equals sum of credits per transaction (in base currency).
  2. Each posting is one-sided: either debit OR credit nonzero, not both.
  3. Posted transactions are immutable. Any "edit" must be a new correcting
     transaction that references the original via reference_type='correction'.
  4. Accounts must belong to the same entity as the transaction.
  5. Postable=False accounts cannot receive postings.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

from sqlalchemy.orm import Session

from .models import Account, Entity, LedgerTransaction, Posting

CENT = Decimal("0.01")


def _q2(x: Decimal) -> Decimal:
    return x.quantize(CENT, rounding=ROUND_HALF_UP)


@dataclass
class PostingInput:
    account_code: str
    debit: Decimal = Decimal("0")
    credit: Decimal = Decimal("0")
    description: Optional[str] = None
    iva_code: Optional[str] = None
    iva_rate: Optional[Decimal] = None
    iva_amount: Optional[Decimal] = None
    retention_code: Optional[str] = None
    retention_amount: Optional[Decimal] = None


@dataclass
class TransactionInput:
    entity_id: str
    txn_date: date
    description: str
    postings: list[PostingInput]
    currency: str = "EUR"
    fx_rate_to_base: Decimal = Decimal("1")
    counterparty_id: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    project_tag: Optional[str] = None
    brand_tag: Optional[str] = None
    value_date: Optional[date] = None


class LedgerError(ValueError):
    pass


def _resolve_account(db: Session, entity_id: str, code: str) -> Account:
    acc = db.query(Account).filter_by(entity_id=entity_id, code=code).one_or_none()
    if acc is None:
        raise LedgerError(f"account '{code}' not found for entity {entity_id}")
    if not acc.is_postable:
        raise LedgerError(f"account '{code}' is not postable")
    if not acc.active:
        raise LedgerError(f"account '{code}' is inactive")
    return acc


def _validate_balance(postings: list[PostingInput]) -> None:
    if len(postings) < 2:
        raise LedgerError("a transaction must have at least 2 postings")
    total_d = sum((_q2(p.debit) for p in postings), Decimal("0"))
    total_c = sum((_q2(p.credit) for p in postings), Decimal("0"))
    if total_d != total_c:
        raise LedgerError(
            f"unbalanced: debits={total_d} credits={total_c} (must be equal in base ccy)"
        )
    if total_d == 0:
        raise LedgerError("transaction has zero total — empty entry")
    for i, p in enumerate(postings):
        d, c = _q2(p.debit), _q2(p.credit)
        if d < 0 or c < 0:
            raise LedgerError(f"line {i + 1}: negative amounts not allowed")
        if d > 0 and c > 0:
            raise LedgerError(f"line {i + 1}: a posting cannot be both debit AND credit")
        if d == 0 and c == 0:
            raise LedgerError(f"line {i + 1}: posting has neither debit nor credit")


def create_draft(db: Session, payload: TransactionInput) -> LedgerTransaction:
    ent = db.get(Entity, payload.entity_id)
    if ent is None:
        raise LedgerError(f"entity {payload.entity_id} not found")
    _validate_balance(payload.postings)

    fx = payload.fx_rate_to_base if payload.currency == ent.base_currency else payload.fx_rate_to_base
    if fx <= 0:
        raise LedgerError("fx_rate_to_base must be positive")

    tx = LedgerTransaction(
        entity_id=ent.id,
        txn_date=payload.txn_date,
        value_date=payload.value_date,
        description=payload.description,
        currency=payload.currency,
        fx_rate_to_base=fx,
        counterparty_id=payload.counterparty_id,
        reference_type=payload.reference_type,
        reference_id=payload.reference_id,
        project_tag=payload.project_tag,
        brand_tag=payload.brand_tag,
        status="draft",
    )
    db.add(tx)
    db.flush()

    for i, p in enumerate(payload.postings, start=1):
        acc = _resolve_account(db, ent.id, p.account_code)
        d_base, c_base = _q2(p.debit), _q2(p.credit)
        # transaction-currency amounts: if txn is in base ccy, equal to base.
        # Otherwise the caller has already converted; we store both for trail.
        d_ccy = (d_base / fx).quantize(CENT, rounding=ROUND_HALF_UP) if fx != 1 else d_base
        c_ccy = (c_base / fx).quantize(CENT, rounding=ROUND_HALF_UP) if fx != 1 else c_base
        db.add(
            Posting(
                transaction_id=tx.id,
                line_no=i,
                account_id=acc.id,
                debit=d_base,
                credit=c_base,
                debit_ccy=d_ccy,
                credit_ccy=c_ccy,
                iva_code=p.iva_code,
                iva_rate=p.iva_rate,
                iva_amount=p.iva_amount,
                retention_code=p.retention_code,
                retention_amount=p.retention_amount,
                description_override=p.description,
            )
        )
    db.commit()
    db.refresh(tx)
    return tx


def post_transaction(db: Session, tx_id: str, by: str = "founder") -> LedgerTransaction:
    tx = db.get(LedgerTransaction, tx_id)
    if tx is None:
        raise LedgerError("transaction not found")
    if tx.status != "draft":
        raise LedgerError(f"can only post draft transactions, status='{tx.status}'")
    # Re-verify balance from persisted postings
    total_d = sum((_q2(p.debit) for p in tx.postings), Decimal("0"))
    total_c = sum((_q2(p.credit) for p in tx.postings), Decimal("0"))
    if total_d != total_c or total_d == 0:
        raise LedgerError(f"cannot post: unbalanced ({total_d} vs {total_c})")
    tx.status = "posted"
    tx.posted_at = datetime.now(timezone.utc)
    tx.posted_by = by
    db.commit()
    db.refresh(tx)
    return tx


def void_transaction(db: Session, tx_id: str) -> LedgerTransaction:
    tx = db.get(LedgerTransaction, tx_id)
    if tx is None:
        raise LedgerError("transaction not found")
    if tx.status != "draft":
        raise LedgerError("only draft transactions can be voided directly; "
                          "post a correcting entry to reverse a posted one")
    tx.status = "void"
    db.commit()
    db.refresh(tx)
    return tx


def account_balance(db: Session, account_id: str, as_of: Optional[date] = None) -> dict:
    """Sum debits & credits on an account (posted transactions only)."""
    q = (
        db.query(Posting)
        .join(LedgerTransaction, Posting.transaction_id == LedgerTransaction.id)
        .filter(Posting.account_id == account_id)
        .filter(LedgerTransaction.status == "posted")
    )
    if as_of is not None:
        q = q.filter(LedgerTransaction.txn_date <= as_of)
    debits = sum((_q2(p.debit) for p in q.all()), Decimal("0"))
    q2 = (
        db.query(Posting)
        .join(LedgerTransaction, Posting.transaction_id == LedgerTransaction.id)
        .filter(Posting.account_id == account_id)
        .filter(LedgerTransaction.status == "posted")
    )
    if as_of is not None:
        q2 = q2.filter(LedgerTransaction.txn_date <= as_of)
    credits = sum((_q2(p.credit) for p in q2.all()), Decimal("0"))
    return {"debits": debits, "credits": credits, "balance": debits - credits}


def trial_balance(db: Session, entity_id: str, as_of: Optional[date] = None) -> list[dict]:
    accounts = (
        db.query(Account)
        .filter_by(entity_id=entity_id, active=True)
        .order_by(Account.code)
        .all()
    )
    out = []
    for a in accounts:
        b = account_balance(db, a.id, as_of=as_of)
        if b["debits"] == 0 and b["credits"] == 0:
            continue
        natural = b["balance"] if a.nature == "debit" else -b["balance"]
        out.append(
            {
                "account_id": a.id,
                "code": a.code,
                "name_es": a.name_es,
                "name_en": a.name_en,
                "group_code": a.group_code,
                "nature": a.nature,
                "debits": b["debits"],
                "credits": b["credits"],
                "balance": b["balance"],
                "natural_balance": natural,
            }
        )
    return out
