# connect-kafka/Dockerfile
FROM confluentinc/cp-kafka-connect:7.5.3

USER root

RUN confluent-hub install --no-prompt \
      confluentinc/kafka-connect-elasticsearch:11.1.0 \
  && confluent-hub install --no-prompt \
      mongodb/kafka-connect-mongodb:1.6.0 \
  && confluent-hub install --no-prompt \
      jcustenborder/kafka-connect-redis:0.0.8 \
  && confluent-hub install --no-prompt \
      neo4j/kafka-connect-neo4j:5.1.12

