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


# === Ledger ===================================================================


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    entity_id: str
    code: str
    name_es: str
    name_en: str
    group_code: str
    nature: str
    is_postable: bool
    iva_rate_default: Optional[Decimal]
    active: bool
    sort_order: int


class CounterpartyIn(BaseModel):
    name: str
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None
    tax_id_country: Optional[str] = None
    country: str = "ES"
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    default_payment_terms_days: Optional[int] = None
    default_iva_treatment: str = "general_21"
    email: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None
    is_client: bool = False
    is_supplier: bool = False


class CounterpartyOut(CounterpartyIn):
    model_config = ConfigDict(from_attributes=True)

    id: str
    active: bool
    created_at: datetime


class PostingIn(BaseModel):
    account_code: str
    debit: Decimal = Decimal("0")
    credit: Decimal = Decimal("0")
    description: Optional[str] = None
    iva_code: Optional[str] = None
    iva_rate: Optional[Decimal] = None
    iva_amount: Optional[Decimal] = None
    retention_code: Optional[str] = None
    retention_amount: Optional[Decimal] = None


class PostingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    line_no: int
    account_id: str
    account_code: Optional[str] = None
    account_name_es: Optional[str] = None
    debit: Decimal
    credit: Decimal
    debit_ccy: Decimal
    credit_ccy: Decimal
    iva_code: Optional[str]
    iva_rate: Optional[Decimal]
    iva_amount: Optional[Decimal]
    retention_code: Optional[str]
    retention_amount: Optional[Decimal]
    description_override: Optional[str]


class TransactionIn(BaseModel):
    entity_id: str
    txn_date: date
    description: str
    postings: list[PostingIn]
    currency: str = "EUR"
    fx_rate_to_base: Decimal = Decimal("1")
    counterparty_id: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    project_tag: Optional[str] = None
    brand_tag: Optional[str] = None
    value_date: Optional[date] = None


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    entity_id: str
    entity_code: Optional[str] = None
    txn_date: date
    value_date: Optional[date]
    description: str
    currency: str
    fx_rate_to_base: Decimal
    counterparty_id: Optional[str]
    counterparty_name: Optional[str] = None
    reference_type: Optional[str]
    reference_id: Optional[str]
    project_tag: Optional[str]
    brand_tag: Optional[str]
    status: str
    posted_at: Optional[datetime]
    posted_by: Optional[str]
    created_at: datetime
    total: Decimal = Decimal("0")
    postings: list[PostingOut] = []


class TrialBalanceRow(BaseModel):
    account_id: str
    code: str
    name_es: str
    name_en: str
    group_code: str
    nature: str
    debits: Decimal
    credits: Decimal
    balance: Decimal
    natural_balance: Decimal
