import { api, TaxObligation } from "@/lib/api";

function formatDate(iso: string): string {
  return new Date(iso + "T00:00:00").toLocaleDateString("es-ES", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function paymentBadge(kind: string): string {
  switch (kind) {
    case "self_assessed":
      return "bg-amber-100 text-amber-900";
    case "advance_payment":
      return "bg-blue-100 text-blue-900";
    case "withheld":
      return "bg-emerald-100 text-emerald-900";
    case "informational":
      return "bg-steel-100 text-steel-700";
    default:
      return "bg-steel-50 text-steel-500";
  }
}

function groupByEntity(rows: TaxObligation[]): Record<string, TaxObligation[]> {
  const out: Record<string, TaxObligation[]> = {};
  for (const r of rows) {
    const key = r.entity_code ?? "?";
    (out[key] ||= []).push(r);
  }
  return out;
}

export default async function TaxCalendar() {
  const obligations = await api.taxCalendar({ include_past_days: 60 });
  const groups = groupByEntity(obligations);

  return (
    <div className="space-y-10">
      <section>
        <h1 className="text-3xl font-semibold tracking-tight text-ink">Tax Calendar</h1>
        <p className="mt-1 max-w-3xl text-sm text-steel-500">
          Spanish tax obligations for all active entities. Dates auto-shift off Saturdays / Sundays
          (art. 30.5 Ley 39/2015). Holidays not yet auto-skipped — verify before each campaign.
        </p>
      </section>

      {Object.entries(groups).map(([entityCode, rows]) => (
        <section key={entityCode}>
          <h2 className="mb-3 font-mono text-sm uppercase tracking-widest text-steel-500">
            {entityCode}
          </h2>
          <div className="overflow-hidden rounded border border-steel-100 bg-white">
            <table className="w-full text-sm">
              <thead className="bg-steel-50 text-left text-xs uppercase tracking-wide text-steel-500">
                <tr>
                  <th className="px-3 py-2">Modelo</th>
                  <th className="px-3 py-2">Period</th>
                  <th className="px-3 py-2">Due</th>
                  <th className="px-3 py-2">Domicil.</th>
                  <th className="px-3 py-2">Type</th>
                  <th className="px-3 py-2">Rate</th>
                  <th className="px-3 py-2">Threshold / Notes</th>
                  <th className="px-3 py-2">Legal</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((o) => (
                  <tr key={o.id} className="border-t border-steel-100 align-top">
                    <td className="px-3 py-2 font-mono text-xs">M{o.modelo}</td>
                    <td className="px-3 py-2 font-mono text-xs text-steel-700">{o.period_label}</td>
                    <td className="px-3 py-2 font-mono text-xs text-ink">{formatDate(o.due_date)}</td>
                    <td className="px-3 py-2 font-mono text-xs text-steel-500">
                      {o.direct_debit_due_date ? formatDate(o.direct_debit_due_date) : "—"}
                    </td>
                    <td className="px-3 py-2 text-xs">
                      <span
                        className={`rounded px-2 py-0.5 text-[10px] uppercase tracking-wide ${paymentBadge(
                          o.payment_kind,
                        )}`}
                      >
                        {o.payment_kind.replace("_", " ")}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-xs text-steel-700">{o.rate_hint ?? "—"}</td>
                    <td className="px-3 py-2 text-xs text-steel-700">
                      {o.threshold_hint && (
                        <div className="font-medium text-ink">{o.threshold_hint}</div>
                      )}
                      {o.notes && <div className="mt-1 text-steel-500">{o.notes}</div>}
                    </td>
                    <td className="px-3 py-2 font-mono text-[10px] text-steel-500">
                      {o.legal_basis ?? "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ))}
    </div>
  );
}
