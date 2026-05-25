import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Insurance Document Assistant",
  description: "Multi-modal RAG-based insurance document Q&A system",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
