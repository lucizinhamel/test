export type Entity = {
  id: string;
  code: string;
  legal_name: string;
  nif: string | null;
  country: string;
  base_currency: string;
  is_personal: boolean;
  is_holding: boolean;
  iva_regime: string;
  active: boolean;
};

export type TaxObligation = {
  id: string;
  entity_id: string;
  entity_code: string | null;
  modelo: string;
  name_es: string;
  name_en: string;
  legal_basis: string | null;
  period_kind: string;
  period_label: string;
  period_start: string;
  period_end: string;
  due_date: string;
  direct_debit_due_date: string | null;
  payment_kind: string;
  rate_hint: string | null;
  threshold_hint: string | null;
  reserve_pct_hint: string | null;
  estimated_amount: string | null;
  notes: string | null;
  status: string;
};

export type Account = {
  id: string;
  entity_id: string;
  code: string;
  name_es: string;
  name_en: string;
  group_code: string;
  nature: "debit" | "credit";
  is_postable: boolean;
  iva_rate_default: string | null;
  active: boolean;
  sort_order: number;
};

export type Counterparty = {
  id: string;
  name: string;
  legal_name: string | null;
  tax_id: string | null;
  tax_id_country: string | null;
  country: string;
  address_line1: string | null;
  city: string | null;
  postal_code: string | null;
  default_payment_terms_days: number | null;
  default_iva_treatment: string;
  email: string | null;
  phone: string | null;
  is_client: boolean;
  is_supplier: boolean;
  active: boolean;
};

export type Posting = {
  id: string;
  line_no: number;
  account_id: string;
  account_code: string | null;
  account_name_es: string | null;
  debit: string;
  credit: string;
  debit_ccy: string;
  credit_ccy: string;
  iva_code: string | null;
  iva_rate: string | null;
  iva_amount: string | null;
  description_override: string | null;
};

export type LedgerTransaction = {
  id: string;
  entity_id: string;
  entity_code: string | null;
  txn_date: string;
  value_date: string | null;
  description: string;
  currency: string;
  fx_rate_to_base: string;
  counterparty_id: string | null;
  counterparty_name: string | null;
  reference_type: string | null;
  reference_id: string | null;
  project_tag: string | null;
  brand_tag: string | null;
  status: "draft" | "posted" | "void";
  posted_at: string | null;
  posted_by: string | null;
  total: string;
  postings: Posting[];
};

export type TrialBalanceRow = {
  account_id: string;
  code: string;
  name_es: string;
  name_en: string;
  group_code: string;
  nature: "debit" | "credit";
  debits: string;
  credits: string;
  balance: string;
  natural_balance: string;
};

export type DocumentRow = {
  id: string;
  sha256: string;
  mime_type: string;
  byte_size: number;
  original_filename: string;
  title: string | null;
  notes: string | null;
  uploaded_at: string;
  uploaded_by: string;
};

async function j<T>(r: Response): Promise<T> {
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return (await r.json()) as T;
}

export const api = {
  entities: () => fetch("/api/entities", { cache: "no-store" }).then((r) => j<Entity[]>(r)),
  taxCalendar: (params: Record<string, string | number | undefined> = {}) => {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== "") qs.append(k, String(v));
    });
    return fetch(`/api/tax-calendar?${qs.toString()}`, { cache: "no-store" }).then((r) =>
      j<TaxObligation[]>(r),
    );
  },
  setObligationStatus: (id: string, status: string) => {
    const fd = new FormData();
    fd.append("status", status);
    return fetch(`/api/tax-calendar/${id}/status`, { method: "PATCH", body: fd }).then((r) =>
      j<TaxObligation>(r),
    );
  },
  accounts: (entityId?: string) => {
    const qs = entityId ? `?entity_id=${entityId}` : "";
    return fetch(`/api/accounts${qs}`, { cache: "no-store" }).then((r) => j<Account[]>(r));
  },
  trialBalance: (entityId: string) =>
    fetch(`/api/trial-balance?entity_id=${entityId}`, { cache: "no-store" }).then((r) =>
      j<TrialBalanceRow[]>(r),
    ),
  counterparties: () =>
    fetch("/api/counterparties", { cache: "no-store" }).then((r) => j<Counterparty[]>(r)),
  createCounterparty: (payload: Partial<Counterparty>) =>
    fetch("/api/counterparties", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then((r) => j<Counterparty>(r)),
  transactions: (entityId?: string, status?: string) => {
    const qs = new URLSearchParams();
    if (entityId) qs.append("entity_id", entityId);
    if (status) qs.append("status", status);
    return fetch(`/api/transactions?${qs.toString()}`, { cache: "no-store" }).then((r) =>
      j<LedgerTransaction[]>(r),
    );
  },
  getTransaction: (id: string) =>
    fetch(`/api/transactions/${id}`, { cache: "no-store" }).then((r) => j<LedgerTransaction>(r)),
  createTransaction: (payload: {
    entity_id: string;
    txn_date: string;
    description: string;
    currency?: string;
    fx_rate_to_base?: string;
    counterparty_id?: string | null;
    project_tag?: string | null;
    postings: { account_code: string; debit: string; credit: string; description?: string }[];
  }) =>
    fetch("/api/transactions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then(async (r) => {
      if (!r.ok) {
        const body = await r.json().catch(() => ({}));
        throw new Error(body.detail ?? `${r.status} ${r.statusText}`);
      }
      return (await r.json()) as LedgerTransaction;
    }),
  postTransaction: (id: string) =>
    fetch(`/api/transactions/${id}/post`, { method: "POST" }).then(async (r) => {
      if (!r.ok) {
        const body = await r.json().catch(() => ({}));
        throw new Error(body.detail ?? `${r.status} ${r.statusText}`);
      }
      return (await r.json()) as LedgerTransaction;
    }),
  voidTransaction: (id: string) =>
    fetch(`/api/transactions/${id}/void`, { method: "POST" }).then((r) => j<LedgerTransaction>(r)),
  documents: () => fetch("/api/documents", { cache: "no-store" }).then((r) => j<DocumentRow[]>(r)),
  uploadDocument: async (file: File, title?: string, notes?: string) => {
    const fd = new FormData();
    fd.append("file", file);
    if (title) fd.append("title", title);
    if (notes) fd.append("notes", notes);
    const r = await fetch("/api/documents", { method: "POST", body: fd });
    return j<DocumentRow>(r);
  },
};
