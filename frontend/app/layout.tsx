import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Mundial 2026 — Cartelera",
  description: "Cartelera y predicciones del Mundial de Fútbol 2026.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
