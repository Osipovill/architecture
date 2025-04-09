# Используем официальный образ Redis
FROM redis:7.0

# Копируем скрипт инициализации (если он нужен)
COPY init-redis.sh /docker-entrypoint-initdb.d/

# Делаем скрипт исполняемым
RUN chmod +x /docker-entrypoint-initdb.d/init-redis.sh
