"use client";

import { useEffect, useState } from "react";
import { API_URL } from "@/lib/api";

type SmartCtaLinkProps = {
  className?: string;
  authedHref: string;
  guestHref: string;
  authedLabel: string;
  guestLabel: string;
};

export function SmartCtaLink({ className, authedHref, guestHref, authedLabel, guestLabel }: SmartCtaLinkProps) {
  const [isAuthed, setIsAuthed] = useState(false);

  useEffect(() => {
    let alive = true;

    fetch(`${API_URL}/auth/me`, { credentials: "include" })
      .then((response) => {
        if (alive) setIsAuthed(response.ok);
      })
      .catch(() => {
        if (alive) setIsAuthed(false);
      });

    return () => {
      alive = false;
    };
  }, []);

  return (
    <a className={className} href={isAuthed ? authedHref : guestHref}>
      {isAuthed ? authedLabel : guestLabel}
    </a>
  );
}
