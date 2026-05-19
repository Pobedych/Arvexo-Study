"use client";

import { useEffect, useMemo, useState } from "react";
import { ArrowRight, Dice5, RotateCcw, Search } from "lucide-react";
import { API_URL } from "@/lib/api";

type TaskListItem = {
  id: string;
  exam_number: number;
  topic: string;
  difficulty: string;
  status: string;
  user_status: "unsolved" | "correct" | "wrong";
  attempts_count: number;
};

type RecentAttempt = {
  task_id: string;
  exam_number: number;
  topic: string;
  is_correct: boolean;
  created_at: string;
};

type AccountStats = {
  weak_exam_numbers: number[];
  recent_attempts: RecentAttempt[];
};

const examNumbers = Array.from({ length: 18 }, (_, index) => index + 1);
type StatusFilter = "all" | "unsolved" | "wrong" | "hard";
type NumberSummary = {
  number: number;
  topic: string;
  total: number;
  solved: number;
  correct: number;
  wrong: number;
  accuracy: number;
};

const INITIAL_VISIBLE_TASKS = 24;

export function TasksBrowser() {
  const [tasks, setTasks] = useState<TaskListItem[]>([]);
  const [stats, setStats] = useState<AccountStats | null>(null);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [selectedNumber, setSelectedNumber] = useState<number | "all">("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [visibleCount, setVisibleCount] = useState(INITIAL_VISIBLE_TASKS);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let alive = true;

    async function loadTasks() {
      setLoading(true);
      setError("");
      try {
        const response = await fetch(`${API_URL}/tasks`, { credentials: "include" });
        if (!response.ok) throw new Error("Не удалось загрузить задания.");
        const payload = (await response.json()) as TaskListItem[];
        if (alive) setTasks(payload);

        const statsResponse = await fetch(`${API_URL}/stats/me?plan=free`, { credentials: "include" });
        if (statsResponse.ok && alive) {
          setStats((await statsResponse.json()) as AccountStats);
        }
      } catch (loadError) {
        if (alive) setError(loadError instanceof Error ? loadError.message : "Не удалось загрузить задания.");
      } finally {
        if (alive) setLoading(false);
      }
    }

    loadTasks();
    return () => {
      alive = false;
    };
  }, []);

  useEffect(() => {
    setVisibleCount(INITIAL_VISIBLE_TASKS);
  }, [selectedNumber, statusFilter, searchQuery]);

  const filteredTasks = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    return tasks.filter((task) => {
      const matchesNumber = selectedNumber === "all" || task.exam_number === selectedNumber;
      const matchesStatus =
        statusFilter === "all" ||
        (statusFilter === "unsolved" && task.user_status === "unsolved") ||
        (statusFilter === "wrong" && task.user_status === "wrong") ||
        (statusFilter === "hard" && task.difficulty === "hard");
      const matchesSearch =
        !query ||
        task.topic.toLowerCase().includes(query) ||
        difficultyLabel(task.difficulty).toLowerCase().includes(query) ||
        `n${task.exam_number}`.includes(query) ||
        `н${task.exam_number}`.includes(query);
      return matchesNumber && matchesStatus && matchesSearch;
    });
  }, [searchQuery, selectedNumber, statusFilter, tasks]);

  const shownTasks = useMemo(() => filteredTasks.slice(0, visibleCount), [filteredTasks, visibleCount]);

  const summaries = useMemo(() => {
    return examNumbers.map((number) => {
      const numberTasks = tasks.filter((task) => task.exam_number === number);
      const solved = numberTasks.filter((task) => task.user_status !== "unsolved").length;
      const correct = numberTasks.filter((task) => task.user_status === "correct").length;
      const wrong = numberTasks.filter((task) => task.user_status === "wrong").length;
      const topic = numberTasks.find(Boolean)?.topic ?? "Тренировка";
      return {
        number,
        topic,
        total: numberTasks.length,
        solved,
        correct,
        wrong,
        accuracy: solved > 0 ? Math.round((correct / solved) * 100) : 0,
      };
    });
  }, [tasks]);

  const selectedSummary = selectedNumber === "all" ? null : summaries.find((summary) => summary.number === selectedNumber);
  const lastAttempt = stats?.recent_attempts[0] ?? null;
  const continueHref = lastAttempt ? `/tasks/${lastAttempt.task_id}` : "/tasks/5";
  const randomTask = filteredTasks.length > 0 ? filteredTasks[Math.floor(Math.random() * filteredTasks.length)] : tasks[0];
  const randomHref = randomTask ? `/tasks/${randomTask.id}` : "/tasks/5";
  const shownCount = Math.min(visibleCount, filteredTasks.length);
  const catalogSummary = loading
    ? "Загружаем задания..."
    : selectedSummary
      ? `N${selectedSummary.number}: ${selectedSummary.solved} из ${selectedSummary.total} решено. Показано ${shownCount} из ${filteredTasks.length}`
      : `Показано ${shownCount} из ${filteredTasks.length}. Всего в банке: ${tasks.length}`;

  function selectStatus(nextStatus: StatusFilter) {
    setStatusFilter(nextStatus);
  }

  function selectNumber(nextNumber: number | "all") {
    setSelectedNumber(nextNumber);
  }

  function repeatErrors() {
    setSelectedNumber("all");
    setStatusFilter("wrong");
  }

  function showUnsolved() {
    setSelectedNumber("all");
    setStatusFilter("unsolved");
  }

  return (
    <section className="white-panel">
      <div className="panel-title">
        <div>
          <h2>Банк заданий</h2>
          <p className="panel-copy">{catalogSummary}</p>
        </div>
        <a href={continueHref}>Продолжить</a>
      </div>

      <div className="task-actions-grid" aria-label="Быстрые действия">
        <a className="task-action-card primary" href={continueHref}>
          <span>Продолжить</span>
          <strong>{lastAttempt ? `N${lastAttempt.exam_number}: ${lastAttempt.topic}` : "N5: Паронимы"}</strong>
          <small>последнее открытое задание</small>
          <ArrowRight size={18} />
        </a>
        <button className="task-action-card" type="button" onClick={repeatErrors}>
          <span>Повторить ошибки</span>
          <strong>{tasks.filter((task) => task.user_status === "wrong").length}</strong>
          <small>задания с последней ошибкой</small>
          <RotateCcw size={18} />
        </button>
        <a className="task-action-card" href={randomHref}>
          <span>Случайное</span>
          <strong>Старт</strong>
          <small>быстрое задание из текущего фильтра</small>
          <Dice5 size={18} />
        </a>
        <button className="task-action-card" type="button" onClick={showUnsolved}>
          <span>Нерешённые</span>
          <strong>{tasks.filter((task) => task.user_status === "unsolved").length}</strong>
          <small>очередь для тренировки</small>
          <ArrowRight size={18} />
        </button>
      </div>

      <div className="task-overview-grid" aria-label="Прогресс по номерам ЕГЭ">
        {summaries.map((summary) => (
          <button
            className={`task-overview-card ${selectedNumber === summary.number ? "active" : ""}`}
            type="button"
            key={summary.number}
            onClick={() => selectNumber(summary.number)}
          >
            <span>N{summary.number}</span>
            <strong>{summary.topic}</strong>
            <small>
              {summary.solved} / {summary.total} решено
            </small>
            <div className="mini-progress" aria-hidden="true">
              <span style={{ width: `${summary.total > 0 ? Math.max(4, (summary.solved / summary.total) * 100) : 0}%` }} />
            </div>
            <em>{summary.wrong > 0 ? `${summary.wrong} ошибок` : summary.solved > 0 ? `${summary.accuracy}% верно` : "не начато"}</em>
          </button>
        ))}
      </div>

      <div className="task-catalog-toolbar">
        <div className="task-search">
          <Search size={18} />
          <input
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            placeholder="Поиск по теме, номеру или сложности"
          />
        </div>
        <button className="secondary-button" type="button" onClick={() => selectNumber("all")}>
          Все номера
        </button>
      </div>

      <div className="filter-row" aria-label="Фильтр по статусу">
        <button className={`chip ${statusFilter === "all" ? "active" : ""}`} type="button" onClick={() => selectStatus("all")}>
          Все
        </button>
        <button
          className={`chip ${statusFilter === "unsolved" ? "active" : ""}`}
          type="button"
          onClick={() => selectStatus("unsolved")}
        >
          Нерешённые
        </button>
        <button
          className={`chip ${statusFilter === "wrong" ? "active" : ""}`}
          type="button"
          onClick={() => selectStatus("wrong")}
        >
          С ошибкой
        </button>
        <button className={`chip ${statusFilter === "hard" ? "active" : ""}`} type="button" onClick={() => selectStatus("hard")}>
          Сложные
        </button>
      </div>

      {error && <p className="task-message error">{error}</p>}

      <div className="task-list">
        {loading ? (
          <article className="task-row">
            <span className="task-number">...</span>
            <div>
              <h3>Загружаем задания</h3>
              <p>Секунду, получаем банк из API.</p>
            </div>
            <span className="status">Загрузка</span>
          </article>
        ) : shownTasks.length > 0 ? (
          shownTasks.map((task) => (
            <a className="task-row" href={`/tasks/${task.id}`} key={task.id}>
              <span className="task-number">N{task.exam_number}</span>
              <div>
                <h3>{task.topic}</h3>
                <p>{difficultyLabel(task.difficulty)}</p>
              </div>
              <span className={`status ${task.user_status === "correct" ? "success" : task.user_status === "wrong" ? "wrong" : ""}`}>
                {taskStatusLabel(task)}
              </span>
            </a>
          ))
        ) : (
          <article className="task-row">
            <span className="task-number">0</span>
            <div>
              <h3>Ничего не найдено</h3>
              <p>Поменяй статус или номер задания.</p>
            </div>
            <span className="status">Пусто</span>
          </article>
        )}
      </div>

      {!loading && filteredTasks.length > shownTasks.length && (
        <button className="load-more-button" type="button" onClick={() => setVisibleCount((count) => count + INITIAL_VISIBLE_TASKS)}>
          Показать ещё {Math.min(INITIAL_VISIBLE_TASKS, filteredTasks.length - shownTasks.length)}
        </button>
      )}
    </section>
  );
}

function difficultyLabel(difficulty: string): string {
  if (difficulty === "hard") return "Сложная";
  if (difficulty === "easy") return "Лёгкая";
  return "Средняя";
}

function taskStatusLabel(task: TaskListItem): string {
  if (task.user_status === "correct") return "Верно";
  if (task.user_status === "wrong") return "Ошибка";
  return "Не решено";
}
