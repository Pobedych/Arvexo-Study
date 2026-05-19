import { BrainCircuit } from "lucide-react";
import { AppSidebar } from "@/components/AppSidebar";

export default function AiPage() {
  return (
    <main className="app-shell">
      <AppSidebar active="ai" />
      <section className="dashboard">
        <div className="dashboard-header">
          <div>
            <p className="eyebrow">AI-помощник</p>
            <h1>Подсказки к заданиям</h1>
          </div>
          <a className="primary-button" href="/tasks/5">Попробовать на N5</a>
        </div>

        <div className="dashboard-cards">
          <article className="stat-card">
            <span>Лимит сегодня</span>
            <strong>5 / 5</strong>
            <p>Free-тариф</p>
          </article>
          <article className="stat-card">
            <span>Формат</span>
            <strong>Hint</strong>
            <p>AI не раскрывает готовый ответ</p>
          </article>
          <article className="continue-card ai-card">
            <BrainCircuit size={26} />
            <div>
              <span>Пример подсказки</span>
              <strong>Сначала найди правило</strong>
              <p>Помощник направляет к решению: тема, правило, проверка варианта и типичная ошибка.</p>
            </div>
          </article>
        </div>
      </section>
    </main>
  );
}
