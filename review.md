# Code Review — EduTech (Tbank-case)

Повторное ревью после исправления `problems.md` и написания тестов. Проверка: соответствие `TASKS.md`, регрессии из `problems.md`, новые проблемы, прогон тестов.

**Вердикт: проект в хорошей форме, демо-готов.** Все блокеры и высокоприоритетные баги из прошлого ревью закрыты, тесты зелёные, верификация проходит. Осталось несколько средних/низких проблем — ни одна не валит демо.

---

## Верификация (прогнано)

| Проверка | Результат |
|---|---|
| `uv run pytest --cov=app --cov-branch` | **115 passed**, coverage **99%** (TOTAL 667 stmts, 2 miss) |
| `uv run ruff check .` | All checks passed |
| `uv run python -c "import app.main"` | import ok |
| `uv run python -m scripts.seed_content` | math 48 / rus 45 / soc 50 задач — отрабатывает |
| `npx tsc --noEmit` (mobile) | exit 0, без ошибок типов |

Покрытие по модулям: `api/*` и `services/*` — 100%, `llm/client.py` — 100%, `llm/prompts.py` — 100%. Не покрыт только `db.py` (75%, две строки `get_session`/engine — ожидаемо).

---

## Регрессии из problems.md — статус

Все блокеры и H-проблемы прошлого ревью проверены в коде:

| ID | Что было | Статус |
|---|---|---|
| B1 | PROMPTS_DIR вне Docker-контекста | **Исправлено** — `Path(__file__).parent / "prompts"`, YAML в `backend/app/llm/prompts/` |
| B2 | `useLocalSearchParams()` в onPress | **Исправлено** — `subject` прокинут пропом в `DayCard` |
| B3 | `asyncio.run()` в sync-хендлерах | **Исправлено** — `finalize_diagnostic` и `generate_plan` стали `async`, эндпоинты `await`-ят |
| B4 | LLM возвращает несуществующие topic_id | **Исправлено** — ID передаются в промпт + `filter_topics` валидирует против реальных ID |
| B5 | `tutor_chat.yaml` с пустым `{{ user_message }}` | **Исправлено** — user-секция убрана, история включает последнее сообщение |
| H1 | Хардкод `grade="9"` | **Исправлено** — `user.grade/exam/goal` пробрасываются, есть тест `test_finalize_diagnostic_uses_user_grade_exam` |
| H2 | `except Exception: pass` | **Исправлено** — ловятся `HTTPStatusError/ConnectError/JSONDecodeError`, есть `print`, есть fallback-тесты |
| H7 | Нет `onboarding_completed` в ответах | **Исправлено** — `_user_response()` и `/auth/anonymous` возвращают флаг |
| H10 | SSE с закрытым sync Session | **Исправлено** — `chat.py` открывает свежий `with Session(engine)` внутри генератора |
| H12 | Topics — пустая заглушка | **Исправлено** — есть карта тем, список с mastery и кнопкой «Тренировать», эндпоинт `GET /subjects/{code}/topics` |
| H13 | Дашборд всегда вёл в диагностику | **Исправлено** — навигация по `last_session_at` (план / диагностика) |
| M5 | `datetime.utcnow()` deprecated | **Исправлено** — `grep utcnow` по `backend/app` пусто |
| M7 | `/lesson/answer` отдавал `correct_answer` | **Исправлено** — возвращается только `is_correct` |

---

## Новые / оставшиеся проблемы

### ВЫСОКАЯ

#### N1. MarkdownView: `<MathView>` вложен в `<Text>` — невалидный для RN
[mobile/components/ui/MarkdownView.tsx:10-32](mobile/components/ui/MarkdownView.tsx#L10) — `InlineText` возвращает `<Text>`, внутри которого для inline-формул `$...$` рендерится `<MathView>`. `MathView` — это View-компонент (SVG), а React Native **не поддерживает вложение View внутрь Text**: на iOS бросит «Nesting of <View> within <Text> is not supported», на Android сломает лейаут. Блочные `$$...$$` (на верхнем уровне строки, line 65) — ок, проблема только в inline.

Это важно: `explain_error` и теория тем активно используют inline `$...$`. На «wow-моменте» разбора ошибки формулы внутри текста сломаются.

**Фикс:** не оборачивать сегменты в один `<Text>`. Рендерить строку как `<View flex-row flex-wrap>` с чередованием `<Text>` и `<MathView>`, либо вынести inline-математику в отдельные элементы вне `<Text>`.

#### N2. Компонент `Heatmap` создан, но не используется нигде
[mobile/components/ui/Heatmap.tsx](mobile/components/ui/Heatmap.tsx) существует и экспортирован, но:
- [results.tsx](mobile/app/diagnostic/results.tsx) рендерит пробелы как Card со строкой `Тема #{t.topic_id}` — **показывает пользователю сырой числовой ID** вместо названия темы и без карты.
- [topics.tsx:67-74](mobile/app/(tabs)/topics.tsx#L67) рисует свою инлайновую сетку плиток, не используя `Heatmap`.

TASKS.md этап 6.1 явно требовал Heatmap-карту тем на экране результатов. Сейчас её там нет, а готовый компонент — мёртвый код.

**Фикс:** использовать `Heatmap` в results.tsx и topics.tsx. Для results нужно, чтобы бэк отдавал название темы вместе с `topic_id` (сейчас `/diagnostic/finish` и `/result/{code}` возвращают только ID — фронт не может показать имя).

### СРЕДНЯЯ

#### N3. `useLLMStream` без таймаута на первый чанк
[mobile/hooks/useLLMStream.ts](mobile/hooks/useLLMStream.ts) — промпт финализации (этап 3.4) требовал: если первый чанк SSE не пришёл за 10 секунд — таймаут и ErrorState. Не реализовано. Если YandexGPT висит — пользователь будет смотреть на «Разбираю твою ошибку…» бесконечно.

#### N4. Нет моделей `DiagnosticSession` / `LessonSession`
Промпт исправлений просил завести обе модели. Вместо этого:
- Lesson — in-memory `_sessions: dict` ([lesson.py:21](backend/app/api/lesson.py#L21)) + fallback в `/finish`, считающий по `Attempt`. Работает, но `_sessions` — модульный глобал: при нескольких uvicorn-воркерах сломается, при рестарте теряется (спасает fallback).
- Diagnostic — `session_id` вообще не персистится, `task_ids` нигде не хранятся. Функционально ок (`/answer` пишет `Attempt`, `/finish` читает по `session_id`), но «возобновление прерванной диагностики» из TASKS.md невозможно.

Для хакатона приемлемо (один контейнер, один воркер), но это технический долг — зафиксировать.

#### N5. results.tsx показывает `Тема #{topic_id}` вместо названия
См. N2 — выделяю отдельно как UX-проблему демо: жюри увидит «Тема #3» вместо «Квадратные уравнения».

### НИЗКАЯ

- **N6.** [lesson/[subject]/[topicId].tsx:101](mobile/app/lesson/%5Bsubject%5D/%5BtopicId%5D.tsx#L101) — `currentTask` рендерится без guard по стадии: на стадиях `feedback` и `explanation` старая задача всё ещё видна и интерактивна над карточкой разбора. Обернуть в `(stage === "task" || stage === "feedback")` или прятать на `explanation`.
- **N7.** [lesson/[subject]/[topicId].tsx:26](mobile/app/lesson/%5Bsubject%5D/%5BtopicId%5D.tsx#L26) — стейт `lastAnswer` устанавливается, но нигде не читается. Мёртвая переменная.
- **N8.** Устаревшие копии YAML в корневом `prompts/` (`diagnose.yaml`, `plan.yaml`, `explain_error.yaml`, `tutor_chat.yaml`) — канонические теперь в `backend/app/llm/prompts/`. Мёртвые файлы, удалить (CLAUDE.md про них уже предупреждает).
- **N9.** [infra/deploy.sh](infra/deploy.sh) — `echo "\ndeploy done"`: без `echo -e` последовательность `\n` выведется буквально.
- **N10.** [dashboard index.tsx:96](mobile/app/(tabs)/index.tsx#L96) — `router.push("/chat/index")`, корректнее `/chat`. Работает, т.к. файл `chat/index.tsx` существует.
- **N11.** `patch_me` возвращает `_user_response` без поля `streak`, а `get_me` — со `streak`. Лёгкая несогласованность формы ответа одного и того же ресурса.
- **N12.** `analyzing.tsx` использует символ `✓` — CLAUDE.md запрещает не-ASCII символы (правило для кода/принтов; тут UI-контент, формально на грани).

---

## Соответствие TASKS.md

Реализованы этапы 0–7 практически полностью. Что отклоняется от спеки:

- **Этап 1.1** — нет моделей `DiagnosticSession` / `LessonSession` (см. N4). `DiagnosticResult` дополнен `priority_skills` — соответствует.
- **Этап 6.1** — Heatmap на результатах диагностики не подключён (см. N2).
- **Этап 8.1** — `useLLMStream` без 10-сек таймаута (см. N3). `ErrorState`/`EmptyState`/`LoadingState` созданы и частично используются.
- **Этап 8.3–8.5** — `eas.json`, `infra/deploy.sh`, `seed_demo_user.py` на месте; EAS Build и реальный деплой требуют ручного прогона (ожидаемо).

Остальное (онбординг, диагностика, план, урок, чат, SSE-стриминг, mastery-логика, контент) — соответствует TASKS.md.

---

## Оценка тестового набора

**Качество высокое.** 115 тестов, 99% branch coverage, прогон 1.7s.

Сильные стороны:
- Чистый AAA, говорящие имена (`test_finalize_diagnostic_uses_real_topic_ids`).
- `FakeLLM`-фикстура с настройкой на успех / исключение / стрим — ни одного реального вызова YandexGPT.
- In-memory SQLite (`StaticPool`) с изоляцией per-test, override `get_session`.
- `clear_lesson_sessions` (autouse) корректно чистит модульный глобал `_sessions` между тестами.
- Детерминированная фикстура `seeded` с темой на 1 задачу — целенаправленно покрывает edge-case H3.
- Регрессы из problems.md покрыты явными тестами: B4, H1, H2, H6.

Замечания:
- Тесты только бэкенда. Мобильная часть не покрыта (jest не настроен) — для хакатона приемлемо, вся логика на бэке.
- `test_pick_tasks_difficulty_distribution` проверяет лишь «каждая сложность встречается за 50 прогонов», а не само распределение `[1,1,2,2,2,3]` — слабая проверка, но не критично.

---

## Рекомендация

Проект **готов к демо**. Перед показом стоит закрыть две вещи, влияющие на «wow»:

1. **N1** — inline-LaTeX в MarkdownView (формулы в разборе ошибки сломаются на устройстве — а это ключевой экран демо).
2. **N2 / N5** — подключить Heatmap на результатах диагностики и показывать названия тем вместо `Тема #3`.

**N3** (таймаут SSE) — желательно, чтобы зависший YandexGPT не вешал экран. Остальное (N4, N6–N12) — технический долг, можно после хакатона.
