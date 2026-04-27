from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def _ulid() -> str:
    return uuid.uuid4().hex


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Entity(Base):
    """Legal entity. One row per company; one row for the founder's personal book."""

    __tablename__ = "entity"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_ulid)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    nif: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    country: Mapped[str] = mapped_column(String(2), default="ES", nullable=False)
    base_currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)
    fiscal_year_start_month: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    iva_regime: Mapped[str] = mapped_column(String(32), default="general", nullable=False)
    is_personal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_holding: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    parent_entity_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("entity.id"), nullable=True
    )
    ownership_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(7, 4), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )


class TaxObligation(Base):
    """A scheduled Spanish tax filing/payment for an entity in a fiscal period.

    These rows are generated from the canonical tax calendar (see seed module).
    Each row represents one filing (one Modelo for one period for one entity).
    """

    __tablename__ = "tax_obligation"
    __table_args__ = (
        UniqueConstraint(
            "entity_id", "modelo", "period_label", name="uq_tax_obligation_entity_modelo_period"
        ),
        Index("ix_tax_obligation_due_date", "due_date"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_ulid)
    entity_id: Mapped[str] = mapped_column(ForeignKey("entity.id"), nullable=False)
    modelo: Mapped[str] = mapped_column(String(16), nullable=False)  # e.g. "303", "200"
    name_es: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    legal_basis: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    period_kind: Mapped[str] = mapped_column(String(16), nullable=False)  # monthly/quarterly/annual
    period_label: Mapped[str] = mapped_column(String(32), nullable=False)  # e.g. "2026-Q2"
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    direct_debit_due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    payment_kind: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # informational / withheld / self_assessed / advance_payment
    rate_hint: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )  # e.g. "21% / 10% / 4% / 0%" or "25% IS"
    threshold_hint: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )  # e.g. ">€3,005.06 with same counterparty"
    reserve_pct_hint: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2), nullable=True
    )  # what % of base to mentally reserve
    estimated_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )  # auto-computed once books exist; null in MVP
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(16), default="upcoming", nullable=False
    )  # upcoming / in_prep / filed / paid / na
    filed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )

    entity = relationship("Entity")


class Document(Base):
    """Content-addressable document store. One row per unique file (by sha256)."""

    __tablename__ = "document"
    __table_args__ = (Index("ix_document_uploaded_at", "uploaded_at"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_ulid)
    sha256: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    uploaded_by: Mapped[str] = mapped_column(String(64), default="founder", nullable=False)


class Counterparty(Base):
    """Master record for a client or supplier. Shared across entities so 347/349
    aggregation and consolidated views work."""

    __tablename__ = "counterparty"
    __table_args__ = (
        Index("ix_counterparty_tax_id", "tax_id"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_ulid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    legal_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    tax_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    tax_id_country: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    country: Mapped[str] = mapped_column(String(2), default="ES", nullable=False)
    address_line1: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    default_payment_terms_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    default_iva_treatment: Mapped[str] = mapped_column(
        String(32), default="general_21", nullable=False
    )
    # general_21 / reduced_10 / super_reduced_4 / exempt / intracom_reverse_charge / export_exempt
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_client: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_supplier: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )


class Account(Base):
    """Chart of accounts entry, scoped per entity. Default seed = Spanish PGC."""

    __tablename__ = "account"
    __table_args__ = (
        UniqueConstraint("entity_id", "code", name="uq_account_entity_code"),
        Index("ix_account_entity_group", "entity_id", "group_code"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_ulid)
    entity_id: Mapped[str] = mapped_column(ForeignKey("entity.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(16), nullable=False)
    name_es: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    group_code: Mapped[str] = mapped_column(String(8), nullable=False)  # "1".."9" or "PERSONAL_*"
    parent_account_code: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    nature: Mapped[str] = mapped_column(String(8), nullable=False)  # "debit" / "credit"
    is_postable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    iva_rate_default: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    deductibility_default: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )


class LedgerTransaction(Base):
    """Journal entry header. Sum of debits == sum of credits in base currency
    is enforced when status moves to 'posted'."""

    __tablename__ = "ledger_transaction"
    __table_args__ = (
        Index("ix_ledger_transaction_entity_date", "entity_id", "txn_date"),
        Index("ix_ledger_transaction_status", "status"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_ulid)
    entity_id: Mapped[str] = mapped_column(ForeignKey("entity.id"), nullable=False)
    txn_date: Mapped[date] = mapped_column(Date, nullable=False)
    value_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    description: Mapped[str] = mapped_column(String(512), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)
    fx_rate_to_base: Mapped[Decimal] = mapped_column(
        Numeric(18, 8), default=Decimal("1"), nullable=False
    )
    counterparty_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("counterparty.id"), nullable=True
    )
    reference_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    # invoice_issued / invoice_received / bank / lc_milestone / manual / intercompany / correction
    reference_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    intercompany_pair_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    project_tag: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    brand_tag: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="draft", nullable=False)
    # draft / posted / void
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    posted_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )

    counterparty = relationship("Counterparty")
    postings = relationship(
        "Posting", back_populates="transaction", cascade="all, delete-orphan", order_by="Posting.line_no"
    )


class Posting(Base):
    """Single debit-or-credit line of a journal entry. Both debit and credit
    are stored in the entity's base currency; debit_ccy/credit_ccy hold the
    transaction-currency amounts (equal to base when fx_rate=1)."""

    __tablename__ = "posting"
    __table_args__ = (
        CheckConstraint("debit >= 0 AND credit >= 0", name="ck_posting_nonneg"),
        CheckConstraint(
            "(debit > 0 AND credit = 0) OR (credit > 0 AND debit = 0) OR (debit = 0 AND credit = 0)",
            name="ck_posting_one_side",
        ),
        Index("ix_posting_account", "account_id"),
        Index("ix_posting_transaction", "transaction_id"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_ulid)
    transaction_id: Mapped[str] = mapped_column(
        ForeignKey("ledger_transaction.id", ondelete="CASCADE"), nullable=False
    )
    line_no: Mapped[int] = mapped_column(Integer, nullable=False)
    account_id: Mapped[str] = mapped_column(ForeignKey("account.id"), nullable=False)
    debit: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"), nullable=False)
    credit: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"), nullable=False)
    debit_ccy: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"), nullable=False)
    credit_ccy: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"), nullable=False)
    iva_code: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    iva_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    iva_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    retention_code: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    retention_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    description_override: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    transaction = relationship("LedgerTransaction", back_populates="postings")
    account = relationship("Account")


class DocumentLink(Base):
    """Polymorphic link between a Document and any other entity (tax_obligation, transaction, ...)."""

    __tablename__ = "document_link"
    __table_args__ = (
        Index("ix_document_link_target", "target_type", "target_id"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_ulid)
    document_id: Mapped[str] = mapped_column(ForeignKey("document.id"), nullable=False)
    target_type: Mapped[str] = mapped_column(String(64), nullable=False)
    target_id: Mapped[str] = mapped_column(String(64), nullable=False)
    role: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )  # receipt / invoice_pdf / dua / bol / proof_of_filing / other
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    document = relationship("Document")
