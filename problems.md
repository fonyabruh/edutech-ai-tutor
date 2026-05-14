# Code Review — EduTech (Tbank-case)

Сверка с [TASKS.md](TASKS.md) и [prompts/01_scaffold_and_content.md](prompts/01_scaffold_and_content.md). Проблемы отсортированы по тяжести: **БЛОКЕР** валит демо, **ВЫСОКАЯ** ломает фичу или ТЗ, **СРЕДНЯЯ** требует фикса до сдачи, **НИЗКАЯ** косметика/долг.

Замечание: Claude Code прошёл сильно дальше этапов 0–1 — реализованы части этапов 2–7 (API auth/diagnostic/plan/lesson/chat, экраны онбординга, диагностики, плана, урока, чата). Проверял всё, что нашёл.

---

## БЛОКЕРЫ (демо не запустится / упадёт на показе)

### B1. PROMPTS_DIR указывает на корень проекта, но Dockerfile его не копирует
[backend/app/llm/prompts.py:6](backend/app/llm/prompts.py#L6) → `Path(__file__).parent.parent.parent.parent / "prompts"` резолвится в `<repo>/prompts/`. [backend/Dockerfile:10](backend/Dockerfile#L10) копирует только `app/`. В контейнере путь `/prompts/` не существует — **любой вызов LLM (диагностика, план, разбор ошибки, чат) упадёт с FileNotFoundError**. Локально на dev работает только потому что cwd совпадает с корнем.

**Фикс:** перенести YAML внутрь `backend/app/llm/prompts/` (как просил ТЗ Этап 0.4) и поправить `PROMPTS_DIR = Path(__file__).parent / "prompts"`. Либо в Dockerfile добавить `COPY ../prompts /prompts` (нарушит контекст билда — лучше первый вариант).

### B2. `useLocalSearchParams()` вызывается внутри onPress — нарушение Rules of Hooks
[mobile/app/plan/[subject].tsx:42](mobile/app/plan/%5Bsubject%5D.tsx#L42) — в обработчике клика «Начать» вызов `useLocalSearchParams().subject`. React-хуки запрещено вызывать в коллбэках; в dev это даст ошибку, в prod — undefined → роутер ведёт в `/lesson/undefined/<topicId>`.

**Фикс:** `subject` уже доступен в родительском `PlanScreen`, прокинуть через props в `DayCard`.

### B3. `asyncio.run()` внутри sync FastAPI-эндпоинтов
[backend/app/services/diagnostic.py:84](backend/app/services/diagnostic.py#L84) и [backend/app/services/plan.py:47](backend/app/services/plan.py#L47). FastAPI прогоняет sync-эндпоинты в threadpool, и в worker-потоке нет event loop — `asyncio.run` создаст новый, что часто работает, но:
- ломается логирование/контекст,
- не работает при отладке через uvicorn `--reload` под нагрузкой,
- может зависнуть, если внутри есть длинные SSE-стримы.

**Фикс:** сделать эндпоинты `async def` и `await llm.chat(...)`. Сам сервис тоже async.

### B4. Промпт диагностики просит LLM вернуть `topic_id`, но в user-message ID не передаются
[prompts/diagnose.yaml:14–20](prompts/diagnose.yaml#L14) — схема JSON содержит `"topic_id": int`, но в [backend/app/services/diagnostic.py:60–67](backend/app/services/diagnostic.py#L60) `answers_summary` и `mastery_summary` содержат только **названия** тем. LLM придумает ID или вернёт неконсистентные значения → фронт по этим ID ничего не найдёт.

**Фикс:** либо передавать `topic_id: <name>` явно в промпте, либо матчить ответ LLM назад по `name → id` на сервере и игнорировать ID из LLM.

### B5. `tutor_chat.yaml` шаблонит `{{ user_message }}`, но chat.py его не передаёт
[backend/app/api/chat.py:77–82](backend/app/api/chat.py#L77) передаёт только `subject_name` и `weak_topics`. В [prompts/tutor_chat.yaml:8](prompts/tutor_chat.yaml#L8) — `user: {{ user_message }}`. Jinja отрендерит пустую строку → в LLM уйдёт system + **пустое user-сообщение** + history. Это может ломать ответы и точно мусорит контекст.

**Фикс:** убрать user-секцию из YAML (оставить только system), либо передавать `user_message=body.message`. Учитывая, что history уже включает последнее сообщение пользователя в `chat.py`, проще удалить user-блок из YAML.

---

## ВЫСОКАЯ серьёзность

### H1. Хардкод `grade="9", exam="ОГЭ"` в LLM-промптах вместо данных пользователя
[backend/app/services/diagnostic.py:77](backend/app/services/diagnostic.py#L77) и [backend/app/services/plan.py:42](backend/app/services/plan.py#L42). Пользователь-11-классник для ЕГЭ получит план «по ОГЭ для 9 класса». В сервис не пробрасывается `User`.

**Фикс:** принимать `user: User` в `finalize_diagnostic` и `generate_plan`, использовать `user.grade`, `user.exam`, `user.goal`.

### H2. `except Exception: pass` глушит ошибки LLM
[backend/app/services/diagnostic.py:85–86](backend/app/services/diagnostic.py#L85) и [backend/app/services/plan.py:49–50](backend/app/services/plan.py#L49). Любой 4xx/5xx от YandexGPT (просрочен ключ, лимит, плохой JSON) → пустой `llm_data = {}` и тихий fallback. На демо если ключ кончится — диагностика «отработает» с дефолтным `estimated_score = avg_mastery × 32` и без комментариев. Никто не поймёт почему.

**Фикс:** ловить конкретные исключения (`httpx.HTTPStatusError`, `json.JSONDecodeError`), `print(f"\nLLM error: {e}")` (по CLAUDE.md можно). Не глотать `Exception` целиком.

### H3. Контент: задач по русскому/обществу в 2× меньше требуемого
- math: 48 задач (нужно 50, ~ОК)
- rus: **23 задачи** (нужно 50)
- soc: **22 задачи** (нужно 50)
- soc topics: 9 (нужно 10)

В rus есть темы с **1 задачей** (`rus.3.1`, `rus.3.2`). На уроке `_lesson/start` запросит 4 задачи по теме — выберет 1 и упадёт по `random.sample`? Нет: [backend/app/api/lesson.py:64](backend/app/api/lesson.py#L64) делает `random.sample(by_diff, min(4, len(by_diff)))` — выдаст 1 задачу, и через 1 ответ урок закончится. Демо по русскому будет смешным.

**Фикс:** заполнить хотя бы по 5 задач на тему для rus и soc. И/или дать спец-сообщение «Маловато задач по этой теме».

### H4. `subjects.json` весь exam="ОГЭ"
[content/subjects.json](content/subjects.json) — все три предмета помечены как ОГЭ, тогда как промпт 0.1 для математики просил ЕГЭ. Это влияет на UX (учеников 10–11 ведём в ЕГЭ-ветку, но предметы помечены ОГЭ). А в коде сейчас и `Subject.exam` нигде не используется на чтение — поле декоративное.

**Фикс:** либо снять поле как ненужное, либо завести по две записи на предмет (math_base_ege, math_base_oge) и фильтровать.

### H5. `Topic.codifier_code` `unique=True` глобально
[backend/app/models/topic.py:8](backend/app/models/topic.py#L8). Сейчас спасают префиксы `mat.`, `rus.`, `soc.`, но это хрупкая защита. Если методист случайно использует чистый `1.1` для разных предметов — упадёт INSERT.

**Фикс:** unique composite `(subject_code, codifier_code)`. Либо документально зафиксировать обязательный префикс.

### H6. `pick_diagnostic_tasks` не соответствует спеке (2 лёгких / 3 средних / 1 сложная)
[backend/app/services/diagnostic.py:19](backend/app/services/diagnostic.py#L19) — `[1, 1, 2, 2, 3, 3]` (2 easy / 2 medium / 2 hard). Спека просила 2 / 3 / 1. Минор, но смещает оценку.

### H7. Отсутствует `User.onboarding_completed`
Спека ТЗ Этап 1.1 явно требует поле `onboarding_completed: bool = False`. Сейчас [backend/app/models/user.py](backend/app/models/user.py) использует вычисляемую функцию `onboarding_completed(user)` через проверку `grade and exam and subjects != "[]"`. Работает, но мобила не получает `onboarding_completed` в `GET /me` ([backend/app/api/users.py:23](backend/app/api/users.py#L23) возвращает чистого User без флага). В результате [mobile/app/_layout.tsx:26](mobile/app/_layout.tsx#L26) сам реплицирует проверку — дублирование логики на сервере и клиенте.

**Фикс:** добавить поле в модель и обновлять при PATCH /me. Возвращать из всех auth-эндпоинтов.

### H8. Отсутствует модель `DiagnosticSession`
Спека Этап 1.1 требует `DiagnosticSession(id, user_id, subject_code, task_ids, current_index, finished)`. Сейчас сессия — просто `uuid.uuid4()` в памяти ([backend/app/api/diagnostic.py:52](backend/app/api/diagnostic.py#L52)), сервер не знает какие задачи были выбраны. Если клиент закроет приложение и зайдёт снова — данных нет. Спека также предусматривала «прерывание сохраняется в SQLite — можно вернуться».

**Фикс:** либо добавить модель (правильно), либо удалить упоминание о возобновлении из UX (быстро).

### H9. Lesson-сессии хранятся в in-memory dict
[backend/app/api/lesson.py:21](backend/app/api/lesson.py#L21) — `_sessions: dict[str, dict] = {}`. При рестарте контейнера (или просто перезапуске uvicorn `--reload`) данные теряются → `POST /lesson/finish` вернёт нули. На демо если бэк упадёт между ответом и финишем — пользователь не увидит summary с mastery_before/after.

**Фикс:** хранить `mastery_before` в Attempt либо отдельной таблице LessonSession. Минимум — fallback в /finish, который считает correct по последним N attempts с этим session_id.

### H10. SSE-эндпоинты используют sync Session внутри async-генератора
[backend/app/api/chat.py:91–105](backend/app/api/chat.py#L91) — `session` приходит как sync `Depends(get_session)`, который yieldит и закрывается по выходу из эндпоинта. Но `sse_stream` живёт дольше — после возврата StreamingResponse FastAPI закроет get_session, а внутри генератора `session.add(assistant_msg); session.commit()` будет работать с закрытым session.

**Фикс:** внутри async-генератора открыть `Session(engine)` вручную через `with Session(engine) as s: ...`. Не полагаться на DI.

### H11. Mobile: createMMKV (по факту OK, проверил v4 API)
**Сначала подозревал баг**, но v4.3.1 действительно экспортирует `createMMKV`. Изменений не нужно. Помечаю чтобы не возвращаться.

### H12. Mobile экран Topics — пустая заглушка
[mobile/app/(tabs)/topics.tsx](mobile/app/(tabs)/topics.tsx) — спека (TASKS этап 7.3) требовала Heatmap всех тем + список тем с кнопкой «Тренировать». Сейчас один Button «Начать диагностику» + Card с текстом «Пройди диагностику». Темы и mastery вообще не подгружаются.

**Фикс:** API уже есть (mastery считается). Запросить темы предмета (нужен новый эндпоинт `GET /subjects/{code}/topics` с mastery) → нарисовать сетку Heatmap-плиток.

### H13. Mobile: при тапе на предмет в дашборде всегда ведёт в диагностику
[mobile/app/(tabs)/index.tsx:24](mobile/app/(tabs)/index.tsx#L24) — `router.push(\`/diagnostic/${s.code}\`)` независимо от того, пройдена ли диагностика. После прохождения это будет «пройти ещё раз», что нелогично. Спека хотела «Сегодня в плане → Начать».

**Фикс:** если `s.last_session_at` есть → ведём в `/plan/${s.code}`, иначе в диагностику.

---

## СРЕДНЯЯ серьёзность

### M1. Expo SDK 54 вместо 52
[mobile/package.json:23](mobile/package.json#L23) → `"expo": "~54.0.33"`. Спека 0.3 явно говорила SDK 52. Сам по себе SDK 54 рабочий и даже свежее, но повышает риск несовместимости плагинов и неожиданных breaking changes (new arch + reanimated 4 + react-compiler). Конкретные риски:
- `react-native-math-view` ^3.9.5 не тестировался на RN 0.81 / new arch.
- `experiments.reactCompiler: true` ([mobile/app.json:46](mobile/app.json#L46)) — экспериментальный компилятор может ломать рендер хуков.

**Фикс на хакатоне:** оставить SDK 54 (даунгрейд дороже), но выключить `reactCompiler`.

### M2. Нет `mobile/.env.example`
Спека Этап 0.3 (п.10). Любой, кто склонит репо, не поймёт, какие переменные нужны клиенту (`EXPO_PUBLIC_API_URL`).

### M3. Нет `infra/deploy.sh`
Спека Этап 0.5 явно требовала. Сейчас в [infra/README.md](infra/README.md) написано «docker compose up -d» но нет rsync-скрипта на VM. Деплой делается руками.

### M4. `goal.tsx` использует `as any`
[mobile/app/(onboarding)/goal.tsx:28](mobile/app/(onboarding)/goal.tsx#L28). Проблема в типах: бэк ожидает `subjects: list[str]`, а в `Partial<User>` поле `subjects: string` (json-сериализованный). `as any` глушит ошибку, но указывает на расхождение между Mobile `User.subjects: string` и серверным запросом `subjects: list[str]`.

**Фикс:** завести отдельный `ProfilePatch` тип в lib/types.ts.

### M5. `datetime.utcnow()` deprecated в Python 3.12
[backend/app/api/auth.py:20](backend/app/api/auth.py#L20), [backend/app/models/user.py:14](backend/app/models/user.py#L14), [backend/app/models/attempt.py:14](backend/app/models/attempt.py#L14), [backend/app/models/mastery.py:12](backend/app/models/mastery.py#L12), [backend/app/models/diagnostic_result.py:14](backend/app/models/diagnostic_result.py#L14), [backend/app/models/learning_plan.py:11](backend/app/models/learning_plan.py#L11), [backend/app/models/chat_message.py:12](backend/app/models/chat_message.py#L12), [backend/app/services/mastery.py:19](backend/app/services/mastery.py#L19).

Будут DeprecationWarning при каждом инсерте.

**Фикс:** `from datetime import datetime, UTC; datetime.now(UTC)`.

### M6. `Mastery` нет unique composite индекса на (user_id, topic_id)
Спека требовала. Сейчас при гонке (две одновременные mutate-операции) можно создать дубликат. На хакатоне маловероятно, но `update_mastery` не использует upsert — `select → if not found insert`.

### M7. `LessonAnswer` возвращает `correct_answer` в теле
[backend/app/api/lesson.py:121](backend/app/api/lesson.py#L121). Спека: «НЕ возвращает разбор ошибки — клиент запросит стрим». Возврат правильного ответа технически не разбор, но всё равно лишний. Фронт его не использует ([mobile/app/lesson/.../[topicId].tsx:45](mobile/app/lesson/%5Bsubject%5D/%5BtopicId%5D.tsx#L45) сохраняет только `is_correct`).

**Фикс:** убрать поле из ответа.

### M8. `/diagnostic/finish` требует `subject_code` в body, хотя он определяется по `session_id`
[backend/app/api/diagnostic.py:30](backend/app/api/diagnostic.py#L30). Сейчас клиент должен помнить и передавать subject_code, хотя сервер мог бы взять его из attempts. Минор.

### M9. Mobile: spec ожидает `/diagnostic/picker` экран
Спека Этап 5.1. Сейчас выбор предмета совмещён с дашбордом и с табом Topics. Не критично, но логика «куда тыкать в первый раз» размазана.

### M10. `MarkdownView` крайне примитивен
[mobile/components/ui/MarkdownView.tsx](mobile/components/ui/MarkdownView.tsx) — поддерживает только `**bold**` и `$...$`. LLM в `explain_error` и `tutor_chat` будет генерить заголовки `**Где ошибка**`, списки `- шаг 1`, и блочные `$$...$$`. Заголовки отрендерятся как inline-bold внутри одной строки, списки — как plain text. На «wow-моменте» разбора ошибки текст будет невыразительным.

**Фикс:** заменить на `react-native-markdown-display` (хорошо работает, можно подключить плагин для math). Один из главных рычагов улучшения wow-фактора при минимальном труде.

### M11. Type mismatch: `DiagnosticResult.weak_topics`
В [mobile/lib/types.ts:43](mobile/lib/types.ts#L43) это `{topic_id, comment?}[]`, бэк отдаёт после `json.loads()` либо ID-объекты (fallback), либо что вернул LLM (см. B4). Если LLM вернул объекты без `topic_id` и с другими ключами — фронт упадёт на чтении `t.topic_id` ([mobile/app/diagnostic/results.tsx:53](mobile/app/diagnostic/results.tsx#L53)).

### M12. `lessonScreen` использует `summary: any`
[mobile/app/lesson/[subject]/[topicId].tsx:28](mobile/app/lesson/%5Bsubject%5D/%5BtopicId%5D.tsx#L28). Должно быть `LessonResult` из types.ts.

### M13. `PlanDay.status` — несогласованные значения
TASKS.md спека: `"available" | "locked" | "done"`. Mobile types.ts: `"available" | "complete" | "locked"`. Backend `/plan/day/.../complete` пишет `"complete"`. Бэк-фронт согласованы, но спека хотела `done`. Минор.

### M14. Spec `DiagnosticResult` потерял поля `priority_skills` и `overall_comment`
Бэк-модель хранит только `llm_summary`. Spec Этап 1.1 требовала отдельные `priority_skills` (json) и `overall_comment`. Сейчас priority_skills из LLM-ответа просто игнорируются.

---

## НИЗКАЯ серьёзность / стиль

### L1. `backend/main.py` — мусор после `uv init`
[backend/main.py](backend/main.py) — leftover hello-world. Удалить.

### L2. `presentation/` в `.gitignore`
[.gitignore:27](.gitignore#L27) — игнорится директория `presentation/`, которая существует в репо и не пуста. Если внутри есть слайды/демо — они не закоммитятся.

### L3. README указывает `cp .env.example .env` в mobile, но файла нет
[README.md:27](README.md#L27).

### L4. README говорит «YAML-контент» — на самом деле JSON
[README.md:10](README.md#L10).

### L5. `TaskMultiChoice key={opt}` — риск дублей
[mobile/components/task/TaskMultiChoice.tsx:25](mobile/components/task/TaskMultiChoice.tsx#L25). Если два варианта совпадают по тексту, React выдаст warning. Использовать `key={i}` или `key={`${i}-${opt}`}`.

### L6. `TaskNumeric.tsx` нет отдельным файлом
Спека Этап 5.3 требовала. Сейчас numeric — флаг внутри `TaskShortAnswer`. Поведенчески норм.

### L7. `chat/index.tsx`: `let idCounter = useRef(...)` странно
[mobile/app/chat/index.tsx:18](mobile/app/chat/index.tsx#L18). Работает, но `let` тут лишний и сбивает с толку.

### L8. Хардкод сабжект-кодов в Mobile
[mobile/app/(tabs)/index.tsx:6](mobile/app/(tabs)/index.tsx#L6), [topics.tsx:7](mobile/app/(tabs)/topics.tsx#L7), [(onboarding)/subjects.tsx:7](mobile/app/(onboarding)/subjects.tsx#L7) — три места дублируют коды math_base/rus/soc и человекочитаемые имена. При добавлении предмета забудешь обновить.

### L9. Импорты внутри функций
[backend/app/api/diagnostic.py:108](backend/app/api/diagnostic.py#L108) — `from app.models import DiagnosticResult` внутри роута. Не упадёт, но плохой стиль.

### L10. Imports внутри функции в seed
[backend/scripts/seed_content.py:5](backend/scripts/seed_content.py#L5) — `sys.path.insert(...)`. Если запускать через `python -m scripts.seed_content` из `backend/`, эта вставка не нужна. Сейчас [скрипт запускается через `python -m scripts.seed_content`] — стоит подтвердить и убрать sys.path-хак, либо завести `[tool.uv.scripts]` команду.

### L11. CLAUDE.md style: type hints
CLAUDE.md говорит «no type hints unless asked». В backend hints везде. Это **не нарушение**, потому что спека 0.4/1.1 явно типизировала сущности SQLModel и Pydantic — без hints оно не работает. Для services/* hints избыточны, можно снять.

### L12. `print("\nWARN:...")` в seed
[backend/scripts/seed_content.py:50](backend/scripts/seed_content.py#L50). CLAUDE.md: «минимум принтов, начинаем с \n». Соблюдено.

### L13. Mobile: `KeyboardAvoidingView` без keyboardVerticalOffset
[mobile/app/chat/index.tsx:42](mobile/app/chat/index.tsx#L42) — на iOS с header клавиатура перекроет инпут.

### L14. Mobile: `weak_topics.slice(0, 5)` без проверки типа
[mobile/app/diagnostic/results.tsx:51](mobile/app/diagnostic/results.tsx#L51). Если бэк вернёт не массив (см. B4/M11) — упадёт.

### L15. exam.tsx не пресетит значение из grade
[mobile/app/(onboarding)/exam.tsx](mobile/app/(onboarding)/exam.tsx). Спека: «auto-suggest по grade: 8-9 → ОГЭ, 10-11 → ЕГЭ». Сейчас экран всегда требует ручной выбор, хотя в grade-step мы уже выставили в стор. Можно `useState(exam)` — уже есть, но пользователь не понимает, что значение преселекчено (Chip визуально не подсветится сразу? — selected проверяется по value === selected, должно работать. Проверить руками).

### L16. CORS открыт `*` на проде
[backend/app/main.py:18](backend/app/main.py#L18). Для хакатона ок, но в TODO записать.

---

## Что НЕ проверял

- Реальный запуск `npx tsc --noEmit` (требует node_modules — есть, но не пробежал).
- Реальный запуск `uv run uvicorn app.main:app` (требует доустановки uv в этой среде).
- Соответствие задач ФИПИ по сути (математические тексты выглядят корректно, но 50+ задач проверять надо методисту).
- iOS-сборка через EAS.

---

## Приоритеты починки (если 1 вечер до демо)

1. **B1** — иначе LLM в продакшне не заведётся вообще.
2. **B2** — экран плана сломан.
3. **B5** + **B4** — без них диагностика и чат врут.
4. **H1** — критично для смысла демо («персональный план»).
5. **H3** — добавить хотя бы по 5 задач на тему rus/soc.
6. **H9** + **H10** — стабильность бэка под рестартом и SSE.
7. **M10** — поменять Markdown-рендер: бесплатно поднимает wow-фактор на демо.
8. Всё остальное — после.
