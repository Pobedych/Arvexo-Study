import { ArrowUpRight, BarChart3, BrainCircuit, CheckCircle2, ListChecks } from "lucide-react";
import { HomeHero } from "@/components/HomeHero";
import { SmartCtaLink } from "@/components/SmartCtaLink";

const features = [
  {
    icon: BrainCircuit,
    title: "AI-подсказки",
    text: "Подсказка объясняет правило и ход решения, но не раскрывает готовый ответ.",
  },
  {
    icon: ListChecks,
    title: "Задания 1-18",
    text: "Тренировка по номерам ЕГЭ, темам и уровню сложности.",
  },
  {
    icon: BarChart3,
    title: "Статистика",
    text: "Видно точность, слабые номера и последние попытки.",
  },
];

const examNumbers = Array.from({ length: 18 }, (_, index) => index + 1);

const footerGroups = [
  {
    title: "Directions",
    links: [
      { label: "Arvexo Study", href: "/" },
      { label: "ЕГЭ по русскому", href: "#tasks" },
      { label: "AI-подсказки", href: "#features" },
    ],
  },
  {
    title: "Products",
    links: [
      { label: "Задания 1-18", href: "/tasks" },
      { label: "Личный кабинет", href: "/dashboard" },
      { label: "Telegram-бот", href: "/telegram" },
      { label: "Pro-подписка", href: "#pricing" },
    ],
  },
  {
    title: "Company",
    links: [
      { label: "Arvexo", href: "https://arvexo.ru/" },
      { label: "Roadmap", href: "https://arvexo.ru/#roadmap" },
      { label: "Contacts", href: "https://arvexo.ru/contacts" },
      { label: "Privacy Policy", href: "https://arvexo.ru/privacy-policy" },
      { label: "Terms", href: "https://arvexo.ru/terms" },
    ],
  },
  {
    title: "Socials",
    links: [
      { label: "Telegram", href: "https://t.me/arvexoai" },
      { label: "Email", href: "https://arvexo.ru/contacts" },
      { label: "GitHub", href: "https://arvexo.ru/contacts" },
    ],
  },
];

export default function Home() {
  return (
    <main className="marketing-page">
      <header className="site-header">
        <div className="header-bar">
          <a className="site-logo" href="/" aria-label="Arvexo Study">
            <img src="/images/arvexo-mark-light-bg.png" alt="" className="site-logo-mark" />
            <span className="logo-text">Arvexo Study</span>
          </a>
          <nav className="desktop-nav">
            <a href="#tasks">Задания</a>
            <a href="#features">Возможности</a>
            <a href="/dashboard">Кабинет</a>
          </nav>
          <SmartCtaLink
            className="primary-button header-cta"
            authedHref="/tasks"
            guestHref="/register"
            authedLabel="Задания"
            guestLabel="Начать"
          />
        </div>
      </header>

      <HomeHero />

      <section id="features" className="page-section">
        <div className="section-heading">
          <p className="eyebrow">Возможности</p>
          <h2>Всё основное для регулярной подготовки</h2>
        </div>
        <div className="feature-grid">
          {features.map((feature) => (
            <article className="feature-card" key={feature.title}>
              <feature.icon size={22} />
              <h3>{feature.title}</h3>
              <p>{feature.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section id="tasks" className="page-section task-preview-section">
        <div className="section-heading">
          <p className="eyebrow">Задания</p>
          <h2>Номера 1-18 в одном рабочем пространстве</h2>
        </div>
        <div className="task-number-grid">
          {examNumbers.map((number) => (
            <a href={`/tasks/${number}`} key={number}>
              <span>N{number}</span>
              <small>{number === 5 ? "Паронимы" : number === 9 ? "Корни" : "Тренировка"}</small>
            </a>
          ))}
        </div>
      </section>

      <section id="pricing" className="page-section pricing-section">
        <article className="plan">
          <h3>Free</h3>
          <p className="price">0 ₽</p>
          <ul>
            <li><CheckCircle2 size={18} /> Задания 1-18</li>
            <li><CheckCircle2 size={18} /> Базовая статистика</li>
            <li><CheckCircle2 size={18} /> 5 AI-запросов в день</li>
          </ul>
        </article>
        <article className="plan highlighted">
          <h3>Pro</h3>
          <p className="price">399 ₽/мес</p>
          <ul>
            <li><CheckCircle2 size={18} /> 150 AI-запросов в день</li>
            <li><CheckCircle2 size={18} /> Расширенная статистика</li>
            <li><CheckCircle2 size={18} /> Без рекламы</li>
          </ul>
        </article>
      </section>

      <footer className="site-footer">
        <div className="footer-brand">
          <a className="site-logo footer-logo" href="/" aria-label="Arvexo Study">
            <img src="/images/arvexo-mark-light-bg.png" alt="" className="site-logo-mark" />
            <span className="logo-text">Arvexo Study</span>
          </a>
          <p>Arvexo Study — подготовка к ЕГЭ по русскому с заданиями, статистикой и AI-подсказками.</p>
          <div className="footer-contact">
            <span>Questions, partnerships or product access?</span>
            <a href="https://arvexo.ru/contacts" target="_blank" rel="noreferrer">
              Contact Arvexo <ArrowUpRight size={16} />
            </a>
          </div>
        </div>

        <div className="footer-grid">
          {footerGroups.map((group) => (
            <nav className="footer-column" key={group.title} aria-label={group.title}>
              <h3>{group.title}</h3>
              {group.links.map((link) => (
                <a key={link.label} href={link.href}>
                  {link.label}
                </a>
              ))}
            </nav>
          ))}
        </div>

        <div className="footer-bottom">
          <span>© 2026 Arvexo. All rights reserved.</span>
          <span>study.arvexo.ru</span>
        </div>
      </footer>
    </main>
  );
}
