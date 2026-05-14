# План работ — AI-ассистент ОГЭ/ЕГЭ

Разбивка хакатонного проекта (4 дня, соло + Claude Code) на подзадачи. Каждая подзадача содержит готовый промпт для Claude Sonnet в Claude Code — копируешь в чат, проверяешь результат, переходишь к следующей.

**Условные обозначения:**
- Все пути от корня репозитория `Tbank-case/`
- Backend живёт в `backend/`, мобильное приложение в `mobile/`
- Промпты сгруппированы так, чтобы можно было выполнять их последовательно, не возвращаясь назад
- В каждом промпте уже зашит контекст стека — Claude Code не нужно объяснять, что такое FastAPI или Expo

**Стек напоминание:**
- Mobile: Expo SDK 52 + RN new arch, TypeScript, expo-router, NativeWind v4, Zustand, TanStack Query, expo-sqlite, MMKV, react-native-math-view, reanimated 3
- Backend: Python 3.12, FastAPI, SQLModel, SQLite, sse-starlette, httpx, uv для зависимостей
- AI: YandexGPT Pro через REST, тонкий адаптер `LLMClient`
- Деплой: 1 VM в Yandex Cloud + docker compose + Caddy

---

## Этап 0. Подготовка (день 1, первые 2 часа)

### 0.1 Скаффолд монорепо

**Что делать:** создать корневую структуру `backend/` и `mobile/`, общие конфиги (gitignore, README, .editorconfig), docker-compose для локальной разработки.

```
Создай монорепозиторий для хакатонного проекта в текущей директории.

Структура:
- backend/        FastAPI приложение (Python 3.12, uv)
- mobile/         Expo приложение (TypeScript)
- content/        JSON-сиды задач ОГЭ/ЕГЭ
- infra/          docker-compose, Caddyfile, скрипты деплоя
- .gitignore      объединённый Python + Node + Expo + IDE
- README.md       краткое описание проекта и команды запуска

Не создавай README длиннее 30 строк. Не добавляй CI — он не нужен на хакатоне.
Не инициализируй git внутри подпапок, только один git init в корне.
```

### 0.2 Backend init (FastAPI + SQLModel + uv)

```
Инициализируй FastAPI-проект в backend/ с использованием uv.

Требования:
- Python 3.12, зависимости через uv (uv init, uv add)
- Зависимости: fastapi, uvicorn[standard], sqlmodel, pydantic-settings, python-jose[cryptography], httpx, sse-starlette, pyyaml
- Dev-зависимости: ruff, pytest, pytest-asyncio
- Структура backend/app/:
  - main.py            точка входа FastAPI
  - config.py          настройки через pydantic-settings (.env)
  - db.py              SQLModel engine + get_session dependency
  - models/            SQLModel модели (пока пустая)
  - api/               роутеры (пока пустая)
  - services/          бизнес-логика (пока пустая)
  - llm/               клиент YandexGPT + промпты (пока пустая)
- Healthcheck GET /health возвращает {"status": "ok"}
- CORS открыт для всех источников (хакатон, на проде сузим)
- Dockerfile (multi-stage, на python:3.12-slim) + .dockerignore

Не добавляй Alembic — миграции делаем через SQLModel.metadata.create_all().
Не добавляй pre-commit хуки.
```

### 0.3 Mobile init (Expo + Router + NativeWind)

```
Инициализируй Expo-проект в mobile/.

Требования:
- npx create-expo-app@latest с TypeScript template, Expo SDK 52
- Включена new architecture (newArchEnabled: true в app.json)
- Установить и настроить:
  - expo-router (tabs + stack)
  - NativeWind v4 (tailwindcss, файл tailwind.config.js, global.css с директивами)
  - zustand
  - @tanstack/react-query + persistent storage
  - react-native-mmkv
  - expo-sqlite
  - react-hook-form, zod, @hookform/resolvers
  - react-native-reanimated 3 (babel plugin)
  - moti
  - react-native-math-view
  - axios

- Структура mobile/app/ (expo-router):
  - _layout.tsx              корневой layout с QueryClientProvider и safe area
  - index.tsx                редирект на онбординг или дашборд
  - (onboarding)/_layout.tsx стэк онбординга
  - (tabs)/_layout.tsx       табы (Home, Plan, Topics, Profile)
  - (tabs)/index.tsx         дашборд
- Папки: components/, hooks/, lib/ (api клиент, mmkv, types), store/ (zustand)
- tsconfig.json со strict: true
- В app.json настроить scheme, splash, иконку (плейсхолдеры пока)

Цветовая палитра в tailwind.config.js: primary #2D6CDF, accent #FFB020, success #2DBE6C, danger #E5484D, surface #F7F8FA, ink #0F172A.
Шрифт системный, не подключай кастомные шрифты пока.
```

### 0.4 LLMClient адаптер + промпты

```
Создай в backend/app/llm/ слой работы с YandexGPT.

Файлы:
- client.py:
  - класс LLMClient с методами:
    - async chat(messages: list[dict], temperature: float = 0.3, max_tokens: int = 2000, response_format: Literal["text", "json"] = "text") -> str
    - async stream(messages: list[dict], **kwargs) -> AsyncIterator[str]
  - реализация через httpx.AsyncClient к https://llm.api.cloud.yandex.net/foundationModels/v1/completion
  - модель yandexgpt/latest, авторизация через Api-Key из настроек
  - retry с экспоненциальным бэкоффом (3 попытки) на сетевые ошибки
- prompts.py:
  - функция load_prompt(name: str, **vars) -> list[dict] — читает YAML из prompts/, рендерит Jinja2, возвращает messages
- prompts/:
  - diagnose.yaml      анализ диагностики, на вход список ответов с темами, на выход JSON {strong_topics, weak_topics, priority_skills, estimated_score}
  - plan.yaml          построение 14-дневного плана по слабым темам + весам в экзамене
  - explain_error.yaml разбор конкретной ошибки в задаче (где ошибся, почему, как правильно, аналогичная задача)
  - tutor_chat.yaml    system-prompt репетитора, сократический метод, разрешает шаги, не даёт сразу ответ

Все промпты на русском, под ОГЭ/ЕГЭ. В каждом YAML структура:
  system: |
    ...
  user: |
    ...

Добавь settings YANDEX_API_KEY, YANDEX_FOLDER_ID, YANDEX_MODEL_URI в config.py.
```

### 0.5 Деплой backend на YC VM

```
Подготовь инфраструктуру деплоя backend на одну VM в Yandex Cloud.

Файлы в infra/:
- docker-compose.yml:
  - сервис backend (build из ../backend, expose 8000)
  - сервис caddy (image caddy:2-alpine, ports 80/443, volume к Caddyfile и data)
  - volume для sqlite-файла (./data:/data в backend, env DATABASE_URL=sqlite:////data/app.db)
- Caddyfile:
  - reverse_proxy на backend:8000
  - автоматический HTTPS через Let's Encrypt
  - placeholder домена {$DOMAIN}
- deploy.sh:
  - rsync содержимого репо на VM по SSH
  - docker compose pull / build / up -d на VM
- README в infra/ с шагами:
  - создать VM в YC (2 vCPU, 4 GB, Ubuntu 22.04)
  - открыть порты 80/443
  - привязать домен (или использовать sslip.io)
  - запустить deploy.sh

Не делай Terraform — это лишнее на хакатоне.
```

---

## Этап 1. Контент и схема данных (день 1, оставшиеся часы)

### 1.1 Схема БД (SQLModel)

```
Создай SQLModel-модели в backend/app/models/.

Сущности:
- User: id (uuid), device_id (unique), grade (8-11), exam (ОГЭ/ЕГЭ), goal (min/good/excellent), subjects (json-список выбранных), created_at
- Subject: code (math_base, rus, soc), name, exam (ОГЭ/ЕГЭ)
- Topic: id, subject_code (fk), name, codifier_code (по ФИПИ), exam_weight (float, вес в экзамене 0..1)
- Task: id, subject_code, topic_id (fk), difficulty (1-5), type (multi_choice/short_answer/numeric), statement_md, options (json для multi_choice), answer, solution_md
- Attempt: id, user_id, task_id, user_answer, is_correct (bool), is_diagnostic (bool), created_at
- Mastery: id, user_id, topic_id, alpha (float), beta (float), updated_at
  - mastery = alpha / (alpha + beta)
- DiagnosticResult: id, user_id, subject_code, weak_topics (json), strong_topics (json), estimated_score (int), llm_summary (text), created_at
- LearningPlan: id, user_id, subject_code, days (json: [{day_index, date, topics: [{topic_id, minutes}], status}]), created_at

Один файл на сущность в backend/app/models/, плюс __init__.py с реэкспортом.
В main.py при старте вызывай SQLModel.metadata.create_all(engine).
```

### 1.2 Сиды контента

```
Создай систему сидов в backend/scripts/seed_content.py.

Источники данных: положи вручную составленные JSON-файлы в content/:
- content/subjects.json     список 3 предметов
- content/topics_math.json  ~10-15 тем математики базы с codifier_code и весами
- content/topics_rus.json   ~10-15 тем русского
- content/topics_soc.json   ~10-15 тем обществознания
- content/tasks_math.json   60 задач по математике, привязка к topic_id
- content/tasks_rus.json    60 задач по русскому
- content/tasks_soc.json    60 задач по обществознанию

Каждая задача: {topic_codifier_code, difficulty, type, statement_md, options?, answer, solution_md}

Скрипт seed_content.py:
- читает все json
- создаёт Subject, Topic, Task в БД (idempotent через upsert по codifier_code/task hash)
- запускается командой: uv run python scripts/seed_content.py

ВАЖНО: задачи бери из открытого банка ФИПИ (fipi.ru/oge, fipi.ru/ege), русские формулировки. Достаточно 5-7 задач на тему. Решения краткие, но содержательные (3-5 шагов).
Темы должны покрывать кодификатор: для матбазы — числа и вычисления, алгебраические выражения, уравнения, неравенства, числовые последовательности, функции, координаты, геометрия (планиметрия), статистика и теория вероятностей, прикладная математика.

Если задач слишком много для одной сессии — сделай заглушки с TODO для половины тем и заполни только 3-4 темы по каждому предмету хорошо.
```

---

## Этап 2. Backend API (день 1 вечер — день 2 утро)

### 2.1 Аноним-аутентификация

```
Реализуй анонимную аутентификацию в backend/app/api/auth.py.

Эндпоинты:
- POST /auth/anonymous
  body: {device_id: str}
  - если User с таким device_id есть — возвращает существующего
  - иначе создаёт нового
  - возвращает {access_token, user: {id, grade, exam, subjects, onboarding_completed}}
  - onboarding_completed = True если заполнены grade/exam/subjects

JWT через python-jose, HS256, secret из config, expires 30 дней.
Dependency get_current_user в app/api/deps.py — читает Bearer token, возвращает User.
```

### 2.2 Профиль и онбординг

```
Реализуй эндпоинты профиля в backend/app/api/users.py.

Эндпоинты:
- GET /me — текущий пользователь (требует auth)
- PATCH /me — обновление grade/exam/goal/subjects (используется после онбординга)
  body: {grade?, exam?, goal?, subjects?: list[str]}
- GET /me/subjects — список доступных предметов с прогрессом
  ответ: [{code, name, mastery_avg, last_session_at}]

После PATCH /me, если subjects изменились — для каждой новой пары (user, topic) создать Mastery с alpha=1, beta=1 (Beta(1,1) = равномерное распределение).
```

### 2.3 Диагностика

```
Реализуй диагностику в backend/app/api/diagnostic.py и services/diagnostic.py.

Эндпоинты:
- POST /diagnostic/start
  body: {subject_code}
  - выбирает 6 задач: по 1 из каждой большой темы предмета, разной сложности (2 лёгких, 3 средних, 1 сложная)
  - создаёт DiagnosticSession (можно в памяти/Redis или просто временная таблица, либо хранить в payload)
  - возвращает {session_id, tasks: [{id, statement_md, type, options?}]}
- POST /diagnostic/answer
  body: {session_id, task_id, user_answer}
  - сохраняет Attempt (is_diagnostic=True)
  - не возвращает правильность (важно: ученик не должен видеть результат во время диагностики)
  - возвращает {next_task_index, completed: bool}
- POST /diagnostic/finish
  body: {session_id}
  - триггерит сервис finalize_diagnostic:
    1. собирает все попытки сессии
    2. обновляет Mastery по каждой задействованной теме (Bayesian update Beta)
    3. формирует payload для LLM (список тем с mastery и правильностью ответов)
    4. вызывает LLM с промптом diagnose, parse JSON ответ
    5. рассчитывает estimated_score (грубо: средний mastery * макс_балл_по_предмету)
    6. сохраняет DiagnosticResult
  - возвращает DiagnosticResult со всеми полями

Сервис mastery_update в services/mastery.py:
- update_mastery(user_id, topic_id, is_correct) -> увеличивает alpha на 1 если правильно, beta на 1 если нет
```

### 2.4 План обучения

```
Реализуй построение плана в backend/app/api/plan.py и services/plan.py.

Эндпоинты:
- POST /plan/generate
  body: {subject_code}
  - берёт текущие mastery пользователя по предмету и веса тем
  - сортирует темы по приоритету (low mastery × high exam_weight = high priority)
  - вызывает LLM с промптом plan, передавая темы и цель пользователя
  - LLM возвращает JSON с 14 днями, каждый день 2-3 темы и время
  - сохраняет LearningPlan
- GET /plan/current?subject_code=... — текущий план
- POST /plan/day/{day_index}/complete — отметить день выполненным

Дни недоступны вперёд: разрешено стартовать только день, у которого все предыдущие отмечены как complete или skipped.
```

### 2.5 Уроки + объяснение ошибки

```
Реализуй уроки в backend/app/api/lesson.py.

Эндпоинты:
- POST /lesson/start
  body: {subject_code, topic_id}
  - выбирает 4 задачи по теме, сложность около текущего mastery (mastery 0.3 → difficulty 2-3)
  - возвращает {lesson_id, theory_md, tasks: [...]}
  - theory_md — короткая теория по теме (пока хардкод или из Topic.theory_md поля, добавь его в модель)
- POST /lesson/answer
  body: {lesson_id, task_id, user_answer}
  - сохраняет Attempt
  - обновляет Mastery
  - возвращает {is_correct, next_task?}
  - НЕ возвращает разбор ошибки в этом эндпоинте — клиент сам запросит стрим
- POST /lesson/finish
  body: {lesson_id}
  - возвращает {tasks_total, correct, mastery_before, mastery_after, xp_earned}

Эндпоинт стриминга разбора:
- POST /lesson/explain (SSE через sse-starlette)
  body: {task_id, user_answer}
  - формирует messages из explain_error промпта (передаёт task statement, solution, user_answer)
  - стримит чанки от YandexGPT через LLMClient.stream
  - формат событий: event: chunk, data: {"text": "..."}
  - финальное событие: event: done, data: {"structured": {where, why, how, similar_task_id?}}

Чтобы получить structured в конце — после стрима делается обычный вызов LLM с теми же сообщениями и response_format=json. Можно упростить: только стрим текстового объяснения без structured, если не успеваем.
```

### 2.6 Чат-репетитор

```
Реализуй чат с AI-репетитором в backend/app/api/chat.py.

Эндпоинты:
- GET /chat/history?subject_code=... — последние 50 сообщений
- POST /chat/message (SSE)
  body: {subject_code, message: str}
  - сохраняет user-message в БД (ChatMessage модель: id, user_id, subject_code, role, content, created_at)
  - подгружает контекст: последние 10 сообщений + список слабых тем пользователя
  - стримит ответ от LLM с промптом tutor_chat
  - после завершения сохраняет assistant-message

Модель ChatMessage добавь в models/.
```

---

## Этап 3. Mobile foundation (день 2)

### 3.1 API-клиент и auth-хук

```
Создай слой API в mobile/lib/.

Файлы:
- mobile/lib/api.ts:
  - axios instance с baseURL из EXPO_PUBLIC_API_URL
  - interceptor добавляет Authorization: Bearer {token из MMKV}
  - типы: User, Subject, Topic, Task, DiagnosticResult, LearningPlan и т.д. (из backend схем)
- mobile/lib/storage.ts:
  - обёртки над MMKV: getToken/setToken, getDeviceId/ensureDeviceId (генерит uuid если нет)
- mobile/lib/sse.ts:
  - EventSource-полифилл для RN через fetch + ReadableStream
  - функция streamSSE(url, body, onChunk, onDone)
- mobile/hooks/useAuth.ts:
  - при монтировании читает токен из MMKV
  - если нет — вызывает POST /auth/anonymous с device_id
  - возвращает {user, isLoading, refresh}
- mobile/hooks/api/ — папка с TanStack Query хуками:
  - useMe, useUpdateMe
  - useDiagnostic (start, answer, finish)
  - usePlan, useGeneratePlan
  - useLesson (start, answer, finish)
  - useChatHistory, useSendMessage

QueryClient настрой со staleTime 30s, retry 1.
```

### 3.2 Базовые UI-компоненты

```
Создай переиспользуемые компоненты в mobile/components/ui/.

Компоненты с NativeWind:
- Button: variants (primary, secondary, ghost, danger), sizes (sm, md, lg), loading state, disabled
- Card: с padding/rounded по умолчанию, поддержка onPress (Pressable с feedback)
- Chip: для выбора (selected/unselected), поддержка multi-select
- ProgressBar: горизонтальная, с анимацией заполнения через reanimated
- Heatmap: сетка тайлов с цветом от красного к зелёному по value 0..1, onPress на тайл
- AnimatedNumber: счётчик с анимацией смены значения (moti)
- MarkdownView: рендер markdown с поддержкой LaTeX через react-native-math-view (внутри парсит $...$ и $$...$$)
- LoadingDots: три точки-пульсации для индикации стрима

Каждый компонент в своём файле, экспорт из components/ui/index.ts.
```

### 3.3 Root layout и навигация

```
Настрой корневую навигацию в mobile/app/.

- app/_layout.tsx:
  - QueryClientProvider, GestureHandlerRootView, SafeAreaProvider
  - проверка через useAuth: пока loading — splash, дальше:
    - нет user → редирект на /(onboarding)/welcome
    - есть user но onboarding_completed=false → /(onboarding)/context
    - иначе → /(tabs)
- app/index.tsx — пустой, делает Redirect на нужный путь по логике auth
- app/(onboarding)/_layout.tsx — Stack без header
- app/(tabs)/_layout.tsx — Tabs с 4 экранами:
  - index (Главная) — иконка home
  - plan — иконка calendar
  - topics — иконка grid
  - profile — иконка user
  - использовать @expo/vector-icons (Ionicons)

Цвета табов: активный primary, неактивный slate-400.
```

---

## Этап 4. Онбординг (день 2 вторая половина)

### 4.1 Welcome-экран

```
Создай mobile/app/(onboarding)/welcome.tsx.

Содержание:
- Большой заголовок «Привет.»
- Подзаголовок 2 строки: «Я помогу тебе подготовиться к экзамену так, чтобы ты понимал, почему ошибаешься — а не просто видел галочку.»
- Иллюстрация (можно эмодзи 🧠 или Lottie-плейсхолдер пока)
- Кнопка «Начнём» снизу — на нажатие navigate('/(onboarding)/context')
- moti-анимация появления текста (slide+fade)

Не больше 60 строк JSX, никакой логики.
```

### 4.2 Контекст-визард (4 шага)

```
Создай 4 экрана в mobile/app/(onboarding)/context/.

Шаги:
- [step].tsx с dynamic route ИЛИ отдельные файлы grade.tsx, exam.tsx, subjects.tsx, goal.tsx

Каждый экран:
- Прогресс-бар сверху (1/4, 2/4, ...)
- Заголовок вопрос
- Варианты ответа большими Chip-кнопками
- Кнопка «Далее» снизу (disabled пока не выбран ответ)

Шаг 1 grade: 8, 9, 10, 11 (single)
Шаг 2 exam: ОГЭ, ЕГЭ (auto-suggest по grade: 8-9 → ОГЭ, 10-11 → ЕГЭ, но можно изменить)
Шаг 3 subjects: математика, русский, обществознание (multi, минимум 1)
Шаг 4 goal: «Сдать на минимум», «Получить хороший балл», «Высокий балл (90+)»

Состояние шагов держи в Zustand store (onboardingStore) с полями grade, exam, subjects, goal.
На последнем шаге кнопка называется «Готово» — отправляет PATCH /me, по успеху navigate('/(tabs)/').

Анимация смены экранов: горизонтальный слайд через expo-router (stack animation).
```

---

## Этап 5. Диагностика (день 3 утро)

### 5.1 Выбор предмета для диагностики

```
После онбординга по умолчанию редиректить на /(tabs) — дашборд.

На дашборде если у пользователя ещё нет DiagnosticResult ни по одному предмету — показывать большую карточку «Начни с диагностики» с кнопкой → ведёт на /diagnostic/picker.

Создай mobile/app/diagnostic/picker.tsx:
- Список выбранных пользователем предметов карточками
- Тап → navigate(`/diagnostic/${subjectCode}`)
- Сверху ссылка «Назад»
```

### 5.2 Экран диагностики

```
Создай mobile/app/diagnostic/[subject].tsx.

Логика:
- useEffect: POST /diagnostic/start → получили session_id и список задач, сохранили в локальный state
- ProgressBar сверху «3 из 6»
- Текущая задача через компонент <TaskRenderer task={current} onAnswer={...} />
- Кнопка «Далее» появляется после ответа
- НЕ показывать правильность ответа во время диагностики
- После последней задачи → POST /diagnostic/finish, навигация на /diagnostic/[subject]/analyzing
- Сохрани прогресс сессии в MMKV — если пользователь закроет, можно продолжить

UI:
- Минималистично: одна задача на экран, много воздуха
- Без таймера
- Кнопка «Пропустить» (отправит null как user_answer, считается неправильным)
```

### 5.3 Компоненты задач

```
Создай в mobile/components/task/:
- TaskRenderer.tsx — switch по task.type, рендерит нужный подкомпонент
- TaskMultiChoice.tsx — вертикальный список options как Chip-кнопок, single select
- TaskShortAnswer.tsx — TextInput + кнопка отправки
- TaskNumeric.tsx — TextInput с keyboardType="numeric"
- TaskStatement.tsx — рендер statement_md через MarkdownView с поддержкой LaTeX

Все варианты:
- Принимают props: {task, onAnswer: (answer: string) => void}
- Локально держат состояние ввода
- Не валидируют — это бизнес-логика бэка

Стиль: задача в Card, options крупные, тач-таргет минимум 56px.
```

### 5.4 Analyzing-экран

```
Создай mobile/app/diagnostic/[subject]/analyzing.tsx.

Эффект:
- 3-4 секунды анимации «AI анализирует твои ответы»
- Параллельно вызывает useQuery на /diagnostic/result/{session_id} (или результат уже пришёл с finish — тогда просто держим состояние)
- Анимация: 3 строки появляются последовательно с галочками
  1. «Считаю твой уровень по темам…»
  2. «Сравниваю с требованиями экзамена…»
  3. «Готовлю персональные рекомендации…»
- moti staggered появление
- По завершении (мин 3 сек + загрузка) navigate replace на /diagnostic/[subject]/results

Если LLM упал — fallback: всё равно показать результат на основе mastery (без LLM-комментария).
```

---

## Этап 6. Wow-моменты (день 3)

### 6.1 Результаты диагностики

```
Создай mobile/app/diagnostic/[subject]/results.tsx.

Контент сверху вниз:
- Заголовок «Вот что я узнал про тебя»
- Большая карточка: estimated_score крупно, прогноз «При работе 30 мин/день → 78 баллов к маю»
- Подзаголовок «Карта тем»
- Heatmap-сетка тем (берём из DiagnosticResult.weak_topics + strong_topics + остальные): тайл с названием темы, цвет по mastery
- Подзаголовок «Главные пробелы»
- Список 3-5 weak topics с короткими LLM-комментариями
- Кнопка снизу «Покажи мой план» → POST /plan/generate, по успеху → /plan/[subject]

Анимация: scroll-driven появление секций (можно reanimated useAnimatedScrollHandler).
Heatmap: тайлы появляются волной с задержкой 50ms каждый (moti delay).
```

### 6.2 Экран плана

```
Создай mobile/app/plan/[subject].tsx.

Контент:
- Заголовок «Твой план»
- Подзаголовок «14 дней до заметного прогресса»
- Вертикальный список из 14 карточек дней:
  - День 1 (сегодня): подсвечен primary-рамкой, статус «Сегодня»
  - День 2-14: серые, статус «Заблокировано» пока не пройдены предыдущие
  - В каждой карточке: дата, темы (2-3 чипа), длительность («20 мин»)
- Кнопка «Начать» на сегодняшнем дне → /lesson/[subject]/[topic_id] (первая тема дня)

Заблокированные дни не кликабельны, но раскрываются по тапу (показать какие темы будут).
Используй FlatList или ScrollView с моти-анимацией появления.
```

### 6.3 Экран урока

```
Создай mobile/app/lesson/[subject]/[topicId].tsx.

Состояния (state machine через Zustand или useState):
- 'theory'      показ теории
- 'task'        показ текущей задачи
- 'feedback'    показ результата (правильно/неправильно)
- 'explanation' стриминг разбора ошибки от AI
- 'summary'    итоги урока

Поток:
1. useEffect: POST /lesson/start → получили theory_md и tasks
2. Состояние theory: MarkdownView с теорией, кнопка «Понял, давай задачи»
3. Состояние task: TaskRenderer + кнопка «Ответить»
4. По ответу: POST /lesson/answer
   - is_correct=true → состояние feedback с зелёной анимацией «Правильно! +10 XP», через 1.5 сек авто-переход к следующей задаче
   - is_correct=false → состояние explanation: открывается «карточка репетитора» снизу, начинается SSE-стрим на /lesson/explain
5. Состояние explanation:
   - аватар «AI-репетитор» сверху с пульсацией
   - текст разбора печатается по мере прихода чанков (использовать useState и аппендить)
   - MarkdownView в режиме live-обновления (форматируется по мере прихода)
   - Кнопка «Понял» — переход к следующей задаче
   - Кнопка «Объясни ещё проще» — повторный стрим с инструкцией «объясни как 5-класснику»
6. После последней задачи: POST /lesson/finish → состояние summary

Это самый важный экран для демо. Уделить внимание анимациям и плавности.
```

### 6.4 SSE хук + стриминг markdown

```
Создай mobile/hooks/useLLMStream.ts.

Сигнатура:
useLLMStream(): {
  text: string,
  isStreaming: boolean,
  start: (endpoint: string, body: object) => void,
  reset: () => void
}

Реализация:
- Использует функцию streamSSE из lib/sse.ts
- При каждом chunk-событии аппендит к text
- isStreaming → true при start, false при done или error
- При сетевой ошибке выставляет fallback-текст «Связь нестабильна. Попробуй ещё раз.» и кнопку retry

В компоненте explanation использовать этот хук:
const { text, isStreaming, start } = useLLMStream()
useEffect(() => { start('/lesson/explain', {task_id, user_answer}) }, [])

Рендер: <MarkdownView content={text} /> + если isStreaming — мигающий курсор в конце.
```

---

## Этап 7. Прогресс и дашборд (день 3 вечер — день 4 утро)

### 7.1 Summary после урока

```
Создай mobile/components/lesson/SessionSummary.tsx.

Контент:
- Большая иконка успеха (или нейтральная если решено <50%)
- «5 задач, 3 правильно»
- Анимированный mastery-бар: до начала урока 0.20 → после 0.41
  - использовать reanimated useSharedValue + withTiming на старте экрана
- XP earned: «+30 XP» с counter-анимацией
- Streak: «День 1 - не теряй огонёк»
- Две кнопки: «На главную» (primary) и «Ещё одна тема» (ghost)

При появлении экрана:
- Если streak увеличился — регистрируй expo-notification на следующий день в 19:00 с текстом «Не теряй огонёк! День X. Открой и позанимайся 15 минут.»
- Использовать expo-notifications: scheduleNotificationAsync
```

### 7.2 Дашборд

```
Создай mobile/app/(tabs)/index.tsx — главный экран.

Контент сверху вниз:
- Header: приветствие «Привет!» + текущая дата
- Streak-баннер: огонёк + «День 3»
- Карточка «Сегодня в плане» (если есть активный план): тема, время, кнопка «Начать»
  - если плана нет → CTA «Пройди диагностику»
  - если день уже выполнен → «Готово на сегодня. Возвращайся завтра» с opacity
- Прогнозы по предметам: для каждого выбранного предмета карточка
  - название, текущий estimated_score, мини-полоса прогресса до цели
  - тап → переход на /plan/[subject]
- Карточка «Спроси у репетитора» → /chat

Стиль: scroll, много воздуха, карточки крупные.
```

### 7.3 Карта тем (детальный экран)

```
Создай mobile/app/(tabs)/topics.tsx.

Контент:
- Сегмент-контрол сверху для переключения предметов
- Большая Heatmap всех тем выбранного предмета
- Список тем под ней (мини-карточки): название, mastery в %, кнопка «Тренировать»
- Тап «Тренировать» → POST /lesson/start с этой темой → переход на /lesson/[subject]/[topicId]

Сегмент-контрол использует useState для активного предмета.
```

### 7.4 Чат с репетитором

```
Создай mobile/app/chat/index.tsx.

Контент:
- Сегмент-контрол выбора предмета (контекст чата)
- Список сообщений (FlatList inverted)
- Поле ввода снизу + кнопка send
- При отправке: POST /chat/message (SSE), стримим ответ как новый assistant-message

Состояние сообщений в Zustand chatStore с map subject_code → message[].
При первом открытии: GET /chat/history, заполнить store.

Markdown + LaTeX рендер сообщений через MarkdownView.
```

---

## Этап 8. Polish и демо (день 4)

### 8.1 Fallback-стратегии

```
Пройдись по приложению и добавь обработку ошибок:

- Все мутации к LLM-эндпоинтам (diagnose, plan, explain, chat) могут падать или таймаутить
- Везде использовать try/catch на уровне хуков
- Fallback UI: компонент <ErrorState message onRetry /> с дружелюбным текстом и кнопкой
- Глобальный QueryClient: настроить onError для мутаций с показом Toast (использовать react-native-toast-message)
- Для SSE-стрима: если первый чанк не пришёл за 10 секунд — таймаут, показать ErrorState

Также добавь EmptyState компонент: для случаев нет данных (план не сгенерирован, чат пуст и т.д.).

LoadingState компонент: skeleton-плитки через moti.
```

### 8.2 Анимации и моменты wow

```
Добавь финальные анимации:

- На экране диагностики: при появлении задачи лёгкий fade-up
- На результатах диагностики: heatmap-плитки появляются волной (delay по индексу * 40ms)
- На экране плана: дни появляются сверху вниз каскадом
- В уроке: переход task → feedback с зелёным flash при правильном ответе (Animated background)
- В уроке: при неправильном ответе — плавное появление «карточки репетитора» снизу (slide-up + scale)
- В summary: mastery-бар анимируется от старого значения к новому за 1.5с
- В дашборде: streak-огонёк лёгко пульсирует (loop reanimated)

Везде использовать moti для простых случаев, reanimated useSharedValue для сложных.
Тайминги: 200-400ms, easing Easing.bezier(0.2, 0.8, 0.2, 1).
```

### 8.3 Сборка демо

```
Подготовь сборку для жюри.

Шаги:
1. В mobile/eas.json создать профиль preview:
   - distribution: internal
   - android: { buildType: apk }
   - ios: { simulator: false } — но iOS не успеем, оставь только android
2. Установить EXPO_PUBLIC_API_URL на продовый бэк (домен VM)
3. Запустить: eas build --profile preview --platform android
4. Получить ссылку на .apk и QR-код
5. Положить QR-код в README в корне репо
6. Описать в README инструкцию для жюри:
   - отсканируй QR
   - установи .apk
   - открой приложение
   - сценарий демо (3 минуты): онбординг → диагностика по математике → план → первая ошибка → разбор → дашборд
```

### 8.4 Демо-сценарий и подсев данных

```
Создай скрипт backend/scripts/seed_demo_user.py.

Создаёт демо-пользователя для подстраховки на случай если у жюри не работает интернет/SMS:
- device_id = "demo-jury-001"
- grade=11, exam=ЕГЭ, subjects=[math, rus, soc], goal=excellent
- onboarding_completed=True
- Имеет DiagnosticResult по математике с заранее посчитанными значениями
- Имеет LearningPlan по математике с днём 1 в статусе available
- Имеет историю Attempt: 5 задач по теме «квадратные уравнения», 2 правильных

В Mobile добавь dev-only кнопку на welcome-экране «Войти как демо» (видна если __DEV__ или есть env-флаг) — устанавливает device_id в MMKV перед вызовом auth.

Так у тебя есть запасной аккаунт на случай если что-то сломается прямо на показе.
```

### 8.5 Финальная проверка

```
Прогон финального чеклиста перед демо:

- [ ] Backend запущен на VM, https работает, GET /health отвечает
- [ ] Все эндпоинты возвращают данные (curl-проверка)
- [ ] YandexGPT API-ключ валиден, лимиты позволяют
- [ ] .apk собран, QR-код в README
- [ ] Демо-пользователь подсеян и работает
- [ ] Приложение запускается с нуля и проходит весь flow до summary
- [ ] При плохом интернете показывает корректные ошибки, не крашится
- [ ] Логи backend пишутся (docker compose logs -f backend)
- [ ] Презентация на 3 слайда: проблема, решение, демо-видео 30 сек

Прогнать сценарий демо 3 раза подряд. Засечь время — должно укладываться в 3 минуты.
```

---

## Приоритеты при отставании

Если на день 3 видно, что не успеваем — резать в таком порядке:

1. **Чат с репетитором** (этап 7.4) — самая необязательная фича
2. **Карта тем детальная** (7.3) — есть упрощённая на результатах диагностики
3. **Локальные пуш-уведомления** (7.1) — оставить только UI streak
4. **Анимации помимо ключевых** (8.2) — оставить только в lesson и diagnostic results
5. **Поддержка обществознания** — оставить только математику и русский
6. **Поддержка русского** — оставить только математику

Минимально-жизнеспособное демо (если катастрофа): онбординг → диагностика по математике → результаты → план → 1 урок с разбором первой ошибки. Этого достаточно, чтобы показать ценность.

---

## Параллелизация с Claude Code

Claude Code хорош для рутины. Делай так:

- **Сам**: продумываешь UX, компонуешь экраны, проверяешь LLM-промпты, дебажишь интеграции
- **Claude Code**: пишет компоненты по детальному ТЗ, генерирует SQLModel-схемы, формирует JSON-сиды задач, рисует Heatmap, настраивает SSE

Один промпт = один pull request в голове. После каждого промпта 5-минутный код-ревью: проверить что не наплодил лишнего, что соответствует требованиям из CLAUDE.md, что нет fallback-кода под несуществующие сценарии.

Особое внимание к промптам на этапах 6.3 и 6.4 (урок + SSE) — там самая высокая концентрация ценности и риска одновременно.
