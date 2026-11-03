const paths = {
  chat: "M5 5h14v11H9l-4 4V5Z M9 9h6 M9 12h4",
  book: "M4 4h6l2 2 2-2h6v15h-6l-2 2-2-2H4V4Z M12 6v15",
  chart: "M4 4v16h16 M8 16v-4 M12 16V7 M16 16v-7",
  spark: "m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5L12 3Z",
  arrow: "M5 12h14 M13 6l6 6-6 6",
  upload: "M12 16V3 M7 8l5-5 5 5 M4 15v5h16v-5",
  file: "M6 3h8l4 4v14H6V3Z M14 3v5h4 M9 12h6 M9 16h4",
  plus: "M12 5v14 M5 12h14", check: "m5 12 4 4L19 6",
  send: "m4 4 17 8-17 8 3-8-3-8Z M7 12h14",
} as const;

export function Icon({ name, className = "size-5" }: { name: keyof typeof paths; className?: string }) {
  return <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" className={className}><path d={paths[name]} /></svg>;
}
