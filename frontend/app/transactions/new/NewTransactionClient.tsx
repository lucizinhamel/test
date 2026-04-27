"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { api, Account, Counterparty, Entity } from "@/lib/api";

type Line = {
  account_code: string;
  debit: string;
  credit: string;
  description: string;
};

const empty = (): Line => ({ account_code: "", debit: "", credit: "", description: "" });

export default function NewTransactionClient({
  entities,
  counterparties,
}: {
  entities: Entity[];
  counterparties: Counterparty[];
}) {
  const router = useRouter();
  const today = new Date().toISOString().slice(0, 10);

  const [entityId, setEntityId] = useState(entities[0]?.id ?? "");
  const [txnDate, setTxnDate] = useState(today);
  const [description, setDescription] = useState("");
  const [counterpartyId, setCounterpartyId] = useState<string>("");
  const [currency, setCurrency] = useState("EUR");
  const [fxRate, setFxRate] = useState("1");
  const [projectTag, setProjectTag] = useState("");
  const [lines, setLines] = useState<Line[]>([empty(), empty()]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!entityId) return;
    setAccounts([]);
    api.accounts(entityId).then(setAccounts).catch((e) => setError(String(e)));
  }, [entityId]);

  const totals = useMemo(() => {
    const d = lines.reduce((acc, l) => acc + (Number(l.debit) || 0), 0);
    const c = lines.reduce((acc, l) => acc + (Number(l.credit) || 0), 0);
    return { d, c, diff: d - c, balanced: Math.abs(d - c) < 0.005 && d > 0 };
  }, [lines]);

  function setLine(idx: number, patch: Partial<Line>) {
    setLines((ls) => ls.map((l, i) => (i === idx ? { ...l, ...patch } : l)));
  }
  function addLine() {
    setLines((ls) => [...ls, empty()]);
  }
  function removeLine(idx: number) {
    setLines((ls) => (ls.length <= 2 ? ls : ls.filter((_, i) => i !== idx)));
  }

  async function save(post: boolean) {
    setError(null);
    if (!totals.balanced) {
      setError(`Unbalanced: D=${totals.d.toFixed(2)} vs C=${totals.c.toFixed(2)}`);
      return;
    }
    setBusy(true);
    try {
      const payload = {
        entity_id: entityId,
        txn_date: txnDate,
        description,
        currency,
        fx_rate_to_base: fxRate,
        counterparty_id: counterpartyId || null,
        project_tag: projectTag || null,
        postings: lines
          .filter((l) => l.account_code && (Number(l.debit) > 0 || Number(l.credit) > 0))
          .map((l) => ({
            account_code: l.account_code,
            debit: l.debit || "0",
            credit: l.credit || "0",
            description: l.description || undefined,
          })),
      };
      const created = await api.createTransaction(payload);
      if (post) await api.postTransaction(created.id);
      router.push(`/transactions/${created.id}`);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-semibold tracking-tight text-ink">New journal entry</h1>

      <section className="grid grid-cols-1 gap-3 rounded border border-steel-100 bg-white p-5 md:grid-cols-3">
        <Field label="Entity *">
          <select
            value={entityId}
            onChange={(e) => setEntityId(e.target.value)}
            className="input"
          >
            {entities.map((e) => (
              <option key={e.id} value={e.id}>
                {e.code} — {e.legal_name}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Date *">
          <input
            type="date"
            value={txnDate}
            onChange={(e) => setTxnDate(e.target.value)}
            className="input"
          />
        </Field>
        <Field label="Counterparty">
          <select
            value={counterpartyId}
            onChange={(e) => setCounterpartyId(e.target.value)}
            className="input"
          >
            <option value="">— none —</option>
            {counterparties.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Description *">
          <input
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="input"
            placeholder="e.g. Sale to Acme Egypt LLC — invoice COWFY-2026-0001"
          />
        </Field>
        <Field label="Currency">
          <input
            value={currency}
            onChange={(e) => setCurrency(e.target.value.toUpperCase())}
            className="input"
            maxLength={3}
          />
        </Field>
        <Field label="FX rate to base">
          <input
            value={fxRate}
            onChange={(e) => setFxRate(e.target.value)}
            className="input"
            placeholder="1"
          />
        </Field>
        <Field label="Project / cost-center tag">
          <input
            value={projectTag}
            onChange={(e) => setProjectTag(e.target.value)}
            className="input"
            placeholder="e.g. Egypt-Alex-24u"
          />
        </Field>
      </section>

      <section className="rounded border border-steel-100 bg-white p-5">
        <h2 className="mb-3 text-sm font-medium text-ink">Postings</h2>
        <table className="w-full text-sm">
          <thead className="text-left text-xs uppercase tracking-wide text-steel-500">
            <tr>
              <th className="px-2 py-1">Account</th>
              <th className="px-2 py-1">Description</th>
              <th className="px-2 py-1 text-right">Debit</th>
              <th className="px-2 py-1 text-right">Credit</th>
              <th className="px-2 py-1"></th>
            </tr>
          </thead>
          <tbody>
            {lines.map((l, i) => (
              <tr key={i} className="border-t border-steel-100">
                <td className="px-2 py-1">
                  <select
                    value={l.account_code}
                    onChange={(e) => setLine(i, { account_code: e.target.value })}
                    className="input font-mono text-xs"
                  >
                    <option value="">— select —</option>
                    {accounts.map((a) => (
                      <option key={a.id} value={a.code}>
                        {a.code} · {a.name_es}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-2 py-1">
                  <input
                    value={l.description}
                    onChange={(e) => setLine(i, { description: e.target.value })}
                    className="input text-xs"
                    placeholder="line memo"
                  />
                </td>
                <td className="px-2 py-1">
                  <input
                    inputMode="decimal"
                    value={l.debit}
                    onChange={(e) =>
                      setLine(i, { debit: e.target.value, credit: e.target.value ? "" : l.credit })
                    }
                    className="input text-right font-mono text-xs"
                  />
                </td>
                <td className="px-2 py-1">
                  <input
                    inputMode="decimal"
                    value={l.credit}
                    onChange={(e) =>
                      setLine(i, { credit: e.target.value, debit: e.target.value ? "" : l.debit })
                    }
                    className="input text-right font-mono text-xs"
                  />
                </td>
                <td className="px-2 py-1 text-right">
                  <button
                    type="button"
                    onClick={() => removeLine(i)}
                    disabled={lines.length <= 2}
                    className="text-xs text-steel-500 hover:text-red-700 disabled:opacity-30"
                  >
                    ×
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="border-t-2 border-steel-300">
              <td colSpan={2} className="px-2 py-2 text-right text-xs uppercase text-steel-500">
                Totals
              </td>
              <td className="px-2 py-2 text-right font-mono text-sm">{totals.d.toFixed(2)}</td>
              <td className="px-2 py-2 text-right font-mono text-sm">{totals.c.toFixed(2)}</td>
              <td className="px-2 py-2 text-right">
                <span
                  className={`rounded px-2 py-0.5 text-[10px] uppercase ${
                    totals.balanced
                      ? "bg-emerald-100 text-emerald-900"
                      : totals.d === 0 && totals.c === 0
                      ? "bg-steel-100 text-steel-700"
                      : "bg-red-100 text-red-900"
                  }`}
                >
                  {totals.balanced
                    ? "balanced"
                    : totals.d === 0 && totals.c === 0
                    ? "empty"
                    : `Δ ${totals.diff.toFixed(2)}`}
                </span>
              </td>
            </tr>
          </tfoot>
        </table>
        <button
          type="button"
          onClick={addLine}
          className="mt-3 text-xs text-steel-500 hover:text-ink"
        >
          + Add line
        </button>
      </section>

      <div className="flex items-center gap-3">
        <button
          type="button"
          disabled={busy || !entityId || !description}
          onClick={() => save(false)}
          className="rounded border border-steel-300 px-4 py-2 text-sm text-ink hover:bg-steel-50 disabled:opacity-40"
        >
          Save draft
        </button>
        <button
          type="button"
          disabled={busy || !entityId || !description || !totals.balanced}
          onClick={() => save(true)}
          className="rounded bg-ink px-4 py-2 text-sm text-white hover:bg-steel-700 disabled:opacity-40"
        >
          Save &amp; post
        </button>
        {error && <span className="text-xs text-red-700">{error}</span>}
      </div>
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
