import { TaskSolver } from "@/components/TaskSolver";

export default function TaskPage() {
  return (
    <main className="task-page">
      <header className="task-header">
        <a className="site-logo" href="/" aria-label="Arvexo Study">
          <img src="/images/arvexo-mark-light-bg.png" alt="" className="site-logo-mark" />
          <span className="logo-text">Arvexo Study</span>
        </a>
        <a className="secondary-button" href="/dashboard">Кабинет</a>
      </header>

      <TaskSolver />
    </main>
  );
}
