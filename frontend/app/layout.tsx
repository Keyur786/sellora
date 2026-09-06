import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "@/components/providers";
import { Sidebar } from "@/components/layout/sidebar";

export const metadata: Metadata = {
  title: "Sellora | Real Profitability for Indian Online Sellers",
  description:
    "Real-time net profit analytics, marketplace fee audits, and unit economics for Amazon India and Flipkart sellers.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased">
        <Providers>
          <div className="flex min-h-screen">
            <Sidebar />
            <div className="flex flex-1 flex-col pl-64">{children}</div>
          </div>
        </Providers>
      </body>
    </html>
  );
}
