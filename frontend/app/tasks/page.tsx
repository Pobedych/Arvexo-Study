import { AppSidebar } from "@/components/AppSidebar";
import { TasksBrowser } from "@/components/TasksBrowser";

export default function TasksPage() {
  return (
    <main className="app-shell">
      <AppSidebar active="tasks" />
      <section className="dashboard">
        <div className="dashboard-header">
          <div>
            <p className="eyebrow">Задания</p>
            <h1>Тренировка 1-18</h1>
          </div>
          <a className="primary-button" href="/tasks/5">Открыть N5</a>
        </div>

        <TasksBrowser />
      </section>
    </main>
  );
}
