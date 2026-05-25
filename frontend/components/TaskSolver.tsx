"use client";

import { FormEvent, KeyboardEvent, useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { BrainCircuit, CheckCircle2, Clock, Target } from "lucide-react";
import { API_URL } from "@/lib/api";

type Task = {
  id: string;
  exam_number: number;
  topic: string;
  condition: string;
  difficulty: string;
  status: string;
};

type TaskListItem = Pick<Task, "id" | "exam_number" | "topic" | "difficulty" | "status">;

type SubmitResult = {
  is_correct: boolean;
  correct_answer: string;
  normalized_answer: string;
  explanation: string | null;
};

type HintResult = {
  hint: string;
  remaining_today: number;
};

type AccountStats = {
  total_attempts: number;
  solved_today: number;
  accuracy_percent: number;
  weak_exam_numbers: number[];
  ai_daily_limit: number;
  ai_remaining_today: number;
};

export function TaskSolver() {
  const params = useParams<{ id: string }>();
  const taskParam = params.id;
  const [task, setTask] = useState<Task | null>(null);
  const [answer, setAnswer] = useState("");
  const [result, setResult] = useState<SubmitResult | null>(null);
  const [hint, setHint] = useState<HintResult | null>(null);
  const [stats, setStats] = useState<AccountStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [checking, setChecking] = useState(false);
  const [hintLoading, setHintLoading] = useState(false);
  const [error, setError] = useState("");

  const difficultyLabel = useMemo(() => {
    if (!task) return "";
    return task.difficulty === "hard" ? "Сложная" : task.difficulty === "easy" ? "Лёгкая" : "Средняя";
  }, [task]);
  const taskContent = useMemo(() => (task ? splitTaskContent(task.condition) : null), [task]);

  useEffect(() => {
    let alive = true;

    async function loadTask() {
      setLoading(true);
      setError("");
      try {
        const loadedTask = await resolveTask(taskParam);
        if (alive) setTask(loadedTask);
      } catch (loadError) {
        if (alive) setError(loadError instanceof Error ? loadError.message : "Не удалось загрузить задание.");
      } finally {
        if (alive) setLoading(false);
      }
    }

    loadTask();
    loadAccountStats();
    return () => {
      alive = false;
    };
  }, [taskParam]);

  async function loadAccountStats() {
    try {
      const response = await fetch(`${API_URL}/stats/me`, { credentials: "include" });
      if (!response.ok) return;
      setStats((await response.json()) as AccountStats);
    } catch {
      setStats(null);
    }
  }

  async function checkCurrentAnswer() {
    if (!task || checking) return;

    const trimmedAnswer = answer.trim();
    if (!trimmedAnswer) {
      setError("Введите ответ перед проверкой.");
      return;
    }

    setChecking(true);
    setError("");
    setResult(null);
    try {
      const response = await fetch(`${API_URL}/tasks/${task.id}/submit`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answer: trimmedAnswer }),
      });
      if (response.status === 401) throw new Error("Войдите в аккаунт, чтобы сохранить решение в статистику.");
      if (!response.ok) throw new Error("Не удалось проверить ответ.");
      setResult((await response.json()) as SubmitResult);
      await loadAccountStats();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Не удалось проверить ответ.");
    } finally {
      setChecking(false);
    }
  }

  async function submitAnswer(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await checkCurrentAnswer();
  }

  async function submitOnEnter(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key !== "Enter") return;
    event.preventDefault();
    await checkCurrentAnswer();
  }

  async function requestHint() {
    if (!task || hintLoading) return;

    setHintLoading(true);
    setError("");
    try {
      const response = await fetch(`${API_URL}/tasks/${task.id}/hint`, {
        method: "POST",
        credentials: "include",
      });
      if (response.status === 401) throw new Error("Войдите в аккаунт, чтобы использовать AI-подсказки.");
      if (response.status === 429) throw new Error("Лимит AI-подсказок на сегодня исчерпан.");
      if (!response.ok) throw new Error("AI-подсказка временно недоступна.");
      setHint((await response.json()) as HintResult);
      await loadAccountStats();
    } catch (hintError) {
      setError(hintError instanceof Error ? hintError.message : "AI-подсказка временно недоступна.");
    } finally {
      setHintLoading(false);
    }
  }

  if (loading) {
    return (
      <TaskShell>
        <article className="task-card">
          <p className="eyebrow">Загрузка</p>
          <h1>Открываем задание</h1>
          <p className="task-condition">Секунду, получаем условие и параметры проверки.</p>
        </article>
      </TaskShell>
    );
  }

  if (!task) {
    return (
      <TaskShell>
        <article className="task-card">
          <p className="eyebrow">Ошибка</p>
          <h1>Задание не найдено</h1>
          <p className="task-condition">{error || "Попробуйте открыть список заданий и выбрать другой номер."}</p>
        </article>
      </TaskShell>
    );
  }

  return (
    <TaskShell>
      <article className="task-card">
        <div className="task-card-top">
          <span className="eyebrow">Задание N{task.exam_number}</span>
          <span className="status success">{difficultyLabel} сложность</span>
        </div>
        <h1>{task.topic}</h1>
        {taskContent && (
          <div className="task-body">
            <section className="task-prompt-block" aria-label="Формулировка задания">
              <span>Что нужно сделать</span>
              <p>{taskContent.prompt}</p>
            </section>

            {taskContent.context.length > 0 && (
              <section className="task-context-block" aria-label="Условие задания">
                <span>{taskContent.contextLabel}</span>
                <div className="task-condition">
                  {taskContent.context.map((line, index) => (
                    <p key={`${line}-${index}`} className={/^\d+[\).]/.test(line) ? "task-option-line" : undefined}>
                      {line}
                    </p>
                  ))}
                </div>
              </section>
            )}
          </div>
        )}
        <form onSubmit={submitAnswer}>
          <label className="answer-field">
            <span>Ваш ответ</span>
            <input
              value={answer}
              onChange={(event) => setAnswer(event.target.value)}
              onKeyDown={submitOnEnter}
              placeholder="Введите слово или последовательность цифр"
              autoComplete="off"
            />
          </label>
          <div className="task-actions">
            <button className="primary-button" type="submit" disabled={checking}>
              {checking ? "Проверяем..." : "Проверить"} <CheckCircle2 size={18} />
            </button>
            <button className="secondary-button" type="button" onClick={requestHint} disabled={hintLoading}>
              {hintLoading ? "Готовим подсказку..." : "Получить подсказку AI"} <BrainCircuit size={18} />
            </button>
          </div>
        </form>

        {error && <p className="task-message error">{error}</p>}

        {result && (
          <div className={`task-result ${result.is_correct ? "correct" : "wrong"}`}>
            <strong>{result.is_correct ? "Правильно" : "Неправильно"}</strong>
            {!result.is_correct && <p>Правильный ответ: {result.correct_answer}</p>}
            {result.explanation && <p>{result.explanation}</p>}
          </div>
        )}

        {hint && (
          <div className="task-hint">
            <BrainCircuit size={18} />
            <div>
              <strong>AI-подсказка</strong>
              <p>{hint.hint}</p>
              <small>Осталось сегодня: {hint.remaining_today}</small>
            </div>
          </div>
        )}
      </article>

      <aside className="task-aside">
        <article>
          <BrainCircuit size={20} />
          <span>Лимит AI</span>
          <strong>{stats ? `${stats.ai_remaining_today} / ${stats.ai_daily_limit}` : "..."}</strong>
        </article>
        <article>
          <Target size={20} />
          <span>Прогресс</span>
          <strong>{stats ? `${stats.total_attempts} решено` : "..."}</strong>
        </article>
        <article>
          <Clock size={20} />
          <span>Точность</span>
          <strong>{stats ? `${Math.round(stats.accuracy_percent)}%` : "..."}</strong>
        </article>
        {stats && stats.weak_exam_numbers.length > 0 && (
          <article>
            <Target size={20} />
            <span>Слабые номера</span>
            <strong>{stats.weak_exam_numbers.map((number) => `N${number}`).join(", ")}</strong>
          </article>
        )}
      </aside>
    </TaskShell>
  );
}

function TaskShell({ children }: { children: React.ReactNode }) {
  return <section className="task-layout">{children}</section>;
}

async function resolveTask(taskParam: string): Promise<Task> {
  if (/^\d+$/.test(taskParam)) {
    const listResponse = await fetch(`${API_URL}/tasks?exam_number=${taskParam}`, { credentials: "include" });
    if (!listResponse.ok) throw new Error("Не удалось найти задание по номеру ЕГЭ.");
    const tasks = (await listResponse.json()) as TaskListItem[];
    const firstTask = tasks[0];
    if (!firstTask) throw new Error("Для этого номера пока нет активных заданий.");
    return fetchTask(firstTask.id);
  }

  return fetchTask(taskParam);
}

async function fetchTask(taskId: string): Promise<Task> {
  const response = await fetch(`${API_URL}/tasks/${taskId}`, { credentials: "include" });
  if (!response.ok) throw new Error("Не удалось загрузить задание.");
  return (await response.json()) as Task;
}

function splitTaskContent(condition: string): { prompt: string; context: string[]; contextLabel: string } {
  const lines = condition
    .split(/\n+/)
    .map((line) => line.trim())
    .filter(Boolean);

  if (lines.length <= 1) {
    return { prompt: condition.trim(), context: [], contextLabel: "Условие" };
  }

  const firstLineIsPrompt = /^(в одном|укажите|выберите|выпишите|найдите|определите|запишите|самостоятельно)/i.test(lines[0]);
  const prompt = firstLineIsPrompt ? lines[0] : lines[lines.length - 1];
  const context = firstLineIsPrompt ? lines.slice(1) : lines.slice(0, -1);
  const hasNumberedOptions = context.some((line) => /^\d+[\).]/.test(line));

  return {
    prompt,
    context,
    contextLabel: hasNumberedOptions ? "Варианты ответа" : "Текст задания",
  };
}
