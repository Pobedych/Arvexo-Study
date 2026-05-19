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

## CI/CD

GitHub Actions workflow: `.github/workflows/ci-cd.yml`.

On pull requests and pushes it runs:

- backend tests;
- frontend production build;
- Docker image builds for frontend, backend and bot.

On push to `main` it also deploys to the VPS over SSH.

Required GitHub repository secrets:

- `VPS_HOST` — server IP or hostname;
- `VPS_USER` — SSH user;
- `VPS_SSH_KEY` — private SSH key with access to the server;
- `VPS_PORT` — SSH port, usually `22`;
- `DEPLOY_PATH` — path to the cloned repository on the server.

The server directory must already contain a cloned repo and a production `.env` file. Deploy command used by CI:

```bash
docker compose -f docker-compose.prod.yml --env-file .env up -d --build --remove-orphans
```

Production Nginx should proxy:

- `study.arvexo.ru` -> `127.0.0.1:3101`
- `api.study.arvexo.ru` -> `127.0.0.1:8101`
