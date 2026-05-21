"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle2, Link2, LogOut, Save, Trash2 } from "lucide-react";
import { API_URL } from "@/lib/api";

type User = {
  email: string;
  name: string;
  last_name: string | null;
  phone: string | null;
  role: string;
  telegram_id: string | null;
  auth_providers: string[];
};

type ProfileState = {
  name: string;
  lastName: string;
  phone: string;
};

const emptyProfile: ProfileState = {
  name: "",
  lastName: "",
  phone: "",
};

export function ProfileForm() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<ProfileState>(emptyProfile);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteConfirmed, setDeleteConfirmed] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const connected = params.get("connected");
    const connectError = params.get("connect_error");
    if (connected) setMessage(`${providerLabel(connected)} подключён к аккаунту.`);
    if (connectError) setError(readableConnectError(connectError));

    let alive = true;

    fetch(`${API_URL}/auth/me`, { credentials: "include" })
      .then((response) => (response.ok ? response.json() : null))
      .then((payload: User | null) => {
        if (!alive) return;
        setUser(payload);
        setProfile({
          name: payload?.name ?? "",
          lastName: payload?.last_name ?? "",
          phone: payload?.phone ?? "",
        });
      })
      .catch(() => {
        if (alive) setError("Не удалось загрузить профиль.");
      })
      .finally(() => {
        if (alive) setLoading(false);
      });

    return () => {
      alive = false;
    };
  }, []);

  async function saveProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setMessage("");
    setError("");

    try {
      const response = await fetch(`${API_URL}/auth/me`, {
        method: "PATCH",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: profile.name,
          last_name: profile.lastName || null,
          phone: profile.phone || null,
        }),
      });

      if (response.status === 401) throw new Error("Войдите в аккаунт, чтобы изменить профиль.");
      if (!response.ok) throw new Error("Не удалось сохранить профиль.");

      const payload = (await response.json()) as User;
      setUser(payload);
      setProfile({
        name: payload.name,
        lastName: payload.last_name ?? "",
        phone: payload.phone ?? "",
      });
      setMessage("Профиль сохранён.");
      router.refresh();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Не удалось сохранить профиль.");
    } finally {
      setSaving(false);
    }
  }

  async function logout() {
    await fetch(`${API_URL}/auth/logout`, { method: "POST", credentials: "include" });
    router.push("/login");
    router.refresh();
  }

  async function deleteAccount() {
    if (!user || !deleteConfirmed || deleting) return;
    setDeleting(true);
    setMessage("");
    setError("");

    try {
      const response = await fetch(`${API_URL}/auth/me`, {
        method: "DELETE",
        credentials: "include",
      });

      if (response.status === 401) throw new Error("Войдите в аккаунт, чтобы удалить профиль.");
      if (!response.ok) throw new Error("Не удалось удалить аккаунт.");

      router.push("/register");
      router.refresh();
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Не удалось удалить аккаунт.");
      setDeleting(false);
    }
  }

  if (loading) {
    return (
      <section className="white-panel">
        <p className="eyebrow">Профиль</p>
        <h2>Загружаем данные</h2>
      </section>
    );
  }

  return (
    <form className="white-panel profile-form" onSubmit={saveProfile}>
      <div className="profile-form-head">
        <div>
          <p className="eyebrow">Личные данные</p>
          <h2>Профиль ученика</h2>
        </div>
        <span className="status success">
          <CheckCircle2 size={15} /> {user ? "Аккаунт активен" : "Нужен вход"}
        </span>
      </div>

      <label>
        <span>Имя</span>
        <input
          value={profile.name}
          onChange={(event) => setProfile((current) => ({ ...current, name: event.target.value }))}
          placeholder="Введите имя"
          minLength={2}
          required
        />
      </label>
      <label>
        <span>Фамилия</span>
        <input
          value={profile.lastName}
          onChange={(event) => setProfile((current) => ({ ...current, lastName: event.target.value }))}
          placeholder="Введите фамилию"
        />
      </label>
      <label>
        <span>Телефон</span>
        <input
          value={profile.phone}
          onChange={(event) => setProfile((current) => ({ ...current, phone: event.target.value }))}
          placeholder="+7 999 000-00-00"
          inputMode="tel"
          autoComplete="tel"
        />
      </label>
      <label>
        <span>Email</span>
        <input value={user?.email ?? ""} placeholder="email не загружен" readOnly />
      </label>
      <label>
        <span>Тариф</span>
        <input defaultValue="Trial, 7 дней" readOnly />
      </label>
      <label>
        <span>Telegram</span>
        <input value={user?.telegram_id ?? "Не подключён"} readOnly />
      </label>

      <section className="connected-auth">
        <div>
          <p className="eyebrow">Способы входа</p>
          <h3>Подключи вход в этот же аккаунт</h3>
        </div>
        <div className="connected-auth-grid">
          <AuthProviderLink provider="email" label="Email" connected={Boolean(user?.auth_providers.includes("email"))} />
          <AuthProviderLink provider="google" label="Google" connected={Boolean(user?.auth_providers.includes("google"))} />
          <AuthProviderLink provider="yandex" label="Яндекс" connected={Boolean(user?.auth_providers.includes("yandex"))} />
          <AuthProviderLink provider="telegram" label="Telegram" connected={Boolean(user?.auth_providers.includes("telegram"))} />
        </div>
      </section>

      {(message || error) && <p className={`profile-message ${error ? "error" : "success"}`}>{error || message}</p>}

      <div className="profile-actions">
        <button className="primary-button" type="submit" disabled={saving || !user}>
          {saving ? "Сохраняем..." : "Сохранить"} <Save size={18} />
        </button>
        <button className="secondary-button profile-logout" type="button" onClick={logout}>
          Выйти <LogOut size={18} />
        </button>
      </div>

      <section className="danger-zone">
        <div>
          <p className="eyebrow">Удаление</p>
          <h3>Удалить аккаунт</h3>
          <p>Будут удалены профиль, способы входа, история решений, AI-логи и подписки в Arvexo Study.</p>
        </div>
        <label className="danger-confirm">
          <input
            type="checkbox"
            checked={deleteConfirmed}
            onChange={(event) => setDeleteConfirmed(event.target.checked)}
            disabled={!user || deleting}
          />
          <span>Я понимаю, что это действие нельзя отменить</span>
        </label>
        <button
          className="danger-button"
          type="button"
          onClick={deleteAccount}
          disabled={!user || !deleteConfirmed || deleting}
        >
          {deleting ? "Удаляем..." : "Удалить аккаунт"} <Trash2 size={18} />
        </button>
      </section>
    </form>
  );
}

function AuthProviderLink({ provider, label, connected }: { provider: string; label: string; connected: boolean }) {
  const href = provider === "google" || provider === "yandex" ? `${API_URL}/auth/${provider}/connect` : undefined;

  if (provider === "email") {
    return (
      <div className={`auth-provider-card ${connected ? "connected" : ""}`}>
        <span>{label}</span>
        <small>{connected ? "Основной вход" : "Не настроен"}</small>
      </div>
    );
  }

  if (provider === "telegram") {
    return (
      <a className={`auth-provider-card ${connected ? "connected" : ""}`} href="/telegram">
        <span>{label}</span>
        <small>{connected ? "Подключён" : "Подключить"}</small>
        <Link2 size={16} />
      </a>
    );
  }

  return (
    <a className={`auth-provider-card ${connected ? "connected" : ""}`} href={href}>
      <span>{label}</span>
      <small>{connected ? "Подключён" : "Подключить"}</small>
      <Link2 size={16} />
    </a>
  );
}

function providerLabel(provider: string): string {
  if (provider === "google") return "Google";
  if (provider === "yandex") return "Яндекс";
  if (provider === "telegram") return "Telegram";
  return "Провайдер";
}

function readableConnectError(error: string): string {
  if (error === "google_already_linked") return "Этот Google-аккаунт уже подключён к другому профилю.";
  if (error === "yandex_already_linked") return "Этот Яндекс-аккаунт уже подключён к другому профилю.";
  return "Не удалось подключить способ входа.";
}
