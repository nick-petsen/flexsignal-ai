import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "N&O Predict",
  description: "Read-only decision support dashboard shell for N&O Predict."
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
