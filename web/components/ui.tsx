export const field = "w-full rounded-lg border border-slate-200 bg-white px-3.5 py-3 text-sm text-slate-800 outline-none transition focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/10 disabled:opacity-50";
export const button = "inline-flex items-center justify-center gap-2 rounded-lg bg-[#183f2e] px-5 py-3 text-sm font-medium text-white transition hover:bg-[#25553f] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-700 disabled:cursor-not-allowed disabled:opacity-50";

export function PageHeading({ eyebrow, title, description, action }: { eyebrow: string; title: string; description: string; action?: React.ReactNode }) {
  return <div className="mb-8 flex flex-wrap items-start justify-between gap-4"><div><p className="mb-3 text-[10px] font-semibold tracking-[.19em] text-emerald-700">{eyebrow}</p><h1 className="text-3xl font-semibold tracking-tight text-[#182d22] sm:text-4xl">{title}</h1><p className="mt-3 max-w-2xl text-sm leading-6 text-slate-500">{description}</p></div>{action}</div>;
}

export function ErrorNotice({ message }: { message: string }) {
  return <p role="alert" className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm leading-6 text-red-700">{message}</p>;
}
