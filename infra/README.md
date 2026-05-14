# Деплой

Одна VM в Yandex Cloud, Docker Compose + Caddy (TLS автоматически).

## Быстрый старт

```bash
cp .env.example .env
# заполни JWT_SECRET, YANDEX_API_KEY, YANDEX_FOLDER_ID, DOMAIN
mkdir -p data
docker compose up -d
```

Caddy автоматически получит TLS-сертификат для `DOMAIN`.
