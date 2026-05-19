import { AppSidebar } from "@/components/AppSidebar";
import { DashboardStats } from "@/components/DashboardStats";
import { UserGreeting } from "@/components/UserGreeting";

export default function DashboardPage() {
  return (
    <main className="app-shell">
      <AppSidebar active="dashboard" />

      <section className="dashboard">
        <div className="dashboard-header">
          <div>
            <p className="eyebrow">Личный кабинет</p>
            <UserGreeting />
          </div>
          <a className="secondary-button" href="/">На главную</a>
        </div>

        <DashboardStats />
      </section>
    </main>
  );
}
