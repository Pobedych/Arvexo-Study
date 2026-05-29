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

const studentBenefits = [
  "Находит слабые темы по реальным попыткам",
  "Даёт подсказку к правилу, а не готовый ответ",
  "Помогает регулярно возвращаться к сложным номерам",
];

const teacherBenefits = [
  "Видимость прогресса учеников и класса",
  "Задания и повторение по темам",
  "Меньше ручной проверки типовых ошибок",
];

const subjects = ["Русский язык", "Математика", "Информатика", "Английский", "Обществознание", "ОГЭ-направления"];

const faqItems = [
  ["Это уже готовая платформа?", "Нет. Arvexo Study находится в MVP-разработке, часть функций доступна как ранний продукт."],
  ["AI будет решать за ученика?", "Нет. Подсказки должны объяснять правило, направление проверки и типовую ошибку без раскрытия готового ответа."],
  ["Какие предметы будут первыми?", "Сейчас фокус на ЕГЭ по русскому. Остальные предметы показаны как планируемые направления."],
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
      { label: "Ранний доступ", href: "#pricing" },
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
            <a href="#features">Возможности</a>
            <a href="#subjects">Предметы</a>
            <a href="#students">Для учеников</a>
            <a href="#teachers">Для преподавателей</a>
            <a href="https://account.arvexo.ru">Войти</a>
          </nav>
          <SmartCtaLink
            className="primary-button header-cta"
            authedHref="/tasks"
            guestHref="https://account.arvexo.ru"
            authedLabel="Задания"
            guestLabel="Ранний доступ"
          />
        </div>
      </header>

      <HomeHero />

      <section id="features" className="page-section">
        <div className="section-heading">
          <p className="eyebrow">Возможности</p>
          <h2>Практические сценарии для регулярной подготовки</h2>
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

      <section id="students" className="page-section split-section">
        <div className="section-heading align-left">
          <p className="eyebrow">Для учеников</p>
          <h2>Персональная траектория без громких обещаний про баллы</h2>
          <p>Study помогает видеть слабые темы, возвращаться к ошибкам и тренироваться регулярнее.</p>
        </div>
        <div className="feature-grid compact-grid">
          {studentBenefits.map((item) => (
            <article className="feature-card" key={item}><h3>{item}</h3></article>
          ))}
        </div>
      </section>

      <section id="teachers" className="page-section split-section">
        <div className="section-heading align-left">
          <p className="eyebrow">Для преподавателей</p>
          <h2>Классы, задания и статистика как следующий слой продукта</h2>
          <p>Учительский сценарий строится вокруг экономии времени на повторении и понятного прогресса по темам.</p>
        </div>
        <div className="feature-grid compact-grid">
          {teacherBenefits.map((item) => (
            <article className="feature-card" key={item}><h3>{item}</h3></article>
          ))}
        </div>
      </section>

      <section id="subjects" className="page-section subjects-section">
        <div className="section-heading">
          <p className="eyebrow">Предметы</p>
          <h2>Фокус на ЕГЭ по русскому, расширение поэтапно</h2>
        </div>
        <div className="task-number-grid subject-grid">
          {subjects.map((subject, index) => (
            <span key={subject}>
              <strong>{subject}</strong>
              <small>{index === 0 ? "MVP" : "Планируется"}</small>
            </span>
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

      <section id="pricing" className="page-section pricing-section early-access-section">
        <article className="plan">
          <h3>Ранний доступ</h3>
          <p className="price">MVP</p>
          <ul>
            <li><CheckCircle2 size={18} /> Задания 1-18</li>
            <li><CheckCircle2 size={18} /> Базовая статистика</li>
            <li><CheckCircle2 size={18} /> Ограниченные AI-подсказки</li>
          </ul>
        </article>
        <article className="plan highlighted">
          <h3>Account и подписки</h3>
          <p className="price">в планах</p>
          <ul>
            <li><CheckCircle2 size={18} /> Единый вход Arvexo Account</li>
            <li><CheckCircle2 size={18} /> Подписки и доступы без фейковых платежей</li>
            <li><CheckCircle2 size={18} /> Связка с Telegram-профилем</li>
          </ul>
        </article>
      </section>

      <section className="page-section faq-section">
        <div className="section-heading">
          <p className="eyebrow">FAQ</p>
          <h2>Честно о статусе продукта</h2>
        </div>
        <div className="faq-list">
          {faqItems.map(([question, answer]) => (
            <details key={question}>
              <summary>{question}</summary>
              <p>{answer}</p>
            </details>
          ))}
        </div>
      </section>

      <footer className="site-footer">
        <div className="footer-brand">
          <a className="site-logo footer-logo" href="/" aria-label="Arvexo Study">
            <img src="/images/arvexo-mark-light-bg.png" alt="" className="site-logo-mark" />
            <span className="logo-text">Arvexo Study</span>
          </a>
          <p>Arvexo Study — AI-тренажёр для ЕГЭ и ОГЭ с заданиями, статистикой, подсказками и ранним доступом.</p>
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
