"use client";

import { Bot } from "lucide-react";
import { TelegramLoginButton } from "@/components/TelegramLoginButton";

export function TelegramConnectPanel() {
  return (
    <>
      <div className="dashboard-header">
        <div>
          <p className="eyebrow">Telegram</p>
          <h1>Бот и уведомления</h1>
        </div>
        <a className="primary-button" href="#telegram-connect">
          Подключить Telegram
        </a>
      </div>

      <section id="telegram-connect" className="white-panel connect-panel">
        <Bot size={34} />
        <h2>Аккаунт пока не подключён</h2>
        <p>
          После подключения бот сможет отправлять ежедневное задание, напоминания и краткую
          статистику по подготовке.
        </p>
        <TelegramLoginButton />
        <div className="settings-grid">
          <span>Ежедневное задание</span>
          <span>Краткая статистика</span>
          <span>Напоминания</span>
          <span>AI-подсказки позже</span>
        </div>
      </section>
    </>
  );
}
