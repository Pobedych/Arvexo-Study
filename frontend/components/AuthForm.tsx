"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { API_URL } from "@/lib/api";
import { TelegramLoginButton } from "@/components/TelegramLoginButton";

type Mode = "register" | "login";

type ApiError = {
  detail?: string;
};

export function AuthForm({ mode }: { mode: Mode }) {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordRepeat, setPasswordRepeat] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const isRegister = mode === "register";

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const oauthError = params.get("oauth_error");
    if (oauthError) setError(readableOAuthError(oauthError));
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    if (isRegister && password !== passwordRepeat) {
      setError("Пароли не совпадают.");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/auth/${isRegister ? "register" : "login"}`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(isRegister ? { name, email, password } : { email, password }),
      });

      if (!response.ok) {
        const payload = (await response.json().catch(() => ({}))) as ApiError;
        throw new Error(readableError(payload.detail, response.status));
      }

      router.push("/dashboard");
      router.refresh();
    } catch (authError) {
      setError(authError instanceof Error ? authError.message : "Не удалось выполнить запрос.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="auth-form" onSubmit={submit}>
      <div className="auth-tabs">
        <a className={isRegister ? "active" : ""} href="/register">Регистрация</a>
        <a className={!isRegister ? "active" : ""} href="/login">Вход</a>
      </div>

      {isRegister && (
        <label>
          <span>Имя</span>
          <input value={name} onChange={(event) => setName(event.target.value)} minLength={2} required />
        </label>
      )}

      <label>
        <span>Email</span>
        <input
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          type="email"
          autoComplete="email"
          required
        />
      </label>

      <label>
        <span>Пароль</span>
        <input
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          type="password"
          autoComplete={isRegister ? "new-password" : "current-password"}
          minLength={isRegister ? 8 : 1}
          required
        />
      </label>

      {isRegister && (
        <label>
          <span>Повтор пароля</span>
          <input
            value={passwordRepeat}
            onChange={(event) => setPasswordRepeat(event.target.value)}
            type="password"
            autoComplete="new-password"
            minLength={8}
            required
          />
        </label>
      )}

      {error && <p className="auth-message">{error}</p>}

      <button className="primary-button auth-submit" type="submit" disabled={loading}>
        {loading ? "Проверяем..." : isRegister ? "Зарегистрироваться" : "Войти"}
      </button>

      <div className="oauth-grid">
        <a href={`${API_URL}/auth/google`}>Google</a>
        <a href={`${API_URL}/auth/yandex`}>Яндекс</a>
      </div>
      <TelegramLoginButton />
    </form>
  );
}

function readableError(detail: string | undefined, status: number): string {
  if (detail === "Email already registered") return "Такой email уже зарегистрирован.";
  if (detail === "Invalid email or password") return "Неверный email или пароль.";
  if (status === 422) return "Проверь email и пароль. Пароль должен быть не короче 8 символов.";
  return detail ?? "Не удалось выполнить запрос.";
}

function readableOAuthError(error: string): string {
  if (error === "google_not_configured") return "Google OAuth не настроен на сервере.";
  if (error === "yandex_not_configured") return "Яндекс OAuth не настроен на сервере.";
  if (error === "invalid_state") return "OAuth-сессия устарела. Попробуй войти ещё раз.";
  if (error.endsWith("_email")) return "OAuth-провайдер не вернул email аккаунта.";
  if (error.endsWith("_token")) return "Не удалось получить OAuth-токен. Проверь настройки приложения.";
  if (error.endsWith("_denied")) return "Вход через OAuth был отменён.";
  return "Не удалось войти через OAuth.";
}
