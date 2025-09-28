# Microservices & CDC Data Platform

## Описание

Платформа демонстрирует потоковую синхронизацию данных из PostgreSQL в различные хранилища и микросервисы. Источник изменений — Debezium (Kafka Connect). Данные транслируются в Elasticsearch, MongoDB, Neo4j и Redis. Дополнительно работают два собственных CDC‑консюмера: один формирует иерархические коллекции в MongoDB, другой — граф связей в Neo4j. Три FastAPI‑сервиса (app_1, app_2, app_3) доступны через API‑шлюз.

Состав:

* **PostgreSQL** — первичная БД.
* **Kafka + Kafka Connect (Debezium)** — шина и коннектор изменений из PostgreSQL.
* **Sinks** — Elasticsearch, MongoDB, Neo4j, Redis.
* **CDC‑консумеры** — Python‑сервисы для MongoDB и Neo4j.
* **Микросервисы** — `app_1`, `app_2`, `app_3` (FastAPI) за **API Gateway**.
* **Скрипты** — регистрация коннекторов, генерация демонстрационных данных.

Базовые порты по умолчанию:

* Kafka Connect: `8083`
* PostgreSQL: `5432`
* Elasticsearch: `9200`
* MongoDB: `27017`
* Neo4j: `7474` (HTTP), `7687` (Bolt)
* Redis: `6379`
* API Gateway и приложения: см. `docker-compose.yaml` (по умолчанию localhost с явным маппингом портов)

---

## Требования

* ОС с Docker Desktop (Windows/macOS/Linux)
* Docker Engine 24+ и Docker Compose v2
* Python 3.11+ (для генераторов данных и/или CDC‑скриптов)
* Git, curl (или PowerShell `Invoke-RestMethod`) для локальных проверок
* Рекомендуемые ресурсы: ≥ 4 CPU, ≥ 8–12 GB RAM

---

## Установка

1. **Клонирование репозитория**

   ```bash
   git clone <repo-url>
   cd <repo>
   ```

2. **Проверьте переменные окружения**
   В файлах `docker-compose.yaml` и конфигурации коннекторов должны быть согласованы:

   * адрес брокера Kafka (обычно `kafka:9092` внутри сети docker);
   * URL’ы целевых хранилищ: Elasticsearch, MongoDB, Neo4j, Redis;
   * параметры подключения к PostgreSQL;
   * префиксы топиков Debezium и списки таблиц.

3. **Поднимите инфраструктуру**

   ```bash
   docker compose up -d zookeeper kafka postgres redis mongodb neo4j elasticsearch
   ```

4. **Запустите Kafka Connect**

   ```bash
   docker compose up -d kafka-connect
   ```

   Убедитесь, что в сервисе задан `CONNECT_PLUGIN_PATH` и смонтирован каталог коннекторов (`./connectors -> /connectors`).

5. **Зарегистрируйте коннекторы**
   В проекте есть скрипт авто‑регистрации всех `*.json`.

   ```bash
   docker compose exec kafka-connect bash -lc '/connectors/register-connectors.sh'
   ```

6. **(Опционально) Сгенерируйте демонстрационные данные**

   ```bash
   python generate_data_for_db.py
   ```

7. **Запустите CDC‑сервисы и приложения**

   ```bash
   docker compose up -d mongo-cdc neo4j-cdc app_1 app_2 app_3 app_gateway
   ```

---

## Использование

### Быстрая проверка коннекторов

```bash
# список коннекторов
curl -s http://localhost:8083/connectors | jq

# статус конкретного коннектора
curl -s http://localhost:8083/connectors/redis-sink-students/status | jq
```

### Проверка потоков данных

* **Elasticsearch** — индексы:

  ```bash
  curl -s http://localhost:9200/_cat/indices?v
  ```
* **MongoDB** — коллекции:

  ```bash
  mongosh --host localhost --eval "db.getSiblingDB('university').getCollectionNames()"
  ```
* **Neo4j** — откройте Neo4j Browser (`http://localhost:7474`), выполните `MATCH (n) RETURN count(n);`.
* **Redis** — ключи:

  ```bash
  redis-cli -h localhost KEYS '*'
  ```

### Доступ к API

* API‑шлюз и сервисы — FastAPI со Swagger‑UI по пути `/docs`.
* Пример чтения часов по группе (app_3):

  ```bash
  curl -s http://localhost:<gateway_port>/api/group-hours/<group_id>
  ```

  Если включена авторизация, укажите заголовок `Authorization: Bearer <JWT>`.

### Грубый цикл разработки

```bash
# перезапуск конкретного сервиса
docker compose up -d --build app_gateway

# логи
docker compose logs -f kafka-connect
```

---

## Примечания

* Конфигурации коннекторов (`connectors/*.json`) задают источники/приёмники и SMT‑обработку; меняйте под свои схемы.
* Инициализация сервисов может занимать время (особенно Elasticsearch и Neo4j).
* Для Windows рекомендуется запускать команды в PowerShell либо WSL.
