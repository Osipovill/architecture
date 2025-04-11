#!/bin/sh
# Очистка Redis
redis-cli FLUSHALL

# Вставка 10 записей студентов в кэш Redis
redis-cli SET student:1 "{\"student_id\":1, \"full_name\": \"Мартынова Лия\", \"code\": \"Ст-2022-001\", \"group_id\": 1}"
redis-cli SET student:2 "{\"student_id\":2, \"full_name\": \"Осипов Илья\", \"code\": \"Ст-2022-002\", \"group_id\": 1}"
redis-cli SET student:3 "{\"student_id\":3, \"full_name\": \"Ершов Александр\", \"code\": \"Ст-2022-003\", \"group_id\": 1}"
redis-cli SET student:4 "{\"student_id\":4, \"full_name\": \"Иванов Сергей\", \"code\": \"Ст-2022-004\", \"group_id\": 2}"
redis-cli SET student:5 "{\"student_id\":5, \"full_name\": \"Петрова Анна\", \"code\": \"Ст-2022-005\", \"group_id\": 2}"
redis-cli SET student:6 "{\"student_id\":6, \"full_name\": \"Сидоров Максим\", \"code\": \"Ст-2022-006\", \"group_id\": 3}"
redis-cli SET student:7 "{\"student_id\":7, \"full_name\": \"Кузнецова Ольга\", \"code\": \"Ст-2022-007\", \"group_id\": 3}"
redis-cli SET student:8 "{\"student_id\":8, \"full_name\": \"Новиков Роман\", \"code\": \"Ст-2022-008\", \"group_id\": 4}"
redis-cli SET student:9 "{\"student_id\":9, \"full_name\": \"Фролова Светлана\", \"code\": \"Ст-2022-009\", \"group_id\": 5}"
redis-cli SET student:10 "{\"student_id\":10, \"full_name\": \"Смирнова Елена\", \"code\": \"Ст-2022-010\", \"group_id\": 6}"


echo "Инициализация Redis завершена."
