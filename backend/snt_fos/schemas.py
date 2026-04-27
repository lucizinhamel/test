"""Pydantic schemas exposed by the HTTP API. Decimal stays as Decimal in JSON
(serialized as string) to avoid float drift in tax math."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class EntityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    legal_name: str
    nif: Optional[str]
    country: str
    base_currency: str
    is_personal: bool
    is_holding: bool
    iva_regime: str
    active: bool


class TaxObligationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    entity_id: str
    entity_code: Optional[str] = None
    modelo: str
    name_es: str
    name_en: str
    legal_basis: Optional[str]
    period_kind: str
    period_label: str
    period_start: date
    period_end: date
    due_date: date
    direct_debit_due_date: Optional[date]
    payment_kind: str
    rate_hint: Optional[str]
    threshold_hint: Optional[str]
    reserve_pct_hint: Optional[Decimal]
    estimated_amount: Optional[Decimal]
    notes: Optional[str]
    status: str
    filed_at: Optional[datetime]
    paid_at: Optional[datetime]


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    sha256: str
    mime_type: str
    byte_size: int
    original_filename: str
    title: Optional[str]
    notes: Optional[str]
    uploaded_at: datetime
    uploaded_by: str


class DocumentLinkIn(BaseModel):
    target_type: str
    target_id: str
    role: Optional[str] = None
    notes: Optional[str] = None


class DocumentLinkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    target_type: str
    target_id: str
    role: Optional[str]
    notes: Optional[str]
    created_at: datetime
