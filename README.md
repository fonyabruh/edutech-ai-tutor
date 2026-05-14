# EduTech — AI-ассистент подготовки к ОГЭ/ЕГЭ

Персональный AI-репетитор: диагностика пробелов, адаптивный план, разбор ошибок, чат с тьютором.

## Структура

```
backend/    FastAPI + SQLModel + SQLite + YandexGPT
mobile/     Expo 52 (React Native, TypeScript)
content/    JSON-контент задач и тем
infra/      Docker Compose + Caddy
prompts/    LLM-промпты
```

## Быстрый старт

**Backend:**
```bash
cd backend
cp .env.example .env  # заполни YANDEX_API_KEY и YANDEX_FOLDER_ID
uv run uvicorn app.main:app --reload
```

**Mobile:**
```bash
cd mobile
cp .env.example .env
npx expo start
```

**Деплой:**
```bash
cd infra
cp .env.example .env
docker compose up -d
```

**EAS Build (APK для Android):**
```bash
cd mobile
eas build --profile preview --platform android
# Сканируй QR из вывода команды → установи APK → открой приложение
```

## Демо-сценарий для жюри (3 минуты)

1. **Онбординг** — выбери класс 11, ЕГЭ, предмет «Математика», цель «Высокий балл»
2. **Диагностика** — реши 6 задач, тапни «Далее» → экран AI-анализа (3 сек) → результаты
3. **Результаты** — оценка уровня, карта тем, пробелы → «Покажи мой план»
4. **План** — 14 дней, тапни «Начать» на Дне 1
5. **Урок** — прочитай теорию → реши 4 задачи → ошибка → AI разбирает её в реальном времени
6. **Итоги урока** — анимированный прогресс mastery, XP → «На главную»
7. **Дашборд** — streak, карточка «Сегодня в плане», прогноз балла

**Запасной аккаунт (если нет сети):**
```bash
cd backend
uv run python -m scripts.seed_demo_user
```
На экране приветствия нажми «Войти как демо» (видна в dev-сборке).
