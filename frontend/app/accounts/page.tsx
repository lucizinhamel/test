import { api, Account, Entity, TrialBalanceRow } from "@/lib/api";

function fmtMoney(s: string): string {
  const n = Number(s);
  return n.toLocaleString("es-ES", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function groupOrder(g: string): number {
  // Numeric PGC groups first, then personal-book groups
  if (/^\d$/.test(g)) return Number(g);
  return 99;
}

export default async function AccountsPage({
  searchParams,
}: {
  searchParams: { entity?: string };
}) {
  const entities: Entity[] = await api.entities();
  const selected =
    entities.find((e) => e.code === searchParams.entity) ??
    entities.find((e) => !e.is_personal && !e.is_holding) ??
    entities[0];

  const [accounts, tb]: [Account[], TrialBalanceRow[]] = await Promise.all([
    api.accounts(selected.id),
    api.trialBalance(selected.id),
  ]);

  const balanceByAccount = new Map(tb.map((r) => [r.account_id, r]));

  const groups = new Map<string, Account[]>();
  for (const a of accounts) {
    const arr = groups.get(a.group_code) ?? [];
    arr.push(a);
    groups.set(a.group_code, arr);
  }
  const sortedGroups = Array.from(groups.entries()).sort(([a], [b]) => groupOrder(a) - groupOrder(b));

  const totalDebits = tb.reduce((acc, r) => acc + Number(r.debits), 0);
  const totalCredits = tb.reduce((acc, r) => acc + Number(r.credits), 0);
  const balanced = Math.abs(totalDebits - totalCredits) < 0.005;

  return (
    <div className="space-y-10">
      <section>
        <div className="flex items-baseline justify-between">
          <h1 className="text-3xl font-semibold tracking-tight text-ink">Chart of Accounts</h1>
          <div className="flex gap-2 text-sm">
            {entities.map((e) => (
              <a
                key={e.id}
                href={`/accounts?entity=${e.code}`}
                className={`rounded border px-3 py-1 ${
                  e.id === selected.id
                    ? "border-ink bg-ink text-white"
                    : "border-steel-100 text-steel-700 hover:border-steel-300"
                }`}
              >
                {e.code}
              </a>
            ))}
          </div>
        </div>
        <p className="mt-1 text-sm text-steel-500">
          {selected.legal_name} · {accounts.length} accounts ·{" "}
          {selected.is_personal
            ? "Simplified personal CoA"
            : "Spanish PGC (RD 1514/2007)"}
        </p>
      </section>

      <section>
        <div className="mb-3 flex items-baseline justify-between">
          <h2 className="text-lg font-medium text-ink">Trial balance</h2>
          <div className="text-sm">
            <span className="font-mono text-xs text-steel-500">D </span>
            <span className="font-mono text-sm">{totalDebits.toLocaleString("es-ES", { minimumFractionDigits: 2 })}</span>
            <span className="ml-4 font-mono text-xs text-steel-500">C </span>
            <span className="font-mono text-sm">{totalCredits.toLocaleString("es-ES", { minimumFractionDigits: 2 })}</span>
            <span
              className={`ml-4 rounded px-2 py-0.5 text-xs ${
                balanced ? "bg-emerald-100 text-emerald-900" : "bg-red-100 text-red-900"
              }`}
            >
              {balanced ? "BALANCED" : "NOT BALANCED"}
            </span>
          </div>
        </div>
      </section>

      {sortedGroups.map(([group, accs]) => (
        <section key={group}>
          <h3 className="mb-2 font-mono text-xs uppercase tracking-widest text-steel-500">
            Grupo {group}
          </h3>
          <div className="overflow-hidden rounded border border-steel-100 bg-white">
            <table className="w-full text-sm">
              <thead className="bg-steel-50 text-left text-xs uppercase tracking-wide text-steel-500">
                <tr>
                  <th className="px-3 py-2">Code</th>
                  <th className="px-3 py-2">Name</th>
                  <th className="px-3 py-2">Nature</th>
                  <th className="px-3 py-2 text-right">Debits</th>
                  <th className="px-3 py-2 text-right">Credits</th>
                  <th className="px-3 py-2 text-right">Balance</th>
                  <th className="px-3 py-2">IVA</th>
                </tr>
              </thead>
              <tbody>
                {accs.map((a) => {
                  const bal = balanceByAccount.get(a.id);
                  return (
                    <tr key={a.id} className="border-t border-steel-100">
                      <td className="px-3 py-2 font-mono text-xs">{a.code}</td>
                      <td className="px-3 py-2 text-xs text-ink">
                        {a.name_es}
                        <span className="ml-2 text-steel-500">{a.name_en}</span>
                      </td>
                      <td className="px-3 py-2 font-mono text-[10px] uppercase text-steel-500">
                        {a.nature}
                      </td>
                      <td className="px-3 py-2 text-right font-mono text-xs text-steel-700">
                        {bal ? fmtMoney(bal.debits) : "—"}
                      </td>
                      <td className="px-3 py-2 text-right font-mono text-xs text-steel-700">
                        {bal ? fmtMoney(bal.credits) : "—"}
                      </td>
                      <td className="px-3 py-2 text-right font-mono text-xs text-ink">
                        {bal ? fmtMoney(bal.natural_balance) : "—"}
                      </td>
                      <td className="px-3 py-2 font-mono text-[10px] text-steel-500">
                        {a.iva_rate_default ? `${a.iva_rate_default}%` : "—"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      ))}
    </div>
  );
}
