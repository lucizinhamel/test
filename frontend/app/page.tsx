import Link from "next/link";
import { api } from "@/lib/api";

function daysUntil(iso: string): number {
  const d = new Date(iso + "T00:00:00");
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  return Math.round((d.getTime() - now.getTime()) / 86400000);
}

function formatDate(iso: string): string {
  return new Date(iso + "T00:00:00").toLocaleDateString("es-ES", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export default async function Dashboard() {
  const [obligations, entities] = await Promise.all([
    api.taxCalendar({ upcoming_days: 90, include_past_days: 0 }),
    api.entities(),
  ]);

  return (
    <div className="space-y-10">
      <section>
        <h1 className="text-3xl font-semibold tracking-tight text-ink">Dashboard</h1>
        <p className="mt-1 text-sm text-steel-500">
          {entities.length} entities · {obligations.length} tax obligations in next 90 days
        </p>
      </section>

      <section>
        <div className="mb-3 flex items-baseline justify-between">
          <h2 className="text-lg font-medium text-ink">Upcoming tax obligations</h2>
          <Link href="/tax" className="text-sm text-steel-500 hover:text-ink">
            See all →
          </Link>
        </div>
        <div className="overflow-hidden rounded border border-steel-100 bg-white">
          <table className="w-full text-sm">
            <thead className="bg-steel-50 text-left text-xs uppercase tracking-wide text-steel-500">
              <tr>
                <th className="px-3 py-2">Due</th>
                <th className="px-3 py-2">Days</th>
                <th className="px-3 py-2">Entity</th>
                <th className="px-3 py-2">Modelo</th>
                <th className="px-3 py-2">Period</th>
                <th className="px-3 py-2">Reserve</th>
                <th className="px-3 py-2">Description</th>
              </tr>
            </thead>
            <tbody>
              {obligations.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-3 py-8 text-center text-steel-500">
                    Nothing due in the next 90 days.
                  </td>
                </tr>
              )}
              {obligations.map((o) => {
                const dl = daysUntil(o.due_date);
                const urgent = dl <= 14;
                return (
                  <tr key={o.id} className="border-t border-steel-100 align-top">
                    <td className="px-3 py-2 font-mono text-xs text-ink">{formatDate(o.due_date)}</td>
                    <td
                      className={`px-3 py-2 font-mono text-xs ${
                        urgent ? "text-red-700 font-semibold" : "text-steel-700"
                      }`}
                    >
                      {dl}d
                    </td>
                    <td className="px-3 py-2 font-mono text-xs text-steel-700">{o.entity_code}</td>
                    <td className="px-3 py-2 font-mono text-xs">M{o.modelo}</td>
                    <td className="px-3 py-2 font-mono text-xs text-steel-700">{o.period_label}</td>
                    <td className="px-3 py-2 text-xs text-steel-700">
                      {o.reserve_pct_hint ? `${o.reserve_pct_hint}%` : "—"}
                    </td>
                    <td className="px-3 py-2 text-xs text-ink">{o.name_es}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
