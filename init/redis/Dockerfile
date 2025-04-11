FROM redis:7.0

ENV LANG=C.UTF-8

# Создаем директорию для логов и даем права
RUN mkdir -p /var/log/redis && chown redis:redis /var/log/redis

# Копируем наш init-скрипт
COPY init-redis.sh /usr/local/bin/init-redis.sh
RUN chmod +x /usr/local/bin/init-redis.sh


CMD ["redis-server", "--loglevel", "warning", "--logfile", "/var/log/redis/redis.log", "--save", "60", "1", "--appendonly", "yes"]
