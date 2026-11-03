"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Icon } from "@/components/icon";
import { button, ErrorNotice, PageHeading } from "@/components/ui";
import { postJson } from "@/lib/api";

type Message = { role: "user" | "assistant"; text: string; tools?: string[] };
const suggestions = [
  { icon: "chart", title: "Understand customer churn", text: "How many customers churned, grouped by login frequency?", tag: "CUSTOMER DATA" },
  { icon: "book", title: "Find a policy answer", text: "What does our refund policy say about eligibility and deadlines?", tag: "COMPANY KNOWLEDGE" },
  { icon: "spark", title: "Connect the dots", text: "How many customers churned, and what do our policies say about win-back offers?", tag: "DATA + DOCUMENTS" },
] as const;

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [query, setQuery] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const session = useRef("");
  const bottom = useRef<HTMLDivElement>(null);
  useEffect(() => { bottom.current?.scrollIntoView({ behavior: "smooth", block: "nearest" }); }, [messages, busy]);

  async function send(event: FormEvent) {
    event.preventDefault();
    if (!query.trim() || busy) return;
    const text = query.trim();
    session.current ||= crypto.randomUUID();
    setError(""); setBusy(true);
    setMessages(previous => [...previous, { role: "user", text }]); setQuery("");
    try {
      const result = await postJson<{ answer: string; tools_used: string[] }>("/agent", { query: text, session_id: session.current });
      setMessages(previous => [...previous, { role: "assistant", text: result.answer, tools: result.tools_used }]);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not get an answer."); setQuery(text); }
    finally { setBusy(false); }
  }

  return <>
    <PageHeading eyebrow="YOUR INTELLIGENCE PARTNER" title="A little clarity. A lot of insight." description="Ask about your customers, explore your policies, and turn questions into next steps."
      action={
        <button disabled={busy} onClick={() => { setMessages([]); session.current = ""; setQuery(""); setError(""); }} className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-xs font-medium hover:bg-slate-50 disabled:opacity-50">
          <Icon name="plus" className="size-4" />New conversation</button>} />
    <section className="flex min-h-162.5 flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center gap-3 border-b border-slate-100 px-6 py-4">
        <span className="flex size-8 items-center justify-center rounded-lg bg-emerald-50 text-emerald-800">
          <Icon name="spark" className="size-4" />
        </span>
        <div>
          <h2 className="text-sm font-semibold">InsightHub Assistant</h2>
          <p className="mt-0.5 text-[11px] text-slate-400">Customer data meets company knowledge</p>
        </div>
      </div>
      <div className="max-h-[65vh] min-h-96 flex-1 overflow-y-auto px-5 py-8 sm:px-9" aria-live="polite" aria-busy={busy}>
        {!messages.length ? <div className="mx-auto max-w-3xl py-5 sm:py-10">
          <span className="mx-auto flex size-14 items-center justify-center rounded-2xl bg-[#eef6ef] text-[#41694a]">
            <Icon name="spark" className="size-7" />
          </span>
          <h2 className="mt-6 text-center text-2xl font-semibold tracking-tight">What would you like to understand?</h2>
          <p className="mt-3 text-center text-sm leading-6 text-slate-500">One place for the questions behind better customer experiences.</p>
          <div className="mt-9 grid gap-3 md:grid-cols-3">{suggestions.map(item => <button key={item.title} onClick={() => setQuery(item.text)} className="group rounded-xl border border-slate-200 p-5 text-left transition hover:border-emerald-300 hover:bg-emerald-50/40">
            <Icon name={item.icon} className="mb-6 size-5 text-emerald-800" />
            <p className="text-[9px] font-semibold tracking-widest text-slate-400">{item.tag}</p><h3 className="mt-2 text-sm font-semibold leading-5">{item.title}</h3>
            <p className="mt-2 text-xs leading-5 text-slate-500">{item.text}</p>
            <Icon name="arrow" className="mt-4 size-4 text-slate-400 group-hover:text-emerald-700" /></button>)}
          </div>
          <p className="mt-7 text-center text-xs text-slate-400">Have a policy to add?
            <Link href="/documents" className="font-medium text-emerald-800 underline decoration-emerald-200 underline-offset-4">Build your knowledge base</Link>
          </p>
        </div> :
          <div className="mx-auto max-w-3xl space-y-7">{messages.map((message, index) =>
            <div key={index} className={`flex gap-3 ${message.role === "user" ? "flex-row-reverse" : ""}`}>
              <span className={`flex size-8 shrink-0 items-center justify-center rounded-lg text-[10px] ${message.role === "user" ? "bg-slate-100 text-slate-600" : "bg-emerald-100 text-emerald-800"}`}>{message.role === "user" ? "YOU" : <Icon name="spark" className="size-4" />}
              </span>
              <div className={`max-w-[85%] rounded-xl p-4 ${message.role === "user" ? "bg-[#eef4ef]" : "bg-slate-50"}`}>
                <p className="whitespace-pre-wrap wrap-break-word text-sm leading-7">{message.text}</p>
                {!!message.tools?.length &&
                  <div className="mt-3 flex flex-wrap gap-2 border-t border-slate-200/70 pt-3">{
                    message.tools.map(
                      tool => <span key={tool} className="rounded-md border border-slate-200 bg-white px-2 py-1 text-[10px] text-slate-500">{tool === "run_safe_query" ? "Customer data" : tool === "search_documents" ? "Policy documents" : tool}</span>
                    )}
                  </div>
                }
              </div>
            </div>
          )}
          </div>
        }
        {busy &&
          <p role="status" className="mx-auto mt-7 max-w-3xl animate-pulse text-sm text-emerald-700">Reviewing your question and gathering evidence…
          </p>}
        <div ref={bottom} />
      </div>
      <div className="border-t border-slate-100 bg-white p-4 sm:px-7">{
        error &&
        <div className="mb-3">
          <ErrorNotice message={error} />
        </div>
      }
        <form onSubmit={send} className="flex items-end gap-3 rounded-xl border border-slate-200 bg-slate-50 p-2 pl-4 focus-within:border-emerald-400">
          <label htmlFor="chat-input" className="sr-only">Your question
          </label>
          <textarea id="chat-input" value={query} onChange={event => setQuery(event.target.value)} onKeyDown={event => { if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) { event.preventDefault(); event.currentTarget.form?.requestSubmit(); } }} rows={2} placeholder="Ask a question about your customers or policies…" disabled={busy} className="max-h-40 min-h-12 flex-1 resize-y bg-transparent py-2 text-sm leading-6 outline-none placeholder:text-slate-400" />
          <button type="submit" disabled={!query.trim() || busy} className={`${button} h-11 px-3`} aria-label="Send question">
            <Icon name="send" className="size-4" />
          </button>
        </form>
        <p className="mt-3 text-center text-[10px] text-slate-400">Grounded in your data. Check cited sources before making decisions.
        </p>
      </div>
    </section>
  </>;
}
