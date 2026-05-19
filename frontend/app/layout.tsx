import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://study.arvexo.ru"),
  title: "Arvexo Study — ЕГЭ по русскому с AI-помощником",
  description: "Готовься к ЕГЭ по русскому с заданиями, статистикой, AI-подсказками и Telegram-ботом.",
  icons: {
    icon: [
      { url: "/favicon-32x32.png", sizes: "32x32", type: "image/png" },
      { url: "/favicon-192x192.png", sizes: "192x192", type: "image/png" },
      { url: "/icon.png", sizes: "512x512", type: "image/png" },
    ],
    apple: [{ url: "/apple-touch-icon.png", sizes: "180x180", type: "image/png" }],
  },
  openGraph: {
    title: "Arvexo Study",
    description: "Подготовка к ЕГЭ по русскому языку с AI-помощником и статистикой.",
    url: "https://study.arvexo.ru",
    siteName: "Arvexo Study",
    type: "website",
    images: [
      {
        url: "/images/arvexo-study-logo.png",
        width: 1024,
        height: 1024,
        alt: "Arvexo Study",
      },
    ],
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ru">
      <body>{children}</body>
    </html>
  );
}
