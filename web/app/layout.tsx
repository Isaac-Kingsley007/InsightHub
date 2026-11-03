import type { Metadata } from "next";
import "./globals.css";
import { Shell } from "@/components/shell";

export const metadata: Metadata = {
  title: "InsightHub | Customer intelligence",
  description: "Customer answers, grounded knowledge, and churn insights in one workspace.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en" className="h-full antialiased"><body className="min-h-full"><Shell>{children}</Shell></body></html>;
}
