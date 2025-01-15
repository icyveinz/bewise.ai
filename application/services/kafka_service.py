from aiokafka import AIOKafkaProducer
import json

producer = None


async def get_producer():
    global producer
    if producer is None:
        producer = AIOKafkaProducer(bootstrap_servers="kafka:9092")
        await producer.start()
    return producer


async def send_to_kafka(topic: str, message: dict):
    producer = await get_producer()
    await producer.send_and_wait(topic, json.dumps(message).encode("utf-8"))
