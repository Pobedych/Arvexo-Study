import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Arvexo Study — ЕГЭ по русскому с AI-помощником",
  description: "Готовься к ЕГЭ по русскому с заданиями, статистикой, AI-подсказками и Telegram-ботом.",
  openGraph: {
    title: "Arvexo Study",
    description: "Подготовка к ЕГЭ по русскому языку с AI-помощником и статистикой.",
    url: "https://study.arvexo.ru",
    siteName: "Arvexo Study",
    type: "website",
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
