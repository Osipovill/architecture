#!/bin/sh
# init-redis.sh
# Инициализация кэша посещаемости в Redis

# Пример: установка процентного показателя посещаемости для студентов
redis-cli SET attendance:1 100
redis-cli SET attendance:2 75
redis-cli SET attendance:3 90
redis-cli SET attendance:4 60

echo "Инициализация Redis завершена."
