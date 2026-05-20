"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { API_URL } from "@/lib/api";

type TelegramUser = {
  id: number;
  first_name?: string;
  last_name?: string;
  username?: string;
  photo_url?: string;
  auth_date: number;
  hash: string;
};

declare global {
  interface Window {
    onTelegramAuth?: (user: TelegramUser) => void;
  }
}

export function TelegramLoginButton() {
  const router = useRouter();
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [message, setMessage] = useState("");
  const [isLocalHost, setIsLocalHost] = useState(false);
  const botUsername = process.env.NEXT_PUBLIC_TELEGRAM_BOT_USERNAME?.trim().replace(/^@/, "");

  useEffect(() => {
    setIsLocalHost(["localhost", "127.0.0.1"].includes(window.location.hostname));
  }, []);

  useEffect(() => {
    window.onTelegramAuth = async (telegramUser: TelegramUser) => {
      setMessage("");
      try {
        const response = await fetch(`${API_URL}/auth/telegram`, {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(telegramUser),
        });

        if (!response.ok) {
          throw new Error(response.status === 503 ? "Telegram вход не настроен на сервере." : "Не удалось войти через Telegram.");
        }

        router.push("/dashboard");
        router.refresh();
      } catch (error) {
        setMessage(error instanceof Error ? error.message : "Не удалось войти через Telegram.");
      }
    };

    return () => {
      delete window.onTelegramAuth;
    };
  }, [router]);

  useEffect(() => {
    if (!botUsername || isLocalHost || !containerRef.current) return;

    containerRef.current.innerHTML = "";
    const script = document.createElement("script");
    script.async = true;
    script.src = "https://telegram.org/js/telegram-widget.js?22";
    script.setAttribute("data-telegram-login", botUsername);
    script.setAttribute("data-size", "large");
    script.setAttribute("data-radius", "12");
    script.setAttribute("data-userpic", "false");
    script.setAttribute("data-request-access", "write");
    script.setAttribute("data-onauth", "onTelegramAuth(user)");
    containerRef.current.appendChild(script);
  }, [botUsername, isLocalHost]);

  if (!botUsername) {
    return (
      <div className="telegram-login-placeholder">
        <span>Telegram не настроен</span>
        <small>Добавь NEXT_PUBLIC_TELEGRAM_BOT_USERNAME</small>
      </div>
    );
  }

  if (isLocalHost) {
    return (
      <div className="telegram-login-placeholder">
        <span>Telegram Login работает только на домене</span>
        <small>Открой https://study.arvexo.ru после настройки BotFather /setdomain</small>
      </div>
    );
  }

  return (
    <div className="telegram-login-wrap">
      <div ref={containerRef} className="telegram-login-widget" />
      {message && <p className="telegram-login-message">{message}</p>}
    </div>
  );
}
