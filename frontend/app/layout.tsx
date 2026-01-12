import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RAGMesh - Insurance RAG Framework",
  description: "Production-Grade Insurance RAG Framework with Tri-Modal Retrieval",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
