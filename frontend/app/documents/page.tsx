import DocumentsClient from "./DocumentsClient";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function DocumentsPage() {
  const docs = await api.documents();
  return <DocumentsClient initialDocs={docs} />;
}
