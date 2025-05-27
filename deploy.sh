#!/bin/bash
# Загрузка переменных окружения
source .env

# Конфигурация
IMAGE_NAME="yandex-music-bot"
CONTAINER_NAME="yandex-music-bot"
REMOTE_DIR="~/yandex-music-bot"

# Проверка наличия необходимых переменных
if [ -z "$REMOTE_HOST" ] || [ -z "$REMOTE_USER" ] || [ -z "$REMOTE_KEY" ]; then
    echo "Error: Missing required environment variables"
    echo "Please check your .env file and ensure REMOTE_HOST, REMOTE_USER and REMOTE_KEY are set"
    exit 1
fi

# Сборка образа
echo "Building Docker image..."
docker build -t $IMAGE_NAME .

# Сохранение образа в tar архив
echo "Saving Docker image..."
docker save $IMAGE_NAME | gzip > $IMAGE_NAME.tar.gz

# Показать размер файла
echo "Archive size:"
ls -lh $IMAGE_NAME.tar.gz

# Отправка архива на сервер
echo "Uploading to server..."
scp -i $REMOTE_KEY $IMAGE_NAME.tar.gz $REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/

# Выполнение команд на сервере
echo "Deploying on server..."
ssh -i $REMOTE_KEY $REMOTE_USER@$REMOTE_HOST << EOF
    cd $REMOTE_DIR
    
    # Остановка и удаление старого контейнера
    docker stop $CONTAINER_NAME || true
    docker rm $CONTAINER_NAME || true
    
    # Загрузка нового образа
    docker load < $IMAGE_NAME.tar.gz
    
    # Запуск нового контейнера
    docker run -d \
        --name $CONTAINER_NAME \
        --restart unless-stopped \
        --env-file .env \
        $IMAGE_NAME
    # проверка запущен ли контейнер
    docker ps -a | grep $CONTAINER_NAME
EOF

# Очистка локальных файлов
echo "Cleaning up..."
rm $IMAGE_NAME.tar.gz

echo "Deployment completed!" 