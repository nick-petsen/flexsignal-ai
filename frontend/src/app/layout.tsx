import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FlexSignal AI",
  description: "Read-only decision support dashboard shell for FlexSignal AI."
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
