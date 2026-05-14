# Промпт: Этапы 0 и 1 — скаффолд проекта и контент

Скопируй блок ниже в Claude Code (Sonnet). После выполнения проверь acceptance criteria в конце.

---

```
Ты — senior разработчик. Выполняешь первые два этапа хакатонного проекта EduTech (AI-ассистент подготовки к ОГЭ/ЕГЭ). Тебе нужно собрать с нуля скелет монорепо, инициализировать backend и mobile, подготовить LLM-слой и подсеять контент в БД.

# Жёсткие правила

- Читай CLAUDE.md в корне репо и соблюдай его строго: терсный код, без комментариев кроме неочевидной логики, без докстрингов на коротких функциях, без type hints если не просят, без try/except без необходимости, плоско вместо классовых иерархий, минимум принтов.
- Все Python-команды через uv (uv init, uv add, uv run). Не используй pip напрямую.
- Не добавляй то, что я не просил: argparse, logging-настройки сверх стандартного, CLI-обёртки, Alembic, pre-commit, husky, CI, Storybook, тесты сверх минимума.
- Не пиши README длиннее 30 строк. Не плоди .md-файлы кроме одного корневого README.md и infra/README.md.
- Если возникает выбор «правильно по продакшну» vs «быстро для хакатона» — выбирай быстро.
- Работай по этапам в указанном порядке. После каждого этапа коротко в одну строку отчитайся «этап N готов» и переходи дальше. Не задавай уточняющих вопросов — решай сам по контексту, если что-то неоднозначно.

# Стек (уже зафиксирован)

- Backend: Python 3.12, FastAPI, SQLModel, SQLite, sse-starlette, httpx, pyyaml, pydantic-settings, python-jose
- Mobile: Expo SDK 52 (new arch), TypeScript strict, expo-router, NativeWind v4, Zustand, TanStack Query, react-native-mmkv, expo-sqlite, react-hook-form + zod, reanimated 3, moti, react-native-math-view, axios
- AI: YandexGPT Pro через REST, тонкий адаптер LLMClient
- Деплой: docker compose + Caddy на одной VM в Yandex Cloud

# Этап 0.1 — Скаффолд монорепо

Создай в корне (текущая директория, рядом с уже существующим CLAUDE.md):

- backend/        пустая папка пока
- mobile/         пустая папка пока
- content/        пустая папка пока
- infra/          пустая папка пока
- prompts/        уже существует, не трогай
- .gitignore      объединённый: Python (.venv, __pycache__, *.pyc, .pytest_cache, .ruff_cache, *.db), Node (node_modules, .expo, dist, *.log), IDE (.idea, .vscode/*, !.vscode/settings.json), env (.env, .env.local), macOS (.DS_Store)
- .editorconfig   utf-8, lf, indent 2 для js/ts/yaml/json, 4 для python, trim trailing whitespace
- README.md       не более 30 строк, секции: «Что это», «Структура», «Быстрый старт» с командами `cd backend && uv run uvicorn app.main:app --reload` и `cd mobile && npx expo start`

Не делай git init — репо может уже быть инициализировано.

# Этап 0.2 — Backend init

В backend/:

1. uv init --python 3.12, затем uv add fastapi "uvicorn[standard]" sqlmodel pydantic-settings "python-jose[cryptography]" httpx sse-starlette pyyaml jinja2
2. uv add --dev ruff pytest pytest-asyncio
3. Создай структуру:
   - app/__init__.py (пустой)
   - app/main.py — FastAPI приложение, CORS open *, healthcheck GET /health -> {"status":"ok"}, при старте вызывает init_db() из app.db
   - app/config.py — Settings(BaseSettings) с полями: database_url (default sqlite:///./app.db), jwt_secret (default "dev-secret-change-me"), jwt_expires_days (default 30), yandex_api_key, yandex_folder_id, yandex_model_uri (default "gpt://{folder_id}/yandexgpt/latest"), читает из .env
   - app/db.py — create_engine, get_session dependency yield, init_db() с SQLModel.metadata.create_all
   - app/models/__init__.py — пустой пока (заполнится в 1.1)
   - app/api/__init__.py — пустой пока
   - app/services/__init__.py — пустой
   - app/llm/__init__.py — пустой пока
4. .env.example с пустыми значениями YANDEX_API_KEY и YANDEX_FOLDER_ID, дефолтами остального
5. Dockerfile multi-stage на python:3.12-slim: builder ставит uv и зависимости, runtime копирует .venv и app/, запускает uvicorn app.main:app --host 0.0.0.0 --port 8000
6. .dockerignore: __pycache__, .venv (на самом деле копируем из builder, но из контекста исключаем), *.db, .env, tests/
7. pyproject.toml: добавь ruff конфиг — line-length 100, target py312, select E,F,I,UP

Проверь: uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 должен стартовать, GET /health должен возвращать json.

# Этап 0.3 — Mobile init

В mobile/:

1. Создай Expo проект: npx create-expo-app@latest . --template default (TypeScript). После — удали дефолтные экраны-примеры (папка app/(tabs) если есть, и весь boilerplate из шаблона), оставив только app/_layout.tsx и app/index.tsx.
2. Включи new architecture в app.json (newArchEnabled: true).
3. Установи зависимости одной командой: npx expo install expo-router expo-linking expo-constants expo-status-bar expo-sqlite expo-notifications react-native-mmkv react-native-reanimated react-native-gesture-handler react-native-safe-area-context react-native-screens react-native-svg
4. Установи остальное через npm: npm i nativewind tailwindcss@3.4.10 zustand @tanstack/react-query @tanstack/query-async-storage-persister @tanstack/react-query-persist-client react-hook-form zod @hookform/resolvers moti react-native-math-view axios react-native-toast-message uuid
5. Установи dev: npm i -D @types/uuid prettier prettier-plugin-tailwindcss
6. Настрой NativeWind v4:
   - tailwind.config.js со скоупом content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"], extend.colors: { primary: "#2D6CDF", accent: "#FFB020", success: "#2DBE6C", danger: "#E5484D", surface: "#F7F8FA", ink: "#0F172A" }
   - global.css с @tailwind base/components/utilities
   - metro.config.js — обёртка через withNativeWind
   - babel.config.js — preset babel-preset-expo, plugins: react-native-worklets/plugin (для reanimated, ставится с reanimated)
   - app/_layout.tsx импортирует global.css
7. tsconfig.json — strict: true, paths "@/*": ["./*"]
8. Структура (создай пустые index.ts с реэкспортами где имеет смысл):
   - app/_layout.tsx — QueryClientProvider + GestureHandlerRootView + SafeAreaProvider + Stack screenOptions={{ headerShown: false }}
   - app/index.tsx — пока просто <Redirect href="/(tabs)/" /> (заглушка для следующих этапов)
   - app/(onboarding)/_layout.tsx — Stack
   - app/(tabs)/_layout.tsx — Tabs с 4 экранами: index/Главная (home), plan/План (calendar), topics/Темы (grid), profile/Профиль (person). Иконки @expo/vector-icons (Ionicons). Активный цвет primary, неактивный slate-400.
   - app/(tabs)/index.tsx — placeholder экран с Text «Дашборд» (заполнится позже)
   - app/(tabs)/plan.tsx, topics.tsx, profile.tsx — аналогичные placeholders
   - components/ui/ — пустая, .gitkeep
   - hooks/ — пустая
   - lib/ — пустая
   - store/ — пустая
9. app.json: scheme "edutech", иконку и splash оставь дефолтные шаблонные (заменим в Этапе 8)
10. .env.example с EXPO_PUBLIC_API_URL=http://localhost:8000

Проверь: npx expo start --no-dev --minify не должен падать по типам. Запускать симулятор не нужно — на хакатоне доверяем тайпчекеру.

# Этап 0.4 — LLMClient адаптер и промпты

В backend/app/llm/:

1. client.py:
   - класс LLMClient с конструктором, берущим settings
   - async def chat(messages, temperature=0.3, max_tokens=2000, response_format="text") — POST на https://llm.api.cloud.yandex.net/foundationModels/v1/completion с заголовком Authorization: Api-Key {key} и x-folder-id. Тело: {modelUri, completionOptions: {stream: false, temperature, maxTokens: str(max_tokens)}, messages}. Парсит result.alternatives[0].message.text. Если response_format="json" — добавляет в system-промпт инструкцию вернуть только JSON и парсит через json.loads с одной попыткой исправления (вырезает блок ```json ... ```).
   - async def stream(messages, **kwargs) — то же, но stream=True, эндпоинт …/completion, читает SSE-стрим httpx и yields текстовые дельты
   - httpx.AsyncClient с timeout 60s, retry 3 раза с бэкоффом 1,2,4 секунды на сетевые ошибки (httpx.ConnectError, ReadTimeout)

2. prompts.py:
   - функция load_prompt(name, **vars) -> list[dict]: читает prompts/{name}.yaml, рендерит через jinja2.Template переменные в каждом поле system/user, возвращает [{"role":"system","text":...},{"role":"user","text":...}] (формат YandexGPT messages)

3. prompts/diagnose.yaml:
   system:
     Ты опытный методист подготовки к ОГЭ и ЕГЭ. Анализируешь результат диагностики ученика и возвращаешь только валидный JSON без markdown-обёртки.
   user:
     Ученик класса {{ grade }} готовится к {{ exam }} по предмету «{{ subject_name }}». Цель: {{ goal }}.
     Результаты диагностики (тема → правильность):
     {{ answers_summary }}

     Текущие оценки уверенности по темам (0..1):
     {{ mastery_summary }}

     Верни JSON со схемой:
     {
       "strong_topics": [{"topic_id": int, "comment": "одно предложение"}],
       "weak_topics": [{"topic_id": int, "comment": "одно предложение, что именно западает"}],
       "priority_skills": ["навык 1", "навык 2", "навык 3"],
       "estimated_score": int,
       "overall_comment": "2-3 предложения личного обращения к ученику"
     }

4. prompts/plan.yaml:
   system:
     Ты строишь персональный учебный план подготовки к ОГЭ/ЕГЭ. Возвращаешь только валидный JSON.
   user:
     Ученик: класс {{ grade }}, экзамен {{ exam }}, предмет «{{ subject_name }}», цель {{ goal }}.
     Темы в порядке приоритета (priority = низкий mastery × вес в экзамене):
     {{ topics_priority }}

     Построй план на 14 дней. Каждый день — 2-3 темы общим объёмом 15-30 минут. Сложные темы повтори несколько раз с интервалом. В первые 3 дня — самые приоритетные пробелы.

     Верни JSON:
     {
       "days": [
         {"day_index": 1, "topics": [{"topic_id": int, "minutes": int, "focus": "что отрабатываем"}], "summary": "одна фраза"}
       ]
     }

5. prompts/explain_error.yaml:
   system:
     Ты опытный репетитор. Объясняешь ученику ошибку в задаче живо и понятно, как человек. Используешь markdown и LaTeX ($...$ для inline, $$...$$ для блочных формул). Не сыплешь канцеляритом.
   user:
     Тема: {{ topic_name }}
     Задача:
     {{ statement }}

     Эталонное решение:
     {{ solution }}

     Правильный ответ: {{ correct_answer }}
     Ответ ученика: {{ user_answer }}

     Сделай разбор по структуре:
     **Где ошибка** — конкретный шаг и место.
     **Почему так получилось** — какое типичное заблуждение или невнимательность.
     **Как правильно** — пошаговое решение, 3-5 шагов с формулами.
     **Попробуй похожую** — придумай аналогичную задачу на тот же навык (без решения).

     Пиши на «ты», тепло, без лекций.

6. prompts/tutor_chat.yaml:
   system:
     Ты AI-репетитор по предметам ОГЭ и ЕГЭ. Ведёшь диалог методом Сократа: задаёшь наводящие вопросы, помогаешь думать, не выдаёшь готовый ответ сразу. Если ученик настаивает — постепенно подводишь к решению с пояснениями. Используешь markdown и LaTeX для формул. Текущий предмет: {{ subject_name }}. Известные пробелы ученика: {{ weak_topics }}.
   user:
     {{ user_message }}

Проверь: добавь временный скрипт scripts/smoke_llm.py — берёт load_prompt("diagnose", grade=11, exam="ЕГЭ", subject_name="математика", goal="высокий балл", answers_summary="…", mastery_summary="…") и принтит результат. НЕ запускай его (нет ключа), просто убедись что импорт работает: uv run python -c "from app.llm.client import LLMClient; from app.llm.prompts import load_prompt; print(load_prompt('diagnose', grade=11, exam='ЕГЭ', subject_name='матем', goal='90+', answers_summary='x', mastery_summary='y'))"

# Этап 0.5 — Инфра деплоя

В infra/:

1. docker-compose.yml:
   ```yaml
   services:
     backend:
       build: ../backend
       restart: unless-stopped
       environment:
         - DATABASE_URL=sqlite:////data/app.db
         - JWT_SECRET=${JWT_SECRET}
         - YANDEX_API_KEY=${YANDEX_API_KEY}
         - YANDEX_FOLDER_ID=${YANDEX_FOLDER_ID}
       volumes:
         - ./data:/data
     caddy:
       image: caddy:2-alpine
       restart: unless-stopped
       ports:
         - "80:80"
         - "443:443"
       volumes:
         - ./Caddyfile:/etc/caddy/Caddyfile:ro
         - caddy_data:/data
         - caddy_config:/config
       depends_on:
         - backend
   volumes:
     caddy_data:
     caddy_config:
   ```

2. Caddyfile:
   ```
   {$DOMAIN} {
     reverse_proxy backend:8000
     encode gzip
   }
   ```

3. deploy.sh — bash-скрипт: rsync исключая node_modules/.venv/.expo/data на $DEPLOY_HOST:$DEPLOY_PATH, затем ssh выполняет `cd $DEPLOY_PATH/infra && docker compose --env-file ../.env up -d --build`. В начале set -euo pipefail.

4. infra/.env.example: DOMAIN=example.sslip.io, JWT_SECRET=, YANDEX_API_KEY=, YANDEX_FOLDER_ID=, DEPLOY_HOST=, DEPLOY_PATH=/opt/edutech

5. infra/README.md (до 30 строк): шаги — создать VM в YC (2 vCPU, 4 GB, Ubuntu 22.04), открыть 80/443, поставить docker, склонировать репо или использовать rsync через deploy.sh, привязать домен через sslip.io ({IP}.sslip.io) для бесплатного HTTPS.

# Этап 1.1 — SQLModel схема БД

В backend/app/models/:

Создай по одному файлу на сущность. Все модели — SQLModel(table=True), id обычно через Field(default_factory=uuid.uuid4, primary_key=True) кроме случаев когда указано иначе. Используй datetime.now с default_factory.

1. user.py — User:
   - id: uuid (str), device_id: str (unique, index), grade: int|None, exam: str|None, goal: str|None, subjects: str (json-сериализованный список кодов, default "[]"), onboarding_completed: bool default False, created_at: datetime

2. subject.py — Subject:
   - code: str (primary_key, например "math_base"), name: str, exam: str ("ОГЭ"|"ЕГЭ")

3. topic.py — Topic:
   - id: int (primary_key, auto), subject_code: str (FK), name: str, codifier_code: str (index), exam_weight: float (0..1), theory_md: str (default "")

4. task.py — Task:
   - id: int (auto), subject_code: str, topic_id: int (FK), difficulty: int (1..5), type: str ("multi_choice"|"short_answer"|"numeric"), statement_md: str, options: str (json default "[]"), answer: str, solution_md: str

5. attempt.py — Attempt:
   - id: uuid, user_id: uuid (FK), task_id: int (FK), user_answer: str, is_correct: bool, is_diagnostic: bool default False, session_id: str|None (для диагностики/урока), created_at: datetime

6. mastery.py — Mastery:
   - id: uuid, user_id: uuid (FK), topic_id: int (FK), alpha: float default 1.0, beta: float default 1.0, updated_at: datetime
   - индекс composite (user_id, topic_id) unique
   - property mastery: float = alpha / (alpha + beta) — реализуй как обычный метод, не Column

7. diagnostic.py — DiagnosticResult и DiagnosticSession:
   - DiagnosticSession: id (uuid), user_id, subject_code, task_ids: str (json), current_index: int default 0, finished: bool default False, created_at
   - DiagnosticResult: id (uuid), user_id, subject_code, weak_topics: str (json), strong_topics: str (json), priority_skills: str (json), estimated_score: int, overall_comment: str, created_at

8. plan.py — LearningPlan:
   - id: uuid, user_id, subject_code, days: str (json), created_at
   - формат days json: [{"day_index":1,"date":"2026-05-15","topics":[{"topic_id":3,"minutes":20,"focus":"..."}],"status":"available"|"locked"|"done","summary":"..."}]

9. chat.py — ChatMessage:
   - id: uuid, user_id, subject_code, role: str ("user"|"assistant"), content: str, created_at

10. __init__.py — реэкспорт всех моделей чтобы SQLModel.metadata их увидел: from .user import User; from .subject import Subject; ... и __all__.

После: убедись что app/main.py при старте импортирует app.models (через app.db.init_db, который трогает metadata) и таблицы создаются.

# Этап 1.2 — Сиды контента

В content/ создай JSON-файлы:

1. subjects.json:
   ```json
   [
     {"code": "math_base", "name": "Математика (база)", "exam": "ЕГЭ"},
     {"code": "rus", "name": "Русский язык", "exam": "ЕГЭ"},
     {"code": "soc", "name": "Обществознание", "exam": "ЕГЭ"}
   ]
   ```

2. topics_math.json — 10 тем матбазы ЕГЭ по кодификатору ФИПИ:
   - "1.1" Числа и вычисления (вес 0.10)
   - "1.2" Алгебраические выражения (0.08)
   - "1.3" Уравнения и системы (0.12)
   - "1.4" Неравенства (0.08)
   - "1.5" Функции (0.10)
   - "1.6" Числовые последовательности (0.05)
   - "2.1" Планиметрия (0.12)
   - "2.2" Стереометрия (0.08)
   - "3.1" Статистика и теория вероятностей (0.10)
   - "4.1" Прикладная математика и текстовые задачи (0.17)

   Формат каждого элемента: {"codifier_code","name","exam_weight","theory_md"}
   theory_md — 3-5 предложений краткой теории по теме с 1-2 формулами в LaTeX.

3. topics_rus.json — 10 тем русского ЕГЭ (орфография, пунктуация, лексика, морфология, синтаксис, текст и его анализ, средства выразительности, нормы ударения, грамматические нормы, культура речи). Веса в сумме около 1.0.

4. topics_soc.json — 10 тем обществознания (человек и общество, экономика, социальные отношения, политика, право, духовная сфера, познание, социальные институты, глобализация, мировоззрение).

5. tasks_math.json — 50 задач (по 5 на каждую тему). Каждая:
   {"topic_codifier_code","difficulty"(1-5),"type","statement_md","options"(если multi_choice),"answer","solution_md"}
   Бери реальные формулировки уровня ЕГЭ-базы из открытого банка ФИПИ (по памяти). Если не уверен в задаче — формулируй проще, но корректно. Решения 3-5 шагов с формулами в LaTeX.

6. tasks_rus.json — 50 задач (5 на тему). Преимущественно multi_choice и short_answer.

7. tasks_soc.json — 50 задач (5 на тему). Преимущественно multi_choice.

В backend/scripts/seed_content.py:
- читает все JSON из ../content/
- upsert Subject по code
- upsert Topic по (subject_code, codifier_code)
- upsert Task по (subject_code, topic_codifier_code, hash(statement_md)) — храни хэш как часть… ладно, проще: чисти таблицу Task перед сидом (это hackathon). Subject и Topic делай idempotent по ключу.
- запуск: cd backend && uv run python -m scripts.seed_content

Не пиши aiohttp-парсер ФИПИ. Задачи кладёшь руками в JSON.

# Финальные проверки (выполни сам)

1. cd backend && uv run uvicorn app.main:app — стартует, GET http://localhost:8000/health возвращает 200
2. cd backend && uv run python -m scripts.seed_content — выполняется, в app.db появляются строки (можно проверить через sqlite3 app.db ".tables" и ".schema task")
3. cd backend && uv run ruff check . — без ошибок
4. cd mobile && npx tsc --noEmit — без ошибок типов
5. Структура файлов соответствует тому что описано выше

После всех этапов одной строкой отчитайся «Этапы 0 и 1 готовы» и перечисли что НЕ удалось доделать (если что-то отложил).

Поехали.
```

---

## Acceptance criteria для проверки

После того как Claude Code отработает, пробеги по списку:

- [ ] Существуют папки `backend/`, `mobile/`, `content/`, `infra/`, `prompts/`
- [ ] Корневой README.md ≤ 30 строк
- [ ] `cd backend && uv run uvicorn app.main:app` стартует без ошибок
- [ ] `GET http://localhost:8000/health` возвращает `{"status":"ok"}`
- [ ] В `backend/app/llm/prompts/` лежат 4 YAML-файла
- [ ] `from app.llm.prompts import load_prompt` рендерит шаблон без ошибок
- [ ] В `backend/app/models/` 9 файлов моделей + `__init__.py` с реэкспортом
- [ ] `cd backend && uv run python -m scripts.seed_content` создаёт таблицы и заполняет их
- [ ] В `app.db` (sqlite) есть 3 subjects, ~30 topics, ~150 tasks
- [ ] `cd mobile && npx tsc --noEmit` проходит без ошибок типов
- [ ] В `mobile/app/` существуют `_layout.tsx`, `(tabs)/_layout.tsx` с 4 табами
- [ ] NativeWind работает: `className="bg-primary"` в любом компоненте не падает
- [ ] В `infra/` есть `docker-compose.yml`, `Caddyfile`, `deploy.sh`

## Что почти наверняка придётся доправить руками

- **Качество задач в content/**: Claude может сгенерить задачи с ошибками в условиях/решениях. Прогони глазами хотя бы по 2-3 задачи на тему. Если плохо — попроси регенерировать отдельным промптом по конкретной теме.
- **Веса тем**: проверь что суммы exam_weight по предметам близки к 1.0.
- **Reanimated babel-plugin**: в Expo SDK 52 плагин называется `react-native-worklets/plugin`, а не `react-native-reanimated/plugin`. Если падает на запуске — поправь.
- **YANDEX_FOLDER_ID в model_uri**: дефолт `gpt://{folder_id}/yandexgpt/latest` — это шаблон, Claude должен подставить folder_id в рантайме в client.py. Проверь.

## Следующий шаг

После прохождения acceptance — переходить к этапу 2 (Backend API: auth, профиль, диагностика). Сделаю промпт для него отдельно.
