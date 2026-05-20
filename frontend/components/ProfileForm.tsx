"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle2, LogOut, Save } from "lucide-react";
import { API_URL } from "@/lib/api";

type User = {
  email: string;
  name: string;
  last_name: string | null;
  phone: string | null;
  role: string;
  telegram_id: string | null;
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
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
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

      {(message || error) && <p className={`profile-message ${error ? "error" : "success"}`}>{error || message}</p>}

      <div className="profile-actions">
        <button className="primary-button" type="submit" disabled={saving || !user}>
          {saving ? "Сохраняем..." : "Сохранить"} <Save size={18} />
        </button>
        <button className="secondary-button profile-logout" type="button" onClick={logout}>
          Выйти <LogOut size={18} />
        </button>
      </div>
    </form>
  );
}
