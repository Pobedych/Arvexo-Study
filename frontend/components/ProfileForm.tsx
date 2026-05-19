"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { API_URL } from "@/lib/api";

type User = {
  email: string;
  name: string;
  telegram_id: string | null;
};

export function ProfileForm() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/auth/me`, { credentials: "include" })
      .then((response) => (response.ok ? response.json() : null))
      .then((payload: User | null) => setUser(payload))
      .catch(() => setUser(null));
  }, []);

  async function logout() {
    await fetch(`${API_URL}/auth/logout`, { method: "POST", credentials: "include" });
    router.push("/login");
    router.refresh();
  }

  return (
    <section className="white-panel profile-form">
      <label>
        <span>Имя</span>
        <input value={user?.name ?? ""} placeholder="Войдите в аккаунт" readOnly />
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
      <button className="secondary-button profile-logout" type="button" onClick={logout}>
        Выйти
      </button>
    </section>
  );
}
