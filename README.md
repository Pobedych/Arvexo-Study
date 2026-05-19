# Arvexo Study

MVP scaffold for `study.arvexo.ru`: a web application and Telegram bot for Russian Unified State Exam preparation.

## Stack

- Frontend: Next.js, React, TypeScript
- Backend: FastAPI, SQLAlchemy, PostgreSQL-ready
- Cache/rate limits: Redis-ready
- Bot: aiogram scaffold
- Infra: Docker Compose, Nginx example

## Local Run

1. Copy `.env.example` to `.env`.
2. Start services:

```powershell
docker compose up --build
```

3. Open:

- Frontend: `http://localhost:3001`
- Backend API: `http://localhost:8001/docs`

## MVP Notes

This repository starts with the first technical slice:

- domain models for users, tasks, attempts, AI usage, subscriptions and payments;
- answer normalization and validation rules;
- task list/detail/submit APIs;
- AI hint endpoint with daily plan limits;
- landing/dashboard UI skeleton;
- Docker Compose for frontend, backend, PostgreSQL, Redis and bot.

Legal review for FIPI materials, payment provider, AI provider and email provider must be completed before production launch.
