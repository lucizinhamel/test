import Link from "next/link";
import { api, Entity, LedgerTransaction } from "@/lib/api";

function fmtMoney(s: string): string {
  return Number(s).toLocaleString("es-ES", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function statusBadge(s: string): string {
  switch (s) {
    case "draft":
      return "bg-amber-100 text-amber-900";
    case "posted":
      return "bg-emerald-100 text-emerald-900";
    case "void":
      return "bg-steel-100 text-steel-700 line-through";
    default:
      return "bg-steel-50 text-steel-500";
  }
}

export const dynamic = "force-dynamic";

export default async function TransactionsPage({
  searchParams,
}: {
  searchParams: { entity?: string; status?: string };
}) {
  const entities: Entity[] = await api.entities();
  const selected = searchParams.entity
    ? entities.find((e) => e.code === searchParams.entity) ?? null
    : null;

  const txs: LedgerTransaction[] = await api.transactions(
    selected?.id,
    searchParams.status,
  );

  return (
    <div className="space-y-8">
      <section className="flex items-baseline justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-ink">Journal</h1>
          <p className="mt-1 text-sm text-steel-500">
            Ledger transactions across {entities.length} entities — most recent first.
          </p>
        </div>
        <Link
          href="/transactions/new"
          className="rounded bg-ink px-4 py-2 text-sm text-white hover:bg-steel-700"
        >
          + New entry
        </Link>
      </section>

      <section className="flex flex-wrap gap-2 text-sm">
        <a
          href="/transactions"
          className={`rounded border px-3 py-1 ${
            !selected
              ? "border-ink bg-ink text-white"
              : "border-steel-100 text-steel-700"
          }`}
        >
          All entities
        </a>
        {entities.map((e) => (
          <a
            key={e.id}
            href={`/transactions?entity=${e.code}${searchParams.status ? `&status=${searchParams.status}` : ""}`}
            className={`rounded border px-3 py-1 ${
              selected?.id === e.id
                ? "border-ink bg-ink text-white"
                : "border-steel-100 text-steel-700"
            }`}
          >
            {e.code}
          </a>
        ))}
        <span className="ml-4 text-steel-300">·</span>
        {[
          { v: undefined, l: "Any status" },
          { v: "draft", l: "Drafts" },
          { v: "posted", l: "Posted" },
          { v: "void", l: "Void" },
        ].map((s) => (
          <a
            key={s.v ?? "all"}
            href={`/transactions?${selected ? `entity=${selected.code}` : ""}${
              selected && s.v ? "&" : ""
            }${s.v ? `status=${s.v}` : ""}`}
            className={`rounded border px-3 py-1 ${
              (searchParams.status ?? undefined) === s.v
                ? "border-ink bg-ink text-white"
                : "border-steel-100 text-steel-700"
            }`}
          >
            {s.l}
          </a>
        ))}
      </section>

      <section>
        <div className="overflow-hidden rounded border border-steel-100 bg-white">
          <table className="w-full text-sm">
            <thead className="bg-steel-50 text-left text-xs uppercase tracking-wide text-steel-500">
              <tr>
                <th className="px-3 py-2">Date</th>
                <th className="px-3 py-2">Entity</th>
                <th className="px-3 py-2">Description</th>
                <th className="px-3 py-2">Counterparty</th>
                <th className="px-3 py-2 text-right">Total</th>
                <th className="px-3 py-2">CCY</th>
                <th className="px-3 py-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {txs.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-3 py-8 text-center text-steel-500">
                    No transactions yet — start with{" "}
                    <Link href="/transactions/new" className="underline">
                      a new entry
                    </Link>
                    .
                  </td>
                </tr>
              )}
              {txs.map((tx) => (
                <tr key={tx.id} className="border-t border-steel-100 hover:bg-steel-50">
                  <td className="px-3 py-2 font-mono text-xs">{tx.txn_date}</td>
                  <td className="px-3 py-2 font-mono text-xs text-steel-700">{tx.entity_code}</td>
                  <td className="px-3 py-2 text-xs text-ink">
                    <Link href={`/transactions/${tx.id}`} className="hover:underline">
                      {tx.description}
                    </Link>
                  </td>
                  <td className="px-3 py-2 text-xs text-steel-700">{tx.counterparty_name ?? "—"}</td>
                  <td className="px-3 py-2 text-right font-mono text-xs">{fmtMoney(tx.total)}</td>
                  <td className="px-3 py-2 font-mono text-xs text-steel-500">{tx.currency}</td>
                  <td className="px-3 py-2">
                    <span className={`rounded px-2 py-0.5 text-[10px] uppercase ${statusBadge(tx.status)}`}>
                      {tx.status}
                    </span>
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
