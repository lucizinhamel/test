import Link from "next/link";
import { api } from "@/lib/api";
import TransactionDetailActions from "./Actions";

export const dynamic = "force-dynamic";

function fmtMoney(s: string): string {
  return Number(s).toLocaleString("es-ES", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export default async function Page({ params }: { params: { id: string } }) {
  const tx = await api.getTransaction(params.id);

  return (
    <div className="space-y-6">
      <Link href="/transactions" className="text-sm text-steel-500 hover:text-ink">
        ← Back to journal
      </Link>

      <div className="flex items-baseline justify-between">
        <h1 className="text-2xl font-semibold tracking-tight text-ink">{tx.description}</h1>
        <span
          className={`rounded px-2 py-0.5 text-xs uppercase ${
            tx.status === "posted"
              ? "bg-emerald-100 text-emerald-900"
              : tx.status === "draft"
              ? "bg-amber-100 text-amber-900"
              : "bg-steel-100 text-steel-700"
          }`}
        >
          {tx.status}
        </span>
      </div>

      <dl className="grid grid-cols-2 gap-x-6 gap-y-2 rounded border border-steel-100 bg-white p-5 text-sm md:grid-cols-4">
        <Detail label="Date" value={tx.txn_date} />
        <Detail label="Entity" value={tx.entity_code ?? ""} />
        <Detail label="Counterparty" value={tx.counterparty_name ?? "—"} />
        <Detail label="Currency" value={`${tx.currency} (FX ${tx.fx_rate_to_base})`} />
        <Detail label="Project tag" value={tx.project_tag ?? "—"} />
        <Detail label="Reference" value={tx.reference_type ? `${tx.reference_type}/${tx.reference_id ?? ""}` : "—"} />
        <Detail label="Posted by" value={tx.posted_by ?? "—"} />
        <Detail label="Posted at" value={tx.posted_at ? new Date(tx.posted_at).toLocaleString("es-ES") : "—"} />
      </dl>

      <section>
        <h2 className="mb-2 text-sm font-medium text-ink">Postings</h2>
        <div className="overflow-hidden rounded border border-steel-100 bg-white">
          <table className="w-full text-sm">
            <thead className="bg-steel-50 text-left text-xs uppercase tracking-wide text-steel-500">
              <tr>
                <th className="px-3 py-2">#</th>
                <th className="px-3 py-2">Account</th>
                <th className="px-3 py-2">Description</th>
                <th className="px-3 py-2 text-right">Debit</th>
                <th className="px-3 py-2 text-right">Credit</th>
                <th className="px-3 py-2 text-right">IVA rate</th>
                <th className="px-3 py-2 text-right">IVA amount</th>
              </tr>
            </thead>
            <tbody>
              {tx.postings.map((p) => (
                <tr key={p.id} className="border-t border-steel-100">
                  <td className="px-3 py-2 font-mono text-xs text-steel-500">{p.line_no}</td>
                  <td className="px-3 py-2 text-xs">
                    <span className="font-mono">{p.account_code}</span>
                    <span className="ml-2 text-steel-700">{p.account_name_es}</span>
                  </td>
                  <td className="px-3 py-2 text-xs text-steel-500">{p.description_override ?? "—"}</td>
                  <td className="px-3 py-2 text-right font-mono text-xs">
                    {Number(p.debit) > 0 ? fmtMoney(p.debit) : "—"}
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-xs">
                    {Number(p.credit) > 0 ? fmtMoney(p.credit) : "—"}
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-xs text-steel-500">
                    {p.iva_rate ?? "—"}
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-xs text-steel-500">
                    {p.iva_amount ? fmtMoney(p.iva_amount) : "—"}
                  </td>
                </tr>
              ))}
              <tr className="border-t-2 border-steel-300">
                <td colSpan={3} className="px-3 py-2 text-right text-xs uppercase text-steel-500">
                  Total
                </td>
                <td className="px-3 py-2 text-right font-mono text-sm">{fmtMoney(tx.total)}</td>
                <td className="px-3 py-2 text-right font-mono text-sm">{fmtMoney(tx.total)}</td>
                <td colSpan={2}></td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <TransactionDetailActions txId={tx.id} status={tx.status} />
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-steel-500">{label}</dt>
      <dd className="font-mono text-sm text-ink">{value}</dd>
    </div>
  );
}
