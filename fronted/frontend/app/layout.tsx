import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PPTAgent - AI Task Management Platform",
  description: "AI-powered presentation generation platform with async task execution",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
