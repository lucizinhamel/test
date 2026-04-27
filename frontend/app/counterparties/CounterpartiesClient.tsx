"use client";

import { useState } from "react";
import { api, Counterparty } from "@/lib/api";

const IVA_TREATMENTS = [
  { v: "general_21", l: "General (21%)" },
  { v: "reduced_10", l: "Reducido (10%)" },
  { v: "super_reduced_4", l: "Superreducido (4%)" },
  { v: "exempt", l: "Exento" },
  { v: "intracom_reverse_charge", l: "Intracomunitario (inversión sujeto pasivo)" },
  { v: "export_exempt", l: "Exportación (exenta art. 21 LIVA)" },
];

export default function CounterpartiesClient({ initial }: { initial: Counterparty[] }) {
  const [items, setItems] = useState<Counterparty[]>(initial);
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    name: "",
    legal_name: "",
    tax_id: "",
    tax_id_country: "ES",
    country: "ES",
    default_iva_treatment: "general_21",
    is_client: true,
    is_supplier: false,
    email: "",
    phone: "",
  });

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const created = await api.createCounterparty({
        ...form,
        legal_name: form.legal_name || null,
        tax_id: form.tax_id || null,
        tax_id_country: form.tax_id_country || null,
        email: form.email || null,
        phone: form.phone || null,
      });
      setItems([created, ...items]);
      setAdding(false);
      setForm({ ...form, name: "", legal_name: "", tax_id: "", email: "", phone: "" });
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed");
    }
  }

  return (
    <div className="space-y-8">
      <section className="flex items-baseline justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-ink">Counterparties</h1>
          <p className="mt-1 text-sm text-steel-500">
            Clients & suppliers. NIF / VAT number drives Modelo 347 & 349 aggregation.
          </p>
        </div>
        <button
          onClick={() => setAdding((v) => !v)}
          className="rounded bg-ink px-4 py-2 text-sm text-white hover:bg-steel-700"
        >
          {adding ? "Cancel" : "+ Add counterparty"}
        </button>
      </section>

      {adding && (
        <form
          onSubmit={submit}
          className="grid grid-cols-1 gap-3 rounded border border-steel-100 bg-white p-5 md:grid-cols-3"
        >
          <Field label="Name *">
            <input
              required
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="input"
            />
          </Field>
          <Field label="Legal name">
            <input
              value={form.legal_name}
              onChange={(e) => setForm({ ...form, legal_name: e.target.value })}
              className="input"
            />
          </Field>
          <Field label="Tax ID (NIF/VAT)">
            <input
              value={form.tax_id}
              onChange={(e) => setForm({ ...form, tax_id: e.target.value })}
              className="input"
              placeholder="B12345678 / EG-..."
            />
          </Field>
          <Field label="Country">
            <input
              value={form.country}
              onChange={(e) =>
                setForm({ ...form, country: e.target.value.toUpperCase().slice(0, 2) })
              }
              className="input"
              maxLength={2}
            />
          </Field>
          <Field label="Default IVA treatment">
            <select
              value={form.default_iva_treatment}
              onChange={(e) => setForm({ ...form, default_iva_treatment: e.target.value })}
              className="input"
            >
              {IVA_TREATMENTS.map((t) => (
                <option key={t.v} value={t.v}>
                  {t.l}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Email">
            <input
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="input"
            />
          </Field>
          <div className="flex items-end gap-4 text-sm">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={form.is_client}
                onChange={(e) => setForm({ ...form, is_client: e.target.checked })}
              />
              Client
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={form.is_supplier}
                onChange={(e) => setForm({ ...form, is_supplier: e.target.checked })}
              />
              Supplier
            </label>
          </div>
          <div className="md:col-span-3">
            <button
              type="submit"
              className="rounded bg-ink px-5 py-2 text-sm text-white hover:bg-steel-700"
            >
              Save
            </button>
            {error && <span className="ml-3 text-xs text-red-700">{error}</span>}
          </div>
        </form>
      )}

      <section>
        <div className="overflow-hidden rounded border border-steel-100 bg-white">
          <table className="w-full text-sm">
            <thead className="bg-steel-50 text-left text-xs uppercase tracking-wide text-steel-500">
              <tr>
                <th className="px-3 py-2">Name</th>
                <th className="px-3 py-2">Tax ID</th>
                <th className="px-3 py-2">Country</th>
                <th className="px-3 py-2">IVA treatment</th>
                <th className="px-3 py-2">Roles</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-3 py-8 text-center text-steel-500">
                    No counterparties yet.
                  </td>
                </tr>
              )}
              {items.map((c) => (
                <tr key={c.id} className="border-t border-steel-100">
                  <td className="px-3 py-2 text-xs text-ink">
                    {c.name}
                    {c.legal_name && (
                      <span className="ml-2 text-steel-500">({c.legal_name})</span>
                    )}
                  </td>
                  <td className="px-3 py-2 font-mono text-xs">
                    {c.tax_id ? `${c.tax_id_country ?? ""}${c.tax_id_country ? "-" : ""}${c.tax_id}` : "—"}
                  </td>
                  <td className="px-3 py-2 font-mono text-xs">{c.country}</td>
                  <td className="px-3 py-2 text-xs text-steel-700">
                    {IVA_TREATMENTS.find((t) => t.v === c.default_iva_treatment)?.l ?? c.default_iva_treatment}
                  </td>
                  <td className="px-3 py-2 text-xs">
                    {c.is_client && (
                      <span className="mr-1 rounded bg-emerald-100 px-2 py-0.5 text-[10px] text-emerald-900">
                        client
                      </span>
                    )}
                    {c.is_supplier && (
                      <span className="rounded bg-amber-100 px-2 py-0.5 text-[10px] text-amber-900">
                        supplier
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block text-sm">
      <span className="text-xs text-steel-500">{label}</span>
      <div className="mt-1">{children}</div>
    </label>
  );
}
