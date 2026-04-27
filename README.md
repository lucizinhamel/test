# SNT-FOS — Financial Operating System

Local-first, multi-entity financial OS for SNT Holdings.

> **Slices delivered**
> - **1.** Spanish tax calendar (full Modelo coverage with dates, rates, reserve guidance, legal basis) + content-addressable document vault.
> - **2.** Spanish PGC chart of accounts + double-entry ledger with balance invariant + counterparties + trial balance.
>
> Invoicing, reconciliation, encryption & auth come in the next slices.

## What's in here

```
backend/   FastAPI + SQLAlchemy + SQLite — API on :8001
frontend/  Next.js 14 (App Router) + Tailwind — UI on :3000
data/      created at runtime under ~/.snt-fos/ (override via SNT_FOS_DATA_DIR)
```

## Run it

Two terminals.

**Backend** (`localhost:8001`):

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/uvicorn snt_fos.main:app --port 8001 --reload
```

On first start the DB is created at `~/.snt-fos/snt-fos.db`, three default
entities are seeded (SNT Holdings, Cowfy, Personal book), and the Spanish tax
calendar is populated for FY2025 + FY2026 (~148 obligations).

To put data somewhere else:

```bash
SNT_FOS_DATA_DIR=/path/to/your/vault .venv/bin/uvicorn snt_fos.main:app --port 8001
```

**Frontend** (`localhost:3000`):

```bash
cd frontend
npm install
npm run dev
```

Next.js rewrites `/api/*` to `http://127.0.0.1:8001/api/*` so the browser only
talks to one origin.

## Pages

- **Dashboard** (`/`) — next 90 days of tax obligations with countdown, modelo, period, reserve %.
- **Journal** (`/transactions`) — list of all ledger transactions, filter by entity & status. New entry form with live "balanced?" indicator. Detail view shows all postings; posted entries are immutable.
- **Accounts** (`/accounts`) — chart of accounts per entity, grouped by PGC group (1–7), with debits/credits/natural-balance per account. Trial-balance check at top.
- **Counterparties** (`/counterparties`) — clients & suppliers with NIF/VAT, default IVA treatment (general / reduced / intracomunitario / exportación / exempt).
- **Tax Calendar** (`/tax`) — full table grouped by entity, with rates, thresholds, legal basis (LIVA/LIRPF/LIS/RGAT articles), and notes.
- **Documents** (`/documents`) — drag-and-drop upload, dedup by SHA-256, list & download. Files live at `~/.snt-fos/documents/<sha[0:2]>/<sha[2:4]>/<sha>`.

## Spanish tax calendar — what's covered

Generated from `backend/snt_fos/seed/spanish_tax_calendar.py`. Every obligation
has: `due_date` (auto-shifted off Sat/Sun per art. 30.5 Ley 39/2015),
`direct_debit_due_date` (5 days earlier), `rate_hint`, `threshold_hint`,
`reserve_pct_hint`, `legal_basis`, `notes`.

| Modelo | When | What | Rate / threshold |
|---|---|---|---|
| **303** | Quarterly · 20 Apr / 20 Jul / 20 Oct / 30 Jan | Autoliquidación IVA | 21 / 10 / 4 / 0% — reserve 100% of (repercutido − soportado deducible) |
| **111** | Quarterly · 20 Apr / Jul / Oct / Jan | Retenciones IRPF (trabajo + profesionales) | 15% profesionales · 7% inicio actividad |
| **115** | Quarterly · 20 Apr / Jul / Oct / Jan | Retenciones IRPF (alquileres urbanos) | 19% sobre base sin IVA |
| **130** | Quarterly · 20 Apr / Jul / Oct / 30 Jan | IRPF estimación directa autónomo | 20% rendimiento neto YTD − pagos previos − retenciones |
| **202** | 1P=20 Apr · 2P=20 Oct · 3P=20 Dec | Pago fraccionado IS | Mod. a) 18% cuota · Mod. b) 17% base PYME · 24% si INCN > €10M (mín 23% s/ resultado contable) |
| **349** | Monthly · 20 del mes siguiente | Operaciones intracomunitarias | Trimestral si < €50.000 cuatro trimestres |
| **200** | Annual · 1-25 Jul (siguiente) | Impuesto sobre Sociedades | 25% general · 23% PYME (INCN<€1M) · 15% nueva creación |
| **232** | Annual · Nov (siguiente) | Operaciones vinculadas + paraísos fiscales | Mismo grupo > €250.000 · operaciones específicas > €100.000 · paraísos cualquier importe |
| **347** | Annual · Feb (siguiente) | Operaciones >€3.005,06 con misma contraparte | €3.005,06 acumulado año |
| **390** | Annual · 30 Jan (siguiente) | Resumen anual IVA | Informativo |
| **190** | Annual · 31 Jan (siguiente) | Resumen anual 111 | Informativo |
| **180** | Annual · 31 Jan (siguiente) | Resumen anual 115 | Informativo |
| **100** | Annual · 7 Apr – 30 Jun (25 Jun domiciliado) | IRPF persona física | Rentas del ahorro: tipo plano por tramo (19/21/23/27/28%). NO progresivo. |
| **714** | Annual · misma campaña que 100 | Patrimonio | Madrid bonificado 100% · declarable si bienes+derechos > €2M · vivienda habitual exenta hasta €300.000 |
| **720** | Annual · 31 Mar (siguiente) | Bienes en el extranjero | > €50.000 por bloque · re-presentación si saldo aumenta > €20.000 |
| **D-6** | Annual · 31 Ene (siguiente) | Valores depositados en el extranjero | Registro de Inversiones (no AEAT) |

## Critical amounts to memorize

- **€3.005,06** → trigger Modelo 347 per counterparty
- **€50.000** → trigger Modelo 720 per asset block
- **€250.000 / €100.000** → trigger Modelo 232 thresholds
- **€6.000.000** INCN → mandatory SII (and forces 202 modalidad b)
- **€10.000.000** INCN → 202 modalidad b at 24%, mín 23% s/ resultado contable
- **€2.000.000** patrimonio → declarable 714 even if bonificado
- **25%** → IS general · **23%** PYME · **15%** nueva creación

## Directory layout (runtime, on the user's machine)

```
~/.snt-fos/
  snt-fos.db                       SQLite database (will become SQLCipher in next slice)
  documents/
    ab/
      cd/
        abcd...sha256_full         file contents, content-addressable
```

## API surface

```
GET    /api/health
GET    /api/entities

GET    /api/tax-calendar?entity_id=&modelo=&status=&upcoming_days=&include_past_days=
PATCH  /api/tax-calendar/{id}/status        form: status=upcoming|in_prep|filed|paid|na

GET    /api/accounts?entity_id=&group_code=
GET    /api/trial-balance?entity_id=&as_of=

GET    /api/counterparties?is_client=&is_supplier=
POST   /api/counterparties                  json: name, tax_id?, country?, default_iva_treatment, ...
PATCH  /api/counterparties/{id}

GET    /api/transactions?entity_id=&status=&limit=
GET    /api/transactions/{id}
POST   /api/transactions                    json: entity_id, txn_date, description, postings[…]
POST   /api/transactions/{id}/post          enforces balance invariant; sets status=posted
POST   /api/transactions/{id}/void          drafts only

POST   /api/documents                       multipart: file, title?, notes?
GET    /api/documents
GET    /api/documents/{id}/download
POST   /api/documents/{id}/links            json: target_type, target_id, role?, notes?
GET    /api/documents/links?target_type=&target_id=
```

## Ledger invariants (enforced)

- Sum of debits = sum of credits per transaction (in base currency, to the cent)
- Each posting is one-sided (debit XOR credit)
- Posted transactions are immutable — corrections require a new entry
- Accounts marked `is_postable=false` cannot receive postings
- Trial-balance test (`backend/tests/test_ledger.py::test_trial_balance_balances`) confirms global D=C across the whole ledger after every change

## Not yet built (next slices)

- Encrypted DB (SQLCipher passphrase) — currently plain SQLite
- Invoice issuance (RD 1619/2012 + Verifactu hash chain & QR — RD 1007/2023, decision pending)
- Bank CSV import + reconciliation (BBVA / Santander / Revolut)
- 347 / 349 aggregation from real ledger data
- Authentication (single-user app password + idle lock)
- Backup/restore
- P&L and Balance Sheet reports
- Multi-currency FX gain/loss postings
