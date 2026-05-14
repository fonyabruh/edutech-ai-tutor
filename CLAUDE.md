# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Code style

- Use uv for all Python environment management: `uv run python`, `uv pip install`, `uv init`
- Before writing new code, check if existing functions already cover it. Extract repeated logic (3+ uses) into functions
- No comments except for non-obvious logic. No docstrings on short functions. No type hints unless asked
- Write terse, flat code. Prefer short but readable names (emb, tok, cfg — not single letters). No defensive try-excepts unless genuinely needed (API calls, file I/O). No unnecessary validation/checks. Prefer flat scripts over class hierarchies
- Minimal prints: always start with \n (`print("\n...")`), simple wording, no f-string float formatting like {:.3f} — print floats raw. Only use basic ASCII symbols, never ±, ≥, →, ✓ or similar
- Don't add infrastructure I didn't ask for (argparse, logging, config files, CLI wrappers)
- Don't refactor existing code unless explicitly asked

## What this is

EduTech — AI-ассистент подготовки к ОГЭ/ЕГЭ. Хакатонный проект: монорепо с FastAPI-бэкендом и Expo (React Native) мобильным приложением. Главный поток ценности: онбординг → диагностика пробелов → персональный план → урок с разбором ошибок от LLM.

`TASKS.md` — подробная спека по этапам. `problems.md` — code review с известными проблемами. `prompts/*.md` — промпты, которыми проект собирался.

## Commands

**Backend** (из `backend/`):
```bash
uv run uvicorn app.main:app --reload          # запуск API на :8000
uv run ruff check .                            # линт (E, F, I, UP)
uv run python -m scripts.seed_content          # засеять предметы/темы/задачи из ../content/*.json
uv run python -m scripts.seed_demo_user        # запасной демо-аккаунт device_id=demo-jury-001
uv run python -m scripts.smoke_llm             # ручной smoke-чек рендера промптов
```

**Mobile** (из `mobile/`):
```bash
npx expo start                                 # дев-сервер
npx tsc --noEmit                               # проверка типов (основная верификация — тестов нет)
npm run lint                                   # expo lint
```

**Деплой** (из `infra/`): `docker compose up -d` (backend + Caddy с авто-HTTPS).

Автотестов в репозитории нет — верификация строится на `ruff check`, `tsc --noEmit`, `import app.main` и прогоне сидов.

## Backend architecture

FastAPI + SQLModel + SQLite. Слои: `api/` (роутеры) → `services/` (бизнес-логика) → `models/` (SQLModel-таблицы). БД создаётся через `SQLModel.metadata.create_all` в lifespan, миграций нет.

**Ключевая абстракция — mastery.** Для каждой пары (user, topic) хранится Beta-распределение (`alpha`, `beta`), `mastery = alpha / (alpha + beta)`. `services/mastery.py` обновляет его после каждой попытки. Mastery — единый источник правды, на нём строятся: результаты диагностики, приоритизация тем в плане, подбор сложности задач в уроке.

**LLM-слой (`app/llm/`)** спроектирован под смену провайдера (YandexGPT → Qwen). `client.py` — тонкий адаптер `LLMClient` с `chat()` и `stream()`. Промпты — YAML-файлы в `app/llm/prompts/` (diagnose, plan, explain_error, tutor_chat), рендерятся через `load_prompt(name, **vars)` (Jinja2). При добавлении LLM-фичи: новый YAML + вызов `load_prompt`, не хардкодить промпты в коде. Примечание: в корневом `prompts/` лежат устаревшие копии YAML — канонические в `backend/app/llm/prompts/`.

**Поток данных диагностики:** `POST /diagnostic/start` подбирает задачи по темам предмета → `/answer` копит `Attempt` → `/finish` вызывает `services/diagnostic.py:finalize_diagnostic`, который обновляет mastery, дёргает LLM-промпт `diagnose` и сохраняет `DiagnosticResult`. Аналогично `services/plan.py` строит `LearningPlan` через промпт `plan`.

**Auth** — анонимный: `POST /auth/anonymous` принимает `device_id`, создаёт/находит `User`, выдаёт JWT (HS256, 30 дней). `api/deps.py:get_current_user` — зависимость для защищённых роутов.

**SSE-стриминг** используется для двух фич: разбор ошибки (`POST /lesson/explain`) и чат-тьютор (`POST /chat/message`). Стрим формируется через `sse-starlette`, чанки идут как `event: chunk` / `event: done`.

JSON-поля в моделях (`subjects`, `weak_topics`, `days` и т.п.) хранятся как сериализованные строки — на чтении делать `json.loads`.

## Mobile architecture

Expo (new architecture) + expo-router (file-based, `app/`). TypeScript strict, NativeWind v4 для стилей.

- **API-слой:** `lib/api.ts` — axios-инстанс с JWT-интерсептором; `hooks/api/*` — обёртки TanStack Query вокруг эндпоинтов (один файл на домен: useDiagnostic, usePlan, useLesson, useChat, useMe). Новые запросы добавлять туда, не дёргать axios напрямую из экранов.
- **SSE на клиенте:** `lib/sse.ts` (`streamSSE`) + `hooks/useLLMStream.ts` — стрим LLM-ответов через fetch + ReadableStream.
- **Состояние:** Zustand для эфемерного UI-стейта (`store/onboardingStore`, `store/chatStore`); серверный стейт — через TanStack Query; токен и device_id — в MMKV (`lib/storage.ts`).
- **Навигация и гейтинг:** `app/_layout.tsx` через `useAuth` решает, куда вести: онбординг / табы. Группы маршрутов: `(onboarding)/`, `(tabs)/`, плюс стеки `diagnostic/`, `lesson/`, `plan/`, `chat/`.
- **UI-кит:** `components/ui/` (Button, Card, Chip, ProgressBar, MarkdownView, Heatmap и др.) — переиспользовать, не плодить дубли. `components/task/` — рендереры типов задач (multi_choice / short_answer / numeric).
- `MarkdownView` рендерит markdown с LaTeX (`$...$`, `$$...$$`) — используется во всех местах с контентом задач и LLM-ответами.

## Content

`content/*.json` — сиды: `subjects.json`, `topics_{math,rus,soc}.json`, `tasks_{math,rus,soc}.json`. Темы привязаны к кодификатору ФИПИ через `codifier_code`. После правок контента — пересеять (`seed_content.py` чистит таблицу Task перед загрузкой).
