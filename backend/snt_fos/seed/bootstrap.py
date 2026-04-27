"""Idempotent DB bootstrap: creates entities (founder's known set) and seeds
the tax calendar for the relevant fiscal years.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from ..db import Base, SessionLocal, engine
from ..models import Account, Entity, TaxObligation
from .spanish_pgc import coa_for_personal, pgc_for_sl
from .spanish_tax_calendar import calendar_for_personal, calendar_for_sl

# Initial entity set. Subsidiaries marked inactive=False until the founder
# confirms which are incorporated (see open question Q17 in design doc).
DEFAULT_ENTITIES = [
    {
        "code": "SNT",
        "legal_name": "SNT Holdings SL",
        "country": "ES",
        "is_holding": True,
        "is_personal": False,
        "iva_regime": "general",
        "active": True,
    },
    {
        "code": "COWFY",
        "legal_name": "Cowfy SL",
        "country": "ES",
        "is_holding": False,
        "is_personal": False,
        "iva_regime": "general",
        "active": True,
    },
    {
        "code": "PERSONAL",
        "legal_name": "Personal — Founder",
        "country": "ES",
        "is_holding": False,
        "is_personal": True,
        "iva_regime": "none_personal",
        "active": True,
    },
]

# Years to seed: FY of last year (annuals fall due THIS year) + current FY.
SEED_YEARS = [2025, 2026]


def _ensure_entities(db: Session) -> dict[str, Entity]:
    out: dict[str, Entity] = {}
    for spec in DEFAULT_ENTITIES:
        ent = db.query(Entity).filter_by(code=spec["code"]).one_or_none()
        if ent is None:
            ent = Entity(**spec)
            db.add(ent)
            db.flush()
        out[spec["code"]] = ent
    db.commit()
    return out


def _seed_obligations_for(db: Session, entity: Entity, year: int) -> int:
    if entity.is_personal:
        specs = calendar_for_personal(year)
    else:
        # Default assumption: SL with intracom operations (so 349 included).
        # Founder can later toggle this off per entity.
        specs = calendar_for_sl(year, has_intracom=True)

    inserted = 0
    for s in specs:
        exists = (
            db.query(TaxObligation)
            .filter_by(entity_id=entity.id, modelo=s.modelo, period_label=s.period_label)
            .one_or_none()
        )
        if exists:
            continue
        db.add(
            TaxObligation(
                entity_id=entity.id,
                modelo=s.modelo,
                name_es=s.name_es,
                name_en=s.name_en,
                legal_basis=s.legal_basis,
                period_kind=s.period_kind,
                period_label=s.period_label,
                period_start=s.period_start,
                period_end=s.period_end,
                due_date=s.due_date,
                direct_debit_due_date=s.direct_debit_due_date,
                payment_kind=s.payment_kind,
                rate_hint=s.rate_hint,
                threshold_hint=s.threshold_hint,
                reserve_pct_hint=s.reserve_pct_hint,
                notes=s.notes,
                status="upcoming",
            )
        )
        inserted += 1
    db.commit()
    return inserted


def _seed_accounts_for(db: Session, entity: Entity) -> int:
    rows = coa_for_personal() if entity.is_personal else pgc_for_sl()
    inserted = 0
    for r in rows:
        exists = (
            db.query(Account).filter_by(entity_id=entity.id, code=r["code"]).one_or_none()
        )
        if exists:
            continue
        db.add(Account(entity_id=entity.id, **r))
        inserted += 1
    db.commit()
    return inserted


def bootstrap() -> dict:
    """Create tables, seed entities, chart of accounts, and tax calendar. Idempotent."""
    Base.metadata.create_all(bind=engine)
    summary = {"entities": [], "obligations_inserted": 0, "accounts_inserted": 0}
    with SessionLocal() as db:
        entities = _ensure_entities(db)
        for code, ent in entities.items():
            summary["accounts_inserted"] += _seed_accounts_for(db, ent)
            for year in SEED_YEARS:
                n = _seed_obligations_for(db, ent, year)
                summary["obligations_inserted"] += n
            summary["entities"].append(code)
    return summary


if __name__ == "__main__":
    s = bootstrap()
    print(s)
