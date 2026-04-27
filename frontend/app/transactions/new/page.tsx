import { api } from "@/lib/api";
import NewTransactionClient from "./NewTransactionClient";

export const dynamic = "force-dynamic";

export default async function Page() {
  const [entities, counterparties] = await Promise.all([api.entities(), api.counterparties()]);
  return <NewTransactionClient entities={entities} counterparties={counterparties} />;
}
