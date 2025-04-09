#!/bin/bash
# Запускаем elasticsearch стандартным скриптом (в фоне)
# (используем оригинальный entrypoint для старта ES)
/usr/local/bin/docker-entrypoint.sh eswrapper &
# Ждем, пока ES станет доступен
sleep 30
# Создаем индекс с нужным маппингом
curl -X PUT "localhost:9200/courses?pretty" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "properties": {
      "course_id": { "type": "keyword" },
      "название": { "type": "text" },
      "описание": { "type": "text" },
      "модули": {
        "type": "nested",
        "properties": {
          "module_id": { "type": "keyword" },
          "тема": { "type": "text" },
          "лекции": { "type": "text" },
          "практические": { "type": "text" }
        }
      }
    }
  }
}
'
# Делаем простой запрос для подтверждения работы, можно использовать tail -f логов, чтобы контейнер не завершился
tail -f /usr/share/elasticsearch/logs/elasticsearch.log
