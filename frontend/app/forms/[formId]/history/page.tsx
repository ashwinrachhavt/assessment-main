"use client";

import { fetcher } from "@/utils/fetcher";
import Link from "next/link";
import useSWR from "swr";

function formatDate(raw: string | undefined) {
  if (!raw) return "Unknown";
  const iso = raw.endsWith("Z") ? raw : raw + "Z";
  return new Date(iso).toLocaleString();
}

function prettyValue(v: any) {
  if (v === null || v === undefined) return "null";
  if (typeof v === "string") return v;
  return JSON.stringify(v);
}

export default function HistoryPage({ params }: { params: { formId: string } }) {
  const { data, error, isLoading } = useSWR({ url: `forms/${params.formId}/history` }, fetcher);

  return (
    <main className="min-h-screen p-8">
      <div className="max-w-3xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-semibold">Form History</h1>
          <Link className="text-sm text-blue-700 hover:underline" href="/">
            Back to chats
          </Link>
        </div>

        <div className="text-sm text-neutral-700">
          <span className="font-semibold">Form ID:</span>{" "}
          <span className="font-mono">{params.formId}</span>
        </div>

        {isLoading && <div className="text-sm text-neutral-600">Loading…</div>}
        {error && <div className="text-sm text-red-700">Failed to load history</div>}

        {Array.isArray(data) && data.length === 0 && (
          <div className="text-sm text-neutral-600">No history found yet.</div>
        )}

        {Array.isArray(data) && data.length > 0 && (
          <div className="space-y-3">
            {data.map((rev: any) => (
              <div
                key={rev.id}
                className="rounded-md border border-neutral-200 bg-white p-4 shadow-sm"
              >
                <div className="flex items-center justify-between">
                  <div className="text-sm">
                    <span className="font-semibold">Event:</span> {rev.event_type}
                    {rev.source ? <span className="text-neutral-600"> ({rev.source})</span> : null}
                  </div>
                  <div className="text-xs text-neutral-600">{formatDate(rev.created_at)}</div>
                </div>

                {Array.isArray(rev.changes) && rev.changes.length > 0 ? (
                  <div className="mt-3 space-y-1">
                    {rev.changes.map((ch: any) => (
                      <div key={ch.id} className="text-sm">
                        <span className="font-mono">{ch.field}</span>:{" "}
                        <span className="text-neutral-700">{prettyValue(ch.old_value)}</span>{" "}
                        <span className="text-neutral-500">→</span>{" "}
                        <span className="text-neutral-900">{prettyValue(ch.new_value)}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="mt-3 text-sm text-neutral-600">
                    No field-level changes recorded.
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
