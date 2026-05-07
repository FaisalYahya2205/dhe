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

function clamp(n, min, max) {
  return Math.max(min, Math.min(max, n));
}

function percent(n) {
  const x = Number(n);
  if (!Number.isFinite(x)) return "—";
  return `${x.toFixed(2)}%`;
}

function StatCard({ label, value, helper }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <div className="text-xs font-medium uppercase tracking-wide text-slate-500">
        {label}
      </div>
      <div className="mt-1 text-2xl font-semibold text-slate-900">{value}</div>
      {helper ? (
        <div className="mt-1 text-xs text-slate-500">{helper}</div>
      ) : null}
    </div>
  );
}

function ProgressBar({ value, color = "bg-emerald-600" }) {
  const v = clamp(Number(value) || 0, 0, 100);
  return (
    <div className="h-2 w-full rounded-full bg-slate-100">
      <div className={`h-2 rounded-full ${color}`} style={{ width: `${v}%` }} />
    </div>
  );
}

function AnalysisDashboard({ result }) {
  const a = result?.analysis;
  if (!a) return null;

  const exactHealth = a.exact_dedupe_health_pct;
  const fuzzyHealth = a.fuzzy_dedupe_health_pct;
  const typo = a.typo;

  return (
    <div className="mt-4 space-y-4">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatCard label="Baris (input)" value={a.row_count_input} />
        <StatCard label="Kolom" value={a.column_count} />
        <StatCard
          label="Duplikat eksak"
          value={a.exact_duplicate_rows}
          helper="Baris identik (semua kolom sama)"
        />
        <StatCard
          label="Unik setelah eksak"
          value={a.rows_after_exact_dedupe}
          helper="drop_duplicates()"
        />
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2 className="text-sm font-semibold text-slate-900">
              Kesehatan data (duplikasi)
            </h2>
            <p className="mt-1 text-xs text-slate-600">
              Eksak = unik/total. Fuzzy = kelompok/total (rapidfuzz pada fingerprint per baris).
            </p>
          </div>
          <div className="text-right">
            <div className="text-xs font-medium text-slate-500">Ambang fuzzy</div>
            <div className="text-lg font-semibold text-slate-900">
              {a.fuzzy_threshold}
            </div>
          </div>
        </div>

        <div className="mt-4 space-y-4">
          <div>
            <div className="flex items-center justify-between">
              <div className="text-xs font-medium text-slate-700">Eksak</div>
              <div className="text-xs font-semibold text-slate-900">
                {percent(exactHealth)}
              </div>
            </div>
            <div className="mt-2">
              <ProgressBar value={exactHealth} color="bg-emerald-600" />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between">
              <div className="text-xs font-medium text-slate-700">Fuzzy</div>
              <div className="text-xs font-semibold text-slate-900">
                {percent(fuzzyHealth)}
              </div>
            </div>
            <div className="mt-2">
              <ProgressBar value={fuzzyHealth} color="bg-sky-600" />
            </div>
            <div className="mt-2 text-xs text-slate-600">
              Kelompok (fuzzy):{" "}
              <span className="font-mono text-slate-900">
                {a.rows_after_fuzzy_grouping}
              </span>
              {" · "}
              Redundan (mirip):{" "}
              <span className="font-mono text-slate-900">
                {a.fuzzy_redundant_rows_among_exact_unique}
              </span>
            </div>
            {a.fuzzy_skipped ? (
              <div className="mt-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
                {a.fuzzy_skip_reason}
              </div>
            ) : null}
          </div>
        </div>
      </div>

      <details className="rounded-2xl border border-slate-200 bg-white p-5">
        <summary className="cursor-pointer select-none text-sm font-semibold text-slate-900">
          Detail JSON
        </summary>
        <pre className="mt-3 overflow-auto rounded-xl bg-slate-950 p-4 text-xs text-slate-100">
{JSON.stringify(a, null, 2)}
        </pre>
      </details>

      <div className="rounded-2xl border border-slate-200 bg-white p-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2 className="text-sm font-semibold text-slate-900">Typos (teks)</h2>
            <p className="mt-1 text-xs text-slate-600">
              Saran normalisasi nilai teks per kolom (contoh: <span className="font-mono">jakrta → jakarta</span>).
              Ini heuristik berbasis kemiripan rapidfuzz + frekuensi.
            </p>
          </div>
          <div className="text-right">
            <div className="text-xs font-medium text-slate-500">Ambang typo</div>
            <div className="text-lg font-semibold text-slate-900">
              {typo?.threshold ?? "—"}
            </div>
          </div>
        </div>

        {typo?.suggestions?.length ? (
          <div className="mt-4 overflow-auto rounded-xl border border-slate-200">
            <table className="w-full min-w-[720px] text-left text-xs">
              <thead className="bg-slate-50 text-slate-600">
                <tr>
                  <th className="px-4 py-3 font-medium">Kolom</th>
                  <th className="px-4 py-3 font-medium">Dari</th>
                  <th className="px-4 py-3 font-medium">Ke</th>
                  <th className="px-4 py-3 font-medium">Score</th>
                  <th className="px-4 py-3 font-medium">Count (from)</th>
                  <th className="px-4 py-3 font-medium">Count (to)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {typo.suggestions.slice(0, 50).map((s, idx) => (
                  <tr key={`${s.column}-${s.from}-${idx}`} className="hover:bg-slate-50">
                    <td className="px-4 py-3 font-medium text-slate-900">{s.column}</td>
                    <td className="px-4 py-3 font-mono text-slate-800">{s.from}</td>
                    <td className="px-4 py-3 font-mono text-slate-900">{s.to}</td>
                    <td className="px-4 py-3 font-mono text-slate-700">{s.score}</td>
                    <td className="px-4 py-3 font-mono text-slate-700">{s.from_count}</td>
                    <td className="px-4 py-3 font-mono text-slate-700">{s.to_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="mt-3 text-xs text-slate-500">
            Tidak ada saran typo (atau kolom teks kosong/terlalu banyak nilai unik).
          </p>
        )}

        {typo?.columns_skipped && Object.keys(typo.columns_skipped).length ? (
          <details className="mt-3">
            <summary className="cursor-pointer select-none text-xs font-medium text-slate-700">
              Kolom yang dilewati
            </summary>
            <pre className="mt-2 overflow-auto rounded-xl bg-slate-950 p-4 text-xs text-slate-100">
{JSON.stringify(typo.columns_skipped, null, 2)}
            </pre>
          </details>
        ) : null}
      </div>
    </div>
  );
}

export default function Home() {
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [fuzzyThreshold, setFuzzyThreshold] = useState(88);

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
      const q = new URLSearchParams({
        fuzzy_threshold: String(fuzzyThreshold),
      });
      const res = await fetch(`${API_BASE}/upload/analyze?${q}`, {
        method: "POST",
        body,
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(formatApiError(data.detail) || res.statusText);
      }
      setResult(data);
      setHistory((prev) => [{ at: Date.now(), ...data }, ...prev].slice(0, 10));
      form.reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto min-h-screen max-w-4xl px-4 py-12">
      <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-xl font-semibold text-slate-900">
              Dashboard analisa data
            </h1>
            <p className="mt-1 text-sm text-slate-600">
              Upload CSV / Excel lalu lihat duplikasi eksak mirip (fuzzy).
            </p>
          </div>
          <div className="text-xs text-slate-500">
            API{" "}
            <code className="rounded bg-slate-100 px-1.5 py-0.5 text-xs text-slate-700">
              {API_BASE}
            </code>
          </div>
        </div>

        <form onSubmit={onSubmit} className="mt-6 space-y-4">
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="sm:col-span-2">
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
              <p className="mt-1 text-xs text-slate-500">
                Didukung: <span className="font-mono">.csv .xlsx .xlsm .xls</span>
              </p>
            </div>
            <div>
              <label
                htmlFor="fuzzy"
                className="mb-2 block text-sm font-medium text-slate-700"
              >
                Ambang fuzzy
              </label>
              <input
                id="fuzzy"
                name="fuzzy"
                type="number"
                min={50}
                max={100}
                value={fuzzyThreshold}
                onChange={(e) => setFuzzyThreshold(Number(e.target.value) || 88)}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                disabled={loading}
              />
              <p className="mt-1 text-xs text-slate-500">
                88–95 biasanya titik awal yang baik.
              </p>
            </div>
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? "Menganalisa…" : "Unggah analisa"}
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
          <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 p-5">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <div className="text-xs font-medium uppercase tracking-wide text-slate-500">
                  Hasil terbaru
                </div>
                <div className="mt-1 text-sm font-semibold text-slate-900">
                  {result.filename}
                </div>
                <div className="mt-1 text-xs text-slate-600">
                  {result.size_bytes} byte ·{" "}
                  <span className="font-mono">{result.content_type ?? "—"}</span>
                </div>
              </div>
              <div className="text-xs text-slate-500 sm:text-right">
                sha256
                <div className="mt-1 max-w-md break-all rounded-lg bg-white px-2 py-1 font-mono text-[11px] text-slate-700">
                  {result.sha256}
                </div>
              </div>
            </div>

            <AnalysisDashboard result={result} />
          </div>
        ) : null}

        <div className="mt-8">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-900">
              Riwayat analisa (session)
            </h2>
            {history.length ? (
              <button
                type="button"
                onClick={() => setHistory([])}
                className="text-xs font-medium text-slate-600 hover:text-slate-900"
              >
                Clear
              </button>
            ) : (
              <span className="text-xs text-slate-500">Kosong</span>
            )}
          </div>

          {history.length ? (
            <div className="mt-3 overflow-auto rounded-2xl border border-slate-200 bg-white">
              <table className="w-full min-w-[760px] text-left text-xs">
                <thead className="sticky top-0 bg-slate-50 text-slate-600">
                  <tr>
                    <th className="px-4 py-3 font-medium">Waktu</th>
                    <th className="px-4 py-3 font-medium">File</th>
                    <th className="px-4 py-3 font-medium">Rows</th>
                    <th className="px-4 py-3 font-medium">Dup (eksak)</th>
                    <th className="px-4 py-3 font-medium">Health (eksak)</th>
                    <th className="px-4 py-3 font-medium">Health (fuzzy)</th>
                    <th className="px-4 py-3 font-medium">Ambang</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {history.map((h) => (
                    <tr key={`${h.sha256}-${h.at}`} className="hover:bg-slate-50">
                      <td className="px-4 py-3 text-slate-600">
                        {new Date(h.at).toLocaleTimeString()}
                      </td>
                      <td className="px-4 py-3 font-medium text-slate-900">
                        {h.filename}
                      </td>
                      <td className="px-4 py-3 font-mono text-slate-800">
                        {h.analysis?.row_count_input ?? "—"}
                      </td>
                      <td className="px-4 py-3 font-mono text-slate-800">
                        {h.analysis?.exact_duplicate_rows ?? "—"}
                      </td>
                      <td className="px-4 py-3 font-mono text-slate-800">
                        {percent(h.analysis?.exact_dedupe_health_pct)}
                      </td>
                      <td className="px-4 py-3 font-mono text-slate-800">
                        {percent(h.analysis?.fuzzy_dedupe_health_pct)}
                      </td>
                      <td className="px-4 py-3 font-mono text-slate-700">
                        {h.analysis?.fuzzy_threshold ?? "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="mt-2 text-xs text-slate-500">
              Upload beberapa file untuk membandingkan hasilnya.
            </p>
          )}
        </div>
      </div>
    </main>
  );
}
