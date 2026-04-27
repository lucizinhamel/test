"use client";

import { useState } from "react";
import { api, DocumentRow } from "@/lib/api";

function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString("es-ES", { dateStyle: "medium", timeStyle: "short" });
}

export default function DocumentsClient({ initialDocs }: { initialDocs: DocumentRow[] }) {
  const [docs, setDocs] = useState<DocumentRow[]>(initialDocs);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const [notes, setNotes] = useState("");

  async function uploadFiles(files: FileList | File[]) {
    setBusy(true);
    setError(null);
    try {
      const list = Array.from(files);
      const uploaded: DocumentRow[] = [];
      for (const f of list) {
        const r = await api.uploadDocument(f, title || undefined, notes || undefined);
        uploaded.push(r);
      }
      const merged = [...uploaded, ...docs];
      const seen = new Set<string>();
      const dedup = merged.filter((d) => (seen.has(d.id) ? false : (seen.add(d.id), true)));
      setDocs(dedup);
      setTitle("");
      setNotes("");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-10">
      <section>
        <h1 className="text-3xl font-semibold tracking-tight text-ink">Documents</h1>
        <p className="mt-1 max-w-3xl text-sm text-steel-500">
          Tax documents, invoices, receipts, contracts, DUAs, BoLs. Files are SHA-256 hashed and
          stored content-addressable — uploading the same bytes twice is automatically deduplicated.
          Nothing leaves your machine.
        </p>
      </section>

      <section className="rounded border border-dashed border-steel-300 bg-white p-6">
        <h2 className="text-lg font-medium text-ink">Upload</h2>
        <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2">
          <label className="text-sm">
            <span className="text-xs text-steel-500">Title (optional)</span>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Modelo 303 Q1 2026 — proof of filing"
              className="mt-1 w-full rounded border border-steel-100 px-3 py-2 text-sm focus:border-ink focus:outline-none"
            />
          </label>
          <label className="text-sm">
            <span className="text-xs text-steel-500">Notes (optional)</span>
            <input
              type="text"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. supplier NIF, invoice number, project tag"
              className="mt-1 w-full rounded border border-steel-100 px-3 py-2 text-sm focus:border-ink focus:outline-none"
            />
          </label>
        </div>
        <div className="mt-4">
          <input
            type="file"
            multiple
            disabled={busy}
            onChange={(e) => {
              if (e.target.files && e.target.files.length > 0) {
                uploadFiles(e.target.files);
                e.target.value = "";
              }
            }}
            className="block w-full text-sm text-steel-700 file:mr-3 file:rounded file:border-0 file:bg-ink file:px-4 file:py-2 file:text-sm file:text-white hover:file:bg-steel-700"
          />
        </div>
        {busy && <p className="mt-3 text-xs text-steel-500">Uploading…</p>}
        {error && <p className="mt-3 text-xs text-red-700">{error}</p>}
      </section>

      <section>
        <h2 className="mb-3 text-lg font-medium text-ink">Vault ({docs.length})</h2>
        <div className="overflow-hidden rounded border border-steel-100 bg-white">
          <table className="w-full text-sm">
            <thead className="bg-steel-50 text-left text-xs uppercase tracking-wide text-steel-500">
              <tr>
                <th className="px-3 py-2">Uploaded</th>
                <th className="px-3 py-2">Filename</th>
                <th className="px-3 py-2">Title</th>
                <th className="px-3 py-2">Notes</th>
                <th className="px-3 py-2">Type</th>
                <th className="px-3 py-2">Size</th>
                <th className="px-3 py-2">SHA-256</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {docs.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-3 py-8 text-center text-steel-500">
                    No documents yet — upload above.
                  </td>
                </tr>
              )}
              {docs.map((d) => (
                <tr key={d.id} className="border-t border-steel-100 align-top">
                  <td className="px-3 py-2 font-mono text-xs text-steel-700">
                    {formatDate(d.uploaded_at)}
                  </td>
                  <td className="px-3 py-2 text-xs text-ink">{d.original_filename}</td>
                  <td className="px-3 py-2 text-xs text-steel-700">{d.title ?? "—"}</td>
                  <td className="px-3 py-2 text-xs text-steel-700">{d.notes ?? "—"}</td>
                  <td className="px-3 py-2 font-mono text-[10px] text-steel-500">{d.mime_type}</td>
                  <td className="px-3 py-2 font-mono text-xs text-steel-700">
                    {formatBytes(d.byte_size)}
                  </td>
                  <td className="px-3 py-2 font-mono text-[10px] text-steel-500">
                    {d.sha256.slice(0, 16)}…
                  </td>
                  <td className="px-3 py-2 text-xs">
                    <a
                      href={`/api/documents/${d.id}/download`}
                      className="text-steel-700 underline hover:text-ink"
                    >
                      download
                    </a>
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
