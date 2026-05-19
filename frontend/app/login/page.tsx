import { AuthForm } from "@/components/AuthForm";

export default function LoginPage() {
  return (
    <main className="auth-page">
      <section className="auth-card">
        <div className="auth-copy">
          <a className="site-logo" href="/" aria-label="Arvexo Study">
            <img src="/images/arvexo-mark-light-bg.png" alt="" className="site-logo-mark" />
            <span className="logo-text">Arvexo Study</span>
          </a>
          <p className="eyebrow">Вход</p>
          <h1>Вернись к подготовке</h1>
          <p>Войди в аккаунт, чтобы продолжить задания и сохранить новую статистику.</p>
        </div>
        <AuthForm mode="login" />
      </section>
    </main>
  );
}
