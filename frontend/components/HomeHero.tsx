"use client";

import { useEffect, useMemo, useState } from "react";
import { ArrowRight, BrainCircuit } from "lucide-react";
import { API_URL } from "@/lib/api";

type User = {
  name: string;
};

type AccountStats = {
  solved_today: number;
  total_attempts: number;
  accuracy_percent: number;
  weak_exam_numbers: number[];
  ai_daily_limit: number;
  ai_remaining_today: number;
};

const examNumbers = Array.from({ length: 18 }, (_, index) => index + 1);

export function HomeHero() {
  const [user, setUser] = useState<User | null>(null);
  const [stats, setStats] = useState<AccountStats | null>(null);

  useEffect(() => {
    let alive = true;

    async function loadPersonalData() {
      try {
        const userResponse = await fetch(`${API_URL}/auth/me`, { credentials: "include" });
        if (!userResponse.ok) return;
        const userPayload = (await userResponse.json()) as User;

        const statsResponse = await fetch(`${API_URL}/stats/me?plan=free`, { credentials: "include" });
        const statsPayload = statsResponse.ok ? ((await statsResponse.json()) as AccountStats) : null;

        if (alive) {
          setUser(userPayload);
          setStats(statsPayload);
        }
      } catch {
        if (alive) {
          setUser(null);
          setStats(null);
        }
      }
    }

    loadPersonalData();
    return () => {
      alive = false;
    };
  }, []);

  const isAuthed = Boolean(user);
  const weakNumbers = stats?.weak_exam_numbers ?? [];
  const demoWeakNumbers = [5, 9, 12];
  const shownWeakNumbers = isAuthed ? weakNumbers : demoWeakNumbers;
  const accuracy = Math.round(stats?.accuracy_percent ?? (isAuthed ? 0 : 82));
  const progressWidth = `${Math.max(4, Math.min(100, accuracy))}%`;
  const nextWeak = weakNumbers[0] ?? 5;
  const title = isAuthed
    ? `${user?.name}, продолжай подготовку`
    : "Готовься к ЕГЭ по русскому с AI-помощником";
  const copy = isAuthed
    ? "Открой задания, продолжи тренировку и следи за реальной статистикой аккаунта."
    : "Решай задания 1-18, получай подсказки без готового ответа и смотри, где уже есть прогресс, а какие темы стоит подтянуть.";

  const gridClasses = useMemo(() => {
    return examNumbers.map((number) => {
      if (!isAuthed) return number === 5 || number === 9 ? "weak" : number < 8 ? "done" : "";
      if (weakNumbers.includes(number)) return "weak";
      return number <= Math.min(18, Math.ceil((stats?.total_attempts ?? 0) / 5)) ? "done" : "";
    });
  }, [isAuthed, stats?.total_attempts, weakNumbers]);

  return (
    <section className="hero-wrap">
      <div className="hero-card">
        <div className="hero-copy">
          <p className="eyebrow">{isAuthed ? "Твой прогресс" : "ЕГЭ по русскому языку"}</p>
          <h1>{title}</h1>
          <p>{copy}</p>
          <div className="hero-actions">
            <a className="primary-button" href={isAuthed ? "/dashboard" : "/register"}>
              {isAuthed ? "Открыть кабинет" : "Начать бесплатно"} <ArrowRight size={18} />
            </a>
            <a className="secondary-button" href={isAuthed ? `/tasks/${nextWeak}` : "#tasks"}>
              {isAuthed ? `Продолжить N${nextWeak}` : "Посмотреть задания"}
            </a>
          </div>
        </div>

        <div className="dashboard-mockup" aria-label="Mockup личного кабинета">
          <div className="mockup-top">
            <span>{isAuthed ? "Личный кабинет" : "Личный кабинет"}</span>
            <strong>
              AI{" "}
              {stats
                ? `${stats.ai_remaining_today} / ${stats.ai_daily_limit}`
                : isAuthed
                  ? "0 / 0"
                  : "5 / 5"}
            </strong>
          </div>
          <div className="mockup-progress">
            <div>
              <span>{isAuthed ? "Точность" : "Прогресс"}</span>
              <strong>{accuracy}%</strong>
            </div>
            <div className="progress-bar">
              <span style={{ width: progressWidth }} />
            </div>
          </div>
          <div className="mockup-exam-grid">
            {examNumbers.map((number, index) => (
              <span key={number} className={gridClasses[index]}>
                {number}
              </span>
            ))}
          </div>
          <div className="mockup-hint">
            <BrainCircuit size={18} />
            <p>
              {isAuthed
                ? "AI-подсказки и статистика учитывают твои реальные решения."
                : "AI-подсказка: найди правило, проверь форму слова и исключи неподходящие варианты."}
            </p>
          </div>
          <div className="mockup-stats">
            <span>Решено сегодня: {stats?.solved_today ?? (isAuthed ? 0 : 12)}</span>
            <span>
              {shownWeakNumbers.length > 0 ? `Слабые: ${shownWeakNumbers.join(", ")}` : "Слабые: пока нет"}
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
