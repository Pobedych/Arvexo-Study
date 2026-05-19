"use client";

import { useEffect, useState } from "react";
import { API_URL } from "@/lib/api";

type User = {
  name: string;
};

export function UserGreeting() {
  const [name, setName] = useState("ученик");

  useEffect(() => {
    fetch(`${API_URL}/auth/me`, { credentials: "include" })
      .then((response) => (response.ok ? response.json() : null))
      .then((user: User | null) => {
        if (user?.name) setName(user.name);
      })
      .catch(() => undefined);
  }, []);

  return <h1>Привет, {name}</h1>;
}
