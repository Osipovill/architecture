import asyncio
import json
import logging
from aiokafka import AIOKafkaConsumer
from motor.motor_asyncio import AsyncIOMotorClient

# Логгер
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cdc_hierarchy")

# Буфер для событий department, если institute ещё не создан
pending_depts: dict[int, list[dict]] = {}

# Настройки Kafka
KAFKA_BOOTSTRAP = "kafka:29092"
KAFKA_GROUP_ID = "university_hierarchy_group"
KAFKA_TOPICS = [
    "university_db.public.universities",
    "university_db.public.institutes",
    "university_db.public.departments"
]

# Настройки MongoDB
MONGO_URI = "mongodb://admin:P%40ssw0rd@mongodb:27017"
MONGO_DB = "university"
MONGO_COLL = "universities"

async def handle_university(coll, after):
    await coll.update_one(
        {"university_id": after["university_id"]},
        {
            "$set": {"name": after["name"]},
            "$setOnInsert": {"institutes": []}
        },
        upsert=True
    )
    logger.info(f"Upserted university {after['university_id']}")

async def handle_institute(coll, after):
    uid = after["university_id"]
    iid = after["institute_id"]
    # Обновляем имя, если институт уже есть
    res = await coll.update_one(
        {"university_id": uid, "institutes.institute_id": iid},
        {"$set": {"institutes.$.name": after["name"]}}
    )
    # Если не было — вставляем новый институт с пустым списком кафедр
    if res.matched_count == 0:
        await coll.update_one(
            {"university_id": uid},
            {"$push": {"institutes": {
                "institute_id": iid,
                "name": after["name"],
                "departments": []
            }}}
        )
    logger.info(f"Upserted institute {iid} for university {uid}")

    # Если до этого приходили события department для этого iid — применяем их
    if iid in pending_depts:
        for dept_after in pending_depts.pop(iid):
            await handle_department(coll, dept_after)

async def handle_department(coll, after):
    did = after["dept_id"]
    iid = after["institute_id"]
    # Пытаемся обновить существующую кафедру
    res = await coll.update_one(
        {"institutes.institute_id": iid, "institutes.departments.department_id": did},
        {"$set": {
            "institutes.$[inst].departments.$[dept].name": after["name"],
            "institutes.$[inst].departments.$[dept].head": after["head"],
            "institutes.$[inst].departments.$[dept].phone": after["phone"]
        }},
        array_filters=[{"inst.institute_id": iid}, {"dept.department_id": did}]
    )
    if res.matched_count == 1:
        logger.info(f"Upserted department {did} under institute {iid}")
        return

    # Если сам institute уже есть, но кафедра новая — пушим в массив
    inst_exists = await coll.count_documents(
        {"institutes.institute_id": iid}, limit=1
    )
    if inst_exists:
        await coll.update_one(
            {"institutes.institute_id": iid},
            {"$push": {"institutes.$.departments": {
                "department_id": did,
                "name": after["name"],
                "head": after["head"],
                "phone": after["phone"]
            }}}
        )
        logger.info(f"Upserted new department {did} under institute {iid}")
    else:
        # Если institute ещё не появился — буферизуем событие
        pending_depts.setdefault(iid, []).append(after)
        logger.info(f"Buffered department {did} for institute {iid}")

async def consume():
    client = AsyncIOMotorClient(MONGO_URI)
    coll = client[MONGO_DB][MONGO_COLL]
    await coll.delete_many({})
    logger.info("Cleared existing universities collection")

    consumer = AIOKafkaConsumer(
        *KAFKA_TOPICS,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id=KAFKA_GROUP_ID,
        auto_offset_reset='earliest',
        enable_auto_commit=False,
        value_deserializer=lambda v: json.loads(v.decode())
    )

    await consumer.start()
    try:
        async for msg in consumer:
            after = msg.value.get("after")
            if not after:
                continue
            table = msg.topic.split('.')[-1]
            if table == "universities":
                await handle_university(coll, after)
            elif table == "institutes":
                await handle_institute(coll, after)
            elif table == "departments":
                await handle_department(coll, after)
    finally:
        await consumer.stop()
        client.close()

if __name__ == "__main__":
    asyncio.run(consume())
