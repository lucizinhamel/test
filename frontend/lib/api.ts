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
