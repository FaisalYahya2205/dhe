"use client";

import { useState } from "react";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
  "http://127.0.0.1:8000";

function formatApiError(detail) {
  if (detail == null) return "Terjadi kesalahan.";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => (typeof item?.msg === "string" ? item.msg : JSON.stringify(item)))
      .join(" ");
  }
  return String(detail);
}

export default function Home() {
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    setError(null);
    setResult(null);

    const form = e.currentTarget;
    const input = form.elements.namedItem("file");
    const file = input?.files?.[0];
    if (!file) {
      setError("Pilih file terlebih dahulu.");
      return;
    }

    setLoading(true);
    try {
      const body = new FormData();
      body.append("file", file);
      const res = await fetch(`${API_BASE}/upload`, {
        method: "POST",
        body,
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(formatApiError(data.detail) || res.statusText);
      }
      setResult(data);
      form.reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-lg flex-col justify-center px-4 py-16">
      <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <h1 className="text-xl font-semibold text-slate-900">Upload data</h1>
        <p className="mt-2 text-sm text-slate-600">
          CSV atau Excel:{" "}
          <code className="rounded bg-slate-100 px-1.5 py-0.5 text-xs">
            .csv, .xlsx, .xlsm, .xls
          </code>
          . API:{" "}
          <code className="rounded bg-slate-100 px-1.5 py-0.5 text-xs">
            {API_BASE}
          </code>
        </p>

        <form onSubmit={onSubmit} className="mt-6 space-y-4">
          <div>
            <label
              htmlFor="file"
              className="mb-2 block text-sm font-medium text-slate-700"
            >
              File
            </label>
            <input
              id="file"
              name="file"
              type="file"
              accept=".csv,.xlsx,.xlsm,.xls,text/csv,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
              className="block w-full text-sm text-slate-600 file:mr-4 file:rounded-lg file:border-0 file:bg-slate-900 file:px-4 file:py-2 file:text-sm file:font-medium file:text-white hover:file:bg-slate-800"
              disabled={loading}
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? "Mengunggah…" : "Unggah"}
          </button>
        </form>

        {error ? (
          <p
            className="mt-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800"
            role="alert"
          >
            {error}
          </p>
        ) : null}

        {result ? (
          <div className="mt-4 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-3 text-sm text-emerald-900">
            <p className="font-medium">Berhasil</p>
            <ul className="mt-2 space-y-1 font-mono text-xs text-emerald-800">
              <li>nama: {result.filename}</li>
              <li>ukuran: {result.size_bytes} byte</li>
              <li>content-type: {result.content_type ?? "—"}</li>
              <li className="break-all">sha256: {result.sha256}</li>
            </ul>
          </div>
        ) : null}
      </div>
    </main>
  );
}
