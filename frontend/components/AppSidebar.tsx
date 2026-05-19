import { BarChart3, Bot, BrainCircuit, ListChecks, UserRound } from "lucide-react";

const navItems = [
  { href: "/dashboard", label: "Кабинет", icon: BarChart3, key: "dashboard" },
  { href: "/tasks", label: "Задания", icon: ListChecks, key: "tasks" },
  { href: "/ai", label: "AI", icon: BrainCircuit, key: "ai" },
  { href: "/telegram", label: "Telegram", icon: Bot, key: "telegram" },
  { href: "/profile", label: "Профиль", icon: UserRound, key: "profile" },
] as const;

type ActiveKey = (typeof navItems)[number]["key"];

export function AppSidebar({ active }: { active: ActiveKey }) {
  return (
    <aside className="sidebar">
      <a className="site-logo site-logo-compact" href="/" aria-label="Arvexo Study">
        <img src="/images/arvexo-mark-light-bg.png" alt="" className="site-logo-mark" />
        <span className="logo-text">Study</span>
      </a>
      <nav className="side-nav" aria-label="Навигация кабинета">
        {navItems.map((item) => (
          <a key={item.key} className={active === item.key ? "active" : ""} href={item.href}>
            <item.icon size={18} />
            {item.label}
          </a>
        ))}
      </nav>
    </aside>
  );
}
