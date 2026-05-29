import { AppSidebar } from "@/components/AppSidebar";
import { ProfileForm } from "@/components/ProfileForm";

export default function ProfilePage() {
  return (
    <main className="app-shell">
      <AppSidebar active="profile" />
      <section className="dashboard">
        <div className="dashboard-header">
          <div>
            <p className="eyebrow">Профиль</p>
            <h1>Данные ученика</h1>
          </div>
          <a className="secondary-button" href="https://account.arvexo.ru">Войти заново</a>
        </div>

        <ProfileForm />
      </section>
    </main>
  );
}
