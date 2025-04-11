FROM redis:7.0

# Создаем директорию для логов и устанавливаем права
RUN mkdir -p /var/log/redis && \
    chown redis:redis /var/log/redis

# Копируем скрипт инициализации
COPY init-redis.sh /docker-entrypoint-initdb.d/

# Делаем скрипт исполняемым
RUN chmod +x /docker-entrypoint-initdb.d/init-redis.sh
