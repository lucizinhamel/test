from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
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
