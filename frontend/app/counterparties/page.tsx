import CounterpartiesClient from "./CounterpartiesClient";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function Page() {
  const items = await api.counterparties();
  return <CounterpartiesClient initial={items} />;
}
