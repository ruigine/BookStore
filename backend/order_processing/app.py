import json
import requests
import time
from rabbitmq import RabbitMQClient

ORDERS_URL = "http://orders:5003/orders"

def process_order(ch, method, properties, body):
    order = json.loads(body)
    order_id = order["order_id"]

    # Simulate processing delay
    time.sleep(5)

    # Update order status to 'completed'
    update_data = {"status": "completed"}
    response = requests.put(f"{ORDERS_URL}/{order_id}", json=update_data)

    ch.basic_ack(delivery_tag=method.delivery_tag)

client = RabbitMQClient()

if __name__ == "__main__":
    client.consume(process_order)