import asyncio
import json
import logging

from aiokafka import AIOKafkaConsumer
from motor.motor_asyncio import AsyncIOMotorClient


logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("cdc_hierarchy")

KAFKA_BOOTSTRAP = "kafka:29092"
KAFKA_GROUP_ID = "university_hierarchy_group"
KAFKA_TOPICS = [
    "university_db.public.universities",
    "university_db.public.institutes",
    "university_db.public.departments",
]

MONGO_URI = "mongodb://admin:P%40ssw0rd@mongodb:27017"
MONGO_DB = "university"
MONGO_COLL = "universities"

# Кафедры, пришедшие раньше своего института
pending_depts: dict[int, list[dict]] = {}


async def _remove_dept_from_other_institutes(coll, dept_id: int,
                                             target_iid: int) -> None:
    await coll.update_many(
        {"institutes.departments.department_id": dept_id},
        {"$pull": {"institutes.$[inst].departments":
                   {"department_id": dept_id}}},
        array_filters=[{"inst.institute_id": {"$ne": target_iid}}],
    )


async def _remove_inst_from_other_universities(coll, inst_id: int,
                                               target_uid: int) -> None:
    await coll.update_many(
        {"institutes.institute_id": inst_id,
         "university_id": {"$ne": target_uid}},
        {"$pull": {"institutes": {"institute_id": inst_id}}},
    )


async def handle_university(coll, after):
    await coll.update_one(
        {"university_id": after["university_id"]},
        {"$set": {"name": after["name"]},
         "$setOnInsert": {"institutes": []}},
        upsert=True,
    )
    logger.info("Upserted university %s", after["university_id"])


async def handle_institute(coll, after):
    uid = after["university_id"]
    iid = after["institute_id"]

    # 0. достаём полную запись института (если она уже где-то есть)
    old_holder = await coll.find_one(
        {"institutes.institute_id": iid},
        {"institutes.$": 1, "university_id": 1}
    )
    inst_full = None
    if old_holder:
        inst_full = old_holder["institutes"][0]
        inst_full["name"] = after["name"]

    # 1. удаляем институт из всех прежних университетов
    await _remove_inst_from_other_universities(coll, iid, uid)

    # 2. пробуем обновить в целевом университете (если он уже там есть)
    res = await coll.update_one(
        {"university_id": uid, "institutes.institute_id": iid},
        {"$set": {"institutes.$.name": after["name"]}},
    )
    if res.matched_count:
        logger.info("Updated institute %s in university %s", iid, uid)
    else:
        # 3. если у нового вуза института нет — вставляем полный объект
        if inst_full is None:
            inst_full = {
                "institute_id": iid,
                "name": after["name"],
                "departments": [],
            }
        await coll.update_one(
            {"university_id": uid},
            {"$push": {"institutes": inst_full}},
            upsert=True,
        )
        logger.info("Inserted institute %s into university %s", iid, uid)

    # 4. применяем отложенные кафедры
    if iid in pending_depts:
        for dept_after in pending_depts.pop(iid):
            await handle_department(coll, dept_after)


async def handle_department(coll, after):
    did = after["dept_id"]
    iid = after["institute_id"]

    # 1. убираем кафедру из всех чужих институтов
    await _remove_dept_from_other_institutes(coll, did, iid)

    # 2. пробуем обновить в целевом институте
    res = await coll.update_one(
        {"institutes.institute_id": iid,
         "institutes.departments.department_id": did},
        {"$set": {
            "institutes.$[inst].departments.$[dept].name": after["name"],
            "institutes.$[inst].departments.$[dept].head": after["head"],
            "institutes.$[inst].departments.$[dept].phone": after["phone"],
        }},
        array_filters=[{"inst.institute_id": iid},
                       {"dept.department_id": did}],
    )
    if res.matched_count:
        logger.info("Updated department %s in institute %s", did, iid)
        return

    # 3. кафедры ещё нет — добавляем
    if await coll.count_documents({"institutes.institute_id": iid}, limit=1):
        await coll.update_one(
            {"institutes.institute_id": iid},
            {"$push": {"institutes.$.departments": {
                "department_id": did,
                "name": after["name"],
                "head": after["head"],
                "phone": after["phone"],
            }}},
        )
        logger.info("Inserted department %s into institute %s", did, iid)
    else:
        # институт не пришёл — буферизуем
        pending_depts.setdefault(iid, []).append(after)
        logger.info("Buffered department %s for future institute %s", did, iid)


async def delete_university(coll, before):
    uid = before["university_id"]
    await coll.delete_one({"university_id": uid})
    logger.info("Deleted university %s", uid)


async def delete_institute(coll, before):
    uid = before["university_id"]
    iid = before["institute_id"]
    await coll.update_one(
        {"university_id": uid},
        {"$pull": {"institutes": {"institute_id": iid}}},
    )
    logger.info("Deleted institute %s from university %s", iid, uid)


async def delete_department(coll, before):
    iid = before["institute_id"]
    did = before["dept_id"]
    await coll.update_one(
        {"institutes.institute_id": iid},
        {"$pull": {"institutes.$.departments": {"department_id": did}}},
    )
    logger.info("Deleted department %s from institute %s", did, iid)


async def consume():
    client = AsyncIOMotorClient(MONGO_URI)
    coll = client[MONGO_DB][MONGO_COLL]
    await coll.delete_many({})
    logger.info("Cleared existing universities collection")

    consumer = AIOKafkaConsumer(
        *KAFKA_TOPICS,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id=KAFKA_GROUP_ID,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        value_deserializer=lambda v: json.loads(v.decode()) if v else None,
    )

    await consumer.start()
    try:
        async for msg in consumer:
            if msg.value is None:
                continue

            op = msg.value.get("op")
            before = msg.value.get("before")
            after = msg.value.get("after")
            table = msg.topic.split('.')[-1]

            if op == "d":
                if table == "universities":
                    await delete_university(coll, before)
                elif table == "institutes":
                    await delete_institute(coll, before)
                elif table == "departments":
                    await delete_department(coll, before)

            elif op in ("c", "u", "r"):
                if table == "universities":
                    await handle_university(coll, after)
                elif table == "institutes":
                    await handle_institute(coll, after)
                elif table == "departments":
                    await handle_department(coll, after)
            else:
                logger.warning("Unknown op: %s", op)
    finally:
        await consumer.stop()
        client.close()


if __name__ == "__main__":
    asyncio.run(consume())