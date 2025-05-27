Я помогу вам создать Dockerfile для сборки образа и подготовить инструкции по запуску на VPS с Ubuntu.

Вот инструкции по сборке и запуску на VPS:

1. На вашем локальном компьютере:
```bash
# Собрать образ
docker build -t yandex-music-bot .

# Сохранить образ в файл
docker save yandex-music-bot > yandex-music-bot.tar
```

2. Перенесите файлы на VPS:
```bash
# Перенести образ
scp yandex-music-bot.tar user@your-vps-ip:~/

# Перенести .env файл
scp .env user@your-vps-ip:~/
```

3. На VPS:
```bash
# Установить Docker если еще не установлен
sudo apt update
sudo apt install docker.io

# Загрузить образ
docker load < yandex-music-bot.tar

# Создать директорию для бота
mkdir -p ~/yandex-music-bot
cd ~/yandex-music-bot

# Скопировать .env файл
cp ~/.env .

# Запустить контейнер
docker run -d \
  --name yandex-music-bot \
  --restart unless-stopped \
  -v $(pwd)/.env:/app/.env \
  yandex-music-bot
```

4. Полезные команды для управления ботом:
```bash
# Посмотреть логи
docker logs yandex-music-bot

# Посмотреть логи в реальном времени
docker logs -f yandex-music-bot

# Остановить бота
docker stop yandex-music-bot

# Запустить бота
docker start yandex-music-bot

# Перезапустить бота
docker restart yandex-music-bot
```

Особенности этой конфигурации:
1. Используется легковесный образ python:3.11-slim
2. Установлены только необходимые системные зависимости
3. Контейнер настроен на автоматический перезапуск при сбоях
4. .env файл монтируется как volume, что позволяет менять настройки без пересборки образа
5. Все временные файлы и кэш исключены из образа

Хотите, чтобы я добавил что-то еще или объяснил какую-то часть подробнее?



====
```bash
UquG*5fXyT4q

scp yandex-music-bot.tar root@5.35.91.202:~/
scp .env root@5.35.91.202:~/
ssh root@5.35.91.202
```