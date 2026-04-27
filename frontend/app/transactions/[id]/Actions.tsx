"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function TransactionDetailActions({
  txId,
  status,
}: {
  txId: string;
  status: string;
}) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (status !== "draft") {
    return (
      <p className="text-xs text-steel-500">
        {status === "posted"
          ? "Posted entries are immutable. To correct, record a new entry that reverses this one."
          : "This entry is void."}
      </p>
    );
  }

  async function post() {
    setBusy(true);
    setError(null);
    try {
      await api.postTransaction(txId);
      router.refresh();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed");
    } finally {
      setBusy(false);
    }
  }

  async function voidIt() {
    if (!confirm("Mark this draft as void?")) return;
    setBusy(true);
    try {
      await api.voidTransaction(txId);
      router.refresh();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex items-center gap-3">
      <button
        onClick={post}
        disabled={busy}
        className="rounded bg-ink px-4 py-2 text-sm text-white hover:bg-steel-700 disabled:opacity-40"
      >
        Post entry
      </button>
      <button
        onClick={voidIt}
        disabled={busy}
        className="rounded border border-steel-300 px-4 py-2 text-sm text-steel-700 hover:bg-steel-50 disabled:opacity-40"
      >
        Void
      </button>
      {error && <span className="text-xs text-red-700">{error}</span>}
    </div>
  );
}
