import { AuthForm } from "@/components/AuthForm";

export default function RegisterPage() {
  return (
    <main className="auth-page">
      <section className="auth-card">
        <div className="auth-copy">
          <a className="site-logo" href="/" aria-label="Arvexo Study">
            <img src="/images/arvexo-mark-light-bg.png" alt="" className="site-logo-mark" />
            <span className="logo-text">Arvexo Study</span>
          </a>
          <p className="eyebrow">Старт подготовки</p>
          <h1>Создай аккаунт и начни решать задания</h1>
          <p>
            После регистрации откроется личный кабинет, статистика и дневной лимит AI-подсказок.
          </p>
        </div>
        <AuthForm mode="register" />
      </section>
    </main>
  );
}
