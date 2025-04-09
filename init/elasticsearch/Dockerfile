# Используем официальный образ Elasticsearch
FROM elasticsearch:7.17.10

# Копируем скрипт инициализации
COPY init-es.sh /docker-entrypoint-initdb.d/

# Делаем скрипт исполняемым
RUN chmod +x /docker-entrypoint-initdb.d/init-es.sh
