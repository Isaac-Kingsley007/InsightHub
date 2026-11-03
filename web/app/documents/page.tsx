"use client";

import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Icon } from "@/components/icon";
import { button, ErrorNotice, PageHeading } from "@/components/ui";
import { api } from "@/lib/api";

type Document = { id: string; filename: string; created_at: string; chunk_count: number };
type UploadResult = { id: string; filename: string; chunk_count: number; created: boolean };

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [listError, setListError] = useState("");
  const [result, setResult] = useState<UploadResult | null>(null);
  const input = useRef<HTMLInputElement>(null);
  const refresh = useCallback(async () => {
    setLoading(true); setListError("");
    try { setDocuments(await api<Document[]>("/documents", { cache: "no-store" })); }
    catch (cause) { setListError(cause instanceof Error ? cause.message : "Could not load documents."); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { void refresh(); }, [refresh]);
  function choose(selected: File | null) {
    setError(""); setResult(null); setFile(null);
    if (!selected) return;
    if (!/\.(pdf|txt)$/i.test(selected.name)) { setError("Choose a PDF or UTF-8 text file."); return; }
    if (!selected.size || selected.size > 10 * 1024 * 1024) { setError("Choose a nonempty file no larger than 10 MB."); return; }
    setFile(selected);
  }
  async function upload(event: FormEvent) {
    event.preventDefault(); if (!file || busy) return;
    setBusy(true); setError(""); setResult(null);
    const body = new FormData(); body.append("file", file);
    try { setResult(await api<UploadResult>("/ingest", { method: "POST", body })); setFile(null); if (input.current) input.current.value = ""; await refresh(); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Upload failed. Please try again."); }
    finally { setBusy(false); }
  }
  return <>
    <PageHeading eyebrow="A SHARED SOURCE OF TRUTH" title="Your knowledge, connected." description="Give your assistant the policies and documents it needs to answer with confidence." />
    <div className="grid items-start gap-6 xl:grid-cols-[1.6fr_1fr]">
      <form onSubmit={upload} className="rounded-2xl border border-slate-200 bg-white p-6 sm:p-8">
        <h2 className="text-lg font-semibold">Add to your knowledge base</h2>
        <p className="mt-2 text-sm leading-6 text-slate-500">Upload a policy, handbook, or reference document.</p>
        <label onDragOver={event => event.preventDefault()} onDrop={event => { event.preventDefault(); if (!busy) choose(event.dataTransfer.files[0] || null); }} className={`mt-7 flex min-h-60 flex-col items-center justify-center rounded-xl border-2 border-dashed p-7 text-center transition focus-within:ring-2 focus-within:ring-emerald-600 ${busy ? "cursor-wait border-slate-200 bg-slate-50" : "cursor-pointer border-emerald-200 bg-[#f5f9f5] hover:border-emerald-500"}`}>
          <span className="mb-5 flex size-12 items-center justify-center rounded-xl border border-emerald-100 bg-white text-emerald-700"><Icon name={file ? "file" : "upload"} className="size-6" />
          </span>
          <span className="max-w-full wrap-break-word text-sm font-medium">{file ? file.name : "Drop your document here"}
          </span>
          <span className="mt-2 text-xs text-slate-500">{file ? `${(file.size / 1024).toFixed(0)} KB · Ready to upload` : "or click to browse your files"}
          </span>
          <span className="mt-5 text-[10px] tracking-wide text-slate-400">PDF OR TXT · UP TO 10 MB
          </span>
          <input ref={input} type="file" accept=".pdf,.txt" disabled={busy} onChange={event => choose(event.target.files?.[0] || null)} className="sr-only" aria-label="Choose policy document" />
        </label>
        <div className="mt-5 space-y-4">{error &&
          <ErrorNotice message={error} />}
          {result &&
            <div role="status" className="flex gap-3 rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm leading-6 text-emerald-900">
              <Icon name="check" className="mt-1 size-4 shrink-0" />
              <span>
                <strong>{result.created ? "Added to your knowledge base." : "Already in your knowledge base."}
                </strong>
                <br />{result.filename} · {result.chunk_count} searchable chunks
              </span>
            </div>}
          <button disabled={!file || busy} className={`${button} w-full`}>
            <Icon name="upload" className="size-4" />{busy ? "Preparing your document…" : "Upload & add to knowledge base"}
          </button>
          {busy &&
            <p role="status" className="text-center text-xs leading-5 text-slate-500">Large files and API rate limits can take several minutes. Keep this page open; your document is ready only when confirmation appears.
            </p>}
        </div>
      </form>
      <aside className="rounded-2xl border border-[#dae6db] bg-[#eef4ee] p-7">
        <span className="mb-5 flex size-10 items-center justify-center rounded-xl bg-white text-emerald-800"><Icon name="book" /></span>
        <h2 className="text-lg font-semibold">Better context. Better answers.</h2>
        <p className="mt-3 text-sm leading-7 text-slate-600">Your documents become the evidence behind your assistant's responses, with citations you can trace back to the source.
        </p>
        <ol className="mt-7 space-y-5">
          {
            ["Choose a text-based PDF or text file", "We prepare it for relevant searches", "Ask your assistant a policy question"].map(
              (text, index) => <li key={text} className="flex gap-3 text-xs leading-5 text-slate-600"><span className="flex size-5 shrink-0 items-center justify-center rounded-full border border-emerald-200 bg-white text-[10px] text-emerald-800">{index + 1}</span>{text}</li>)}
        </ol>
        <Link href="/chat" className="mt-8 flex items-center gap-2 text-xs font-semibold text-emerald-900">Open the assistant
          <Icon name="arrow" className="size-4" />
        </Link>
      </aside>
    </div>
    <section className="mt-8 overflow-hidden rounded-2xl border border-slate-200 bg-white">
      <div className="flex items-center justify-between border-b border-slate-100 px-6 py-5">
        <h2 className="text-base font-semibold">Document library <span className="ml-2 rounded-md bg-slate-100 px-2 py-1 text-[10px] text-slate-500">{documents.length}</span>
        </h2>
        <button onClick={() => void refresh()} disabled={loading || busy} className="text-xs font-medium text-emerald-800 disabled:opacity-40">Refresh</button>
      </div>{loading ?
        <p role="status" className="p-8 text-sm text-slate-500">Loading your documents…</p> : listError ?
          <div className="p-5">
            <ErrorNotice message={listError} />
          </div> : !documents.length ? <div className="p-10 text-center">
            <Icon name="file" className="mx-auto mb-4 size-7 text-slate-300" />
            <p className="text-sm font-medium">A fresh start for your knowledge base</p>
            <p className="mt-2 text-xs text-slate-500">Upload your first document to get started.
            </p>
          </div> :
            <ul className="divide-y divide-slate-100">{
              documents.map(document =>
                <li key={document.id} className="flex flex-wrap items-center gap-4 px-6 py-5"><span className="flex size-10 items-center justify-center rounded-lg bg-slate-50 text-slate-500"><Icon name="file" /></span>
                  <div className="min-w-0 flex-1">
                    <p className="wrap-break-word text-sm font-medium">{document.filename}</p>
                    <p className="mt-1 text-xs text-slate-400">Added {new Date(document.created_at).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })} · {document.chunk_count} chunks</p>
                  </div>
                  <span className="flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-[10px] font-medium text-emerald-700"><Icon name="check" className="size-3" />Ready for search
                  </span>
                </li>)
            }</ul>
      }
    </section>
  </>;
}
