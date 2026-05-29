"use client";

import { useEffect, useMemo, useState } from "react";
import { ChevronRight } from "lucide-react";
import { API_URL } from "@/lib/api";

type RecentAttempt = {
  task_id: string;
  exam_number: number;
  topic: string;
  is_correct: boolean;
  created_at: string;
};

type AccountStats = {
  total_attempts: number;
  solved_today: number;
  correct_attempts: number;
  wrong_attempts: number;
  accuracy_percent: number;
  weak_exam_numbers: number[];
  ai_daily_limit: number;
  ai_remaining_today: number;
  recent_attempts: RecentAttempt[];
};

export function DashboardStats() {
  const [stats, setStats] = useState<AccountStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let alive = true;

    async function loadStats() {
      try {
        const response = await fetch(`${API_URL}/stats/me`, { credentials: "include" });
        if (!response.ok) throw new Error("Не удалось загрузить статистику аккаунта.");
        const payload = (await response.json()) as AccountStats;
        if (alive) setStats(payload);
      } catch (statsError) {
        if (alive) setError(statsError instanceof Error ? statsError.message : "Не удалось загрузить статистику.");
      } finally {
        if (alive) setLoading(false);
      }
    }

    loadStats();
    return () => {
      alive = false;
    };
  }, []);

  const continueTarget = useMemo(() => {
    const lastAttempt = stats?.recent_attempts[0];
    if (lastAttempt) return `/tasks/${lastAttempt.task_id}`;
    const weakNumber = stats?.weak_exam_numbers[0];
    return weakNumber ? `/tasks/${weakNumber}` : "/tasks/5";
  }, [stats]);

  if (loading) {
    return (
      <div className="white-panel">
        <p className="eyebrow">Статистика</p>
        <h2>Собираем данные аккаунта</h2>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="white-panel">
        <p className="eyebrow">Статистика</p>
        <h2>Нужно войти в аккаунт</h2>
        <p className="panel-copy">{error || "После входа здесь появятся реальные решения и AI-лимиты."}</p>
        <a className="primary-button" href="https://account.arvexo.ru">Войти</a>
      </div>
    );
  }

  const lastAttempt = stats.recent_attempts[0];

  return (
    <>
      <div className="dashboard-cards">
        <article className="stat-card">
          <span>Решено сегодня</span>
          <strong>{stats.solved_today}</strong>
          <p>всего решений: {stats.total_attempts}</p>
        </article>
        <article className="stat-card">
          <span>Точность</span>
          <strong>{Math.round(stats.accuracy_percent)}%</strong>
          <p>верно: {stats.correct_attempts}, ошибок: {stats.wrong_attempts}</p>
        </article>
        <article className="stat-card">
          <span>AI-запросы</span>
          <strong>{stats.ai_remaining_today} / {stats.ai_daily_limit}</strong>
          <p>дневной лимит аккаунта</p>
        </article>
        <article className="stat-card weak-card">
          <span>Слабые задания</span>
          {stats.weak_exam_numbers.length > 0 ? (
            <div className="weak-list">
              {stats.weak_exam_numbers.map((number) => <b key={number}>{number}</b>)}
            </div>
          ) : (
            <strong>Нет</strong>
          )}
          <p>{stats.weak_exam_numbers.length > 0 ? "начни повторение с этих номеров" : "ошибок пока не было"}</p>
        </article>
        <article className="continue-card">
          <div>
            <span>Продолжить подготовку</span>
            <strong>{lastAttempt ? `Задание N${lastAttempt.exam_number}: ${lastAttempt.topic}` : "Задание N5: Паронимы"}</strong>
            <p>
              {lastAttempt
                ? `Ты остановился здесь ${new Date(lastAttempt.created_at).toLocaleString("ru-RU", {
                    dateStyle: "short",
                    timeStyle: "short",
                  })}.`
                : "Начни с базового тренажёра, и последнее задание появится здесь."}
            </p>
          </div>
          <a className="primary-button" href={continueTarget}>
            Продолжить <ChevronRight size={18} />
          </a>
        </article>
      </div>

      <section className="white-panel">
        <div className="panel-title">
          <h2>Последние задания</h2>
          <a href="/tasks">Все задания</a>
        </div>
        <div className="task-list">
          {stats.recent_attempts.length > 0 ? (
            stats.recent_attempts.map((attempt) => (
              <article className="task-row" key={`${attempt.task_id}-${attempt.created_at}`}>
                <span className="task-number">N{attempt.exam_number}</span>
                <div>
                  <h3>{attempt.topic}</h3>
                  <p>{new Date(attempt.created_at).toLocaleString("ru-RU", { dateStyle: "short", timeStyle: "short" })}</p>
                </div>
                <span className={`status ${attempt.is_correct ? "success" : ""}`}>
                  {attempt.is_correct ? "Верно" : "Ошибка"}
                </span>
              </article>
            ))
          ) : (
            <article className="task-row">
              <span className="task-number">N5</span>
              <div>
                <h3>Пока нет решений</h3>
                <p>Начни с любого задания, и история появится здесь.</p>
              </div>
              <a className="secondary-button" href="/tasks/5">Открыть</a>
            </article>
          )}
        </div>
      </section>
    </>
  );
}
