# Yandex Music Telegram Bot

![Screen](screenshot.png)

Telegram бот для скачивания музыки из Яндекс.Музыки.

## Возможности

- Поиск треков по названию
- Скачивание треков по ссылке из Яндекс.Музыки
- Поддержка ограничения доступа по Telegram ID
- Демо режим для неавторизованных пользователей (30-секундные превью)
- Название/исполнитель/обложка прошиваются прямо в mp3 (через `mutagen`), а не только передаются параметрами Telegram
- Кеш отправленных треков (`file_id`) — повторная отправка того же трека мгновенная, без повторного скачивания с Яндекса

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/sboychenko/yandex-music-bot.git
cd yandex-music-bot
```

2. Создайте виртуальное окружение и установите зависимости:
```bash
python -m venv .venv
source .venv/bin/activate  # для Linux/Mac
# или
.venv\Scripts\activate  # для Windows
pip install -r requirements.txt
```

3. Создайте файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
```
Обязательные переменные — `TELEGRAM_BOT_TOKEN` и `YANDEX_MUSIC_TOKEN`. `ALLOWED_USERS` (через запятую) и `ADMIN_ID` —
опционально: без `ALLOWED_USERS` доступ открыт всем, без `ADMIN_ID` уведомления о запуске/новых пользователях просто
не отправляются. `CACHE_FILE_PATH` — путь к файлу кеша (по умолчанию `data/cache.json`).

## Запуск

```bash
python bot.py
```

## Требования

- Python 3.9+ (в Docker-образе — 3.11)
- Точные версии зависимостей — в [requirements.txt](requirements.txt): `python-telegram-bot`, `yandex-music`,
  `python-dotenv`, `mutagen`

## CI/CD

При пуше в `main` GitHub Actions ([.github/workflows/deploy.yml](.github/workflows/deploy.yml)) собирает Docker-образ,
пушит его в GitHub Container Registry и разворачивает на VPS по SSH. В pull request'ах и других ветках выполняется
только проверка сборки, без публикации и деплоя.

Для автодеплоя нужно один раз добавить в **Settings → Secrets and variables → Actions** секреты:

- `REMOTE_HOST` — адрес VPS
- `REMOTE_USER` — пользователь для SSH
- `REMOTE_KEY` — приватный SSH-ключ (содержимое файла, не путь)

На сервере в `~/yandex-music-bot/.env` должен лежать файл с `TELEGRAM_BOT_TOKEN`, `YANDEX_MUSIC_TOKEN` и остальными
переменными — workflow его не создаёт и не перезаписывает, только запускает контейнер с `--env-file`. Кеш треков
монтируется из `~/yandex-music-bot/data` и переживает передеплой.

Ручной деплой через `deploy.sh` (см. [deploy.md](deploy.md)) продолжает работать и может использоваться как запасной
вариант.

## Лицензия

MIT

## Получение токена yandex music
https://github.com/MarshalX/yandex-music-api/discussions/513#discussioncomment-2729781
