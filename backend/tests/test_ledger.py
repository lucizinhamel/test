"""Ledger invariants — these are the financial-correctness tests that must
NEVER regress. If any of these fails, the books are wrong."""

from __future__ import annotations

import os
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def db():
    # isolated DB per test module
    test_dir = Path("/tmp/snt-fos-test-ledger")
    if test_dir.exists():
        import shutil

        shutil.rmtree(test_dir)
    os.environ["SNT_FOS_DATA_DIR"] = str(test_dir)

    # Re-import after env var so the engine binds to the test DB
    import importlib

    from snt_fos import db as db_module  # noqa: F401
    from snt_fos import ledger as ledger_module  # noqa: F401
    from snt_fos import models as models_module  # noqa: F401
    from snt_fos.seed import bootstrap as bootstrap_module

    importlib.reload(db_module)
    importlib.reload(models_module)
    importlib.reload(ledger_module)
    importlib.reload(bootstrap_module)

    bootstrap_module.bootstrap()
    return db_module.SessionLocal()


@pytest.fixture
def cowfy_id(db):
    from snt_fos.models import Entity

    return db.query(Entity).filter_by(code="COWFY").one().id


def _basic_postings():
    from snt_fos.ledger import PostingInput

    return [
        PostingInput(account_code="572", debit=Decimal("1210")),
        PostingInput(account_code="700", credit=Decimal("1000")),
        PostingInput(account_code="477", credit=Decimal("210")),
    ]


def test_balanced_draft_creates(db, cowfy_id):
    from snt_fos.ledger import TransactionInput, create_draft

    tx = create_draft(
        db,
        TransactionInput(
            entity_id=cowfy_id,
            txn_date=date(2026, 4, 15),
            description="test sale 1000 + 21% IVA",
            postings=_basic_postings(),
        ),
    )
    assert tx.status == "draft"
    assert len(tx.postings) == 3


def test_unbalanced_rejected(db, cowfy_id):
    from snt_fos.ledger import LedgerError, PostingInput, TransactionInput, create_draft

    with pytest.raises(LedgerError, match="unbalanced"):
        create_draft(
            db,
            TransactionInput(
                entity_id=cowfy_id,
                txn_date=date(2026, 4, 15),
                description="bad",
                postings=[
                    PostingInput(account_code="572", debit=Decimal("100")),
                    PostingInput(account_code="700", credit=Decimal("99")),
                ],
            ),
        )


def test_two_sided_posting_rejected(db, cowfy_id):
    from snt_fos.ledger import LedgerError, PostingInput, TransactionInput, create_draft

    with pytest.raises(LedgerError, match="both debit AND credit"):
        create_draft(
            db,
            TransactionInput(
                entity_id=cowfy_id,
                txn_date=date(2026, 4, 15),
                description="bad",
                postings=[
                    PostingInput(account_code="572", debit=Decimal("100"), credit=Decimal("50")),
                    PostingInput(account_code="700", credit=Decimal("50")),
                ],
            ),
        )


def test_post_makes_immutable(db, cowfy_id):
    from snt_fos.ledger import (
        LedgerError,
        TransactionInput,
        create_draft,
        post_transaction,
    )

    tx = create_draft(
        db,
        TransactionInput(
            entity_id=cowfy_id,
            txn_date=date(2026, 4, 15),
            description="post test",
            postings=_basic_postings(),
        ),
    )
    posted = post_transaction(db, tx.id)
    assert posted.status == "posted"
    assert posted.posted_at is not None
    # Cannot post again
    with pytest.raises(LedgerError, match="only post draft"):
        post_transaction(db, tx.id)


def test_account_balance_after_post(db, cowfy_id):
    from snt_fos.ledger import (
        TransactionInput,
        account_balance,
        create_draft,
        post_transaction,
    )
    from snt_fos.models import Account

    tx = create_draft(
        db,
        TransactionInput(
            entity_id=cowfy_id,
            txn_date=date(2026, 4, 16),
            description="balance test",
            postings=_basic_postings(),
        ),
    )
    post_transaction(db, tx.id)

    bank = db.query(Account).filter_by(entity_id=cowfy_id, code="572").one()
    bal = account_balance(db, bank.id)
    # we've posted at least 1210 in debits to bank in this module
    assert bal["debits"] >= Decimal("1210")
    assert bal["balance"] == bal["debits"] - bal["credits"]


def test_unknown_account_rejected(db, cowfy_id):
    from snt_fos.ledger import LedgerError, PostingInput, TransactionInput, create_draft

    with pytest.raises(LedgerError, match="not found"):
        create_draft(
            db,
            TransactionInput(
                entity_id=cowfy_id,
                txn_date=date(2026, 4, 15),
                description="bad",
                postings=[
                    PostingInput(account_code="572", debit=Decimal("100")),
                    PostingInput(account_code="9999", credit=Decimal("100")),
                ],
            ),
        )


def test_trial_balance_balances(db, cowfy_id):
    """The fundamental accounting identity: across all accounts, sum of debits
    must equal sum of credits — for any entity, at any point in time."""
    from snt_fos.ledger import trial_balance

    rows = trial_balance(db, cowfy_id)
    total_d = sum((r["debits"] for r in rows), Decimal("0"))
    total_c = sum((r["credits"] for r in rows), Decimal("0"))
    assert total_d == total_c, f"trial balance broken: {total_d} vs {total_c}"
