"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Icon } from "./icon";

const navigation = [
  { href: "/chat", label: "Assistant", icon: "chat" },
  { href: "/documents", label: "Knowledge base", icon: "book" },
  { href: "/predictions", label: "Churn predictions", icon: "chart" },
] as const;

export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const active = navigation.find(item => pathname.startsWith(item.href));
  return <div className="min-h-screen lg:pl-64">
    <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-white focus:p-3">Skip to content</a>
    <aside className="bg-[#12251e] text-white lg:fixed lg:inset-y-0 lg:left-0 lg:flex lg:w-64 lg:flex-col">
      <Link href="/chat" className="flex items-center gap-3 px-6 py-7"><span className="flex size-9 items-center justify-center rounded-xl bg-[#b8f2d0] text-[#143b2a]"><Icon name="spark" /></span><span className="text-xl font-semibold tracking-tight">InsightHub<span className="text-[#a6d8ba]">.</span></span></Link>
      <div className="hidden px-6 pb-3 text-[10px] font-semibold tracking-[.19em] text-[#77988a] lg:block">YOUR WORKSPACE</div>
      <nav aria-label="Main navigation" className="flex gap-1 overflow-x-auto px-3 pb-4 lg:flex-col lg:px-4">{navigation.map(item => <Link key={item.href} href={item.href} aria-current={pathname.startsWith(item.href) ? "page" : undefined} className={`flex shrink-0 items-center gap-3 rounded-lg px-3 py-3 text-sm transition-colors ${pathname.startsWith(item.href) ? "bg-[#294435] text-[#c4f8d7]" : "text-[#b0c4ba] hover:bg-white/5 hover:text-white"}`}><Icon name={item.icon} /><span>{item.label}</span>{pathname.startsWith(item.href) && <span className="ml-auto hidden size-1.5 rounded-full bg-[#b8f2d0] lg:block" />}</Link>)}</nav>
      <div className="mx-5 mt-auto hidden border-t border-white/10 py-6 lg:block"><div className="mb-4 rounded-xl border border-white/10 bg-white/4 p-4"><Icon name="spark" className="mb-3 size-5 text-[#b8f2d0]" /><p className="text-sm font-medium">Clarity for every conversation.</p><p className="mt-2 text-xs leading-5 text-[#92afa0]">Bring customer data and company knowledge together.</p></div><div className="flex items-center gap-3 pt-2"><span className="flex size-8 items-center justify-center rounded-full bg-[#385145] text-xs">CS</span><div><p className="text-xs font-medium">Customer Success</p><p className="mt-1 text-[10px] text-[#86a694]">Orbitel workspace</p></div></div></div>
    </aside>
    <header className="flex h-18 items-center justify-between border-b border-slate-200/80 bg-white px-5 sm:px-9"><div className="flex items-center gap-2 text-xs text-slate-400"><span>Workspace</span><span>/</span><span className="font-medium text-slate-700">{active?.label || "InsightHub"}</span></div><span className="rounded-full border border-slate-200 px-3 py-1.5 text-[10px] font-medium tracking-wide text-slate-500">CUSTOMER INTELLIGENCE</span></header>
    <main id="main" className="mx-auto max-w-7xl px-5 py-8 sm:px-9 lg:py-10">{children}</main>
  </div>;
}
