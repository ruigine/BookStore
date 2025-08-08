import json
import requests
import time
from rabbitmq import RabbitMQClient

ORDERS_URL = "http://orders:5003/orders"
BOOKS_URL = "http://books:5002/books"

def process_order(ch, method, properties, body):
    try:
        order = json.loads(body)
        order_id = order["order_id"]
        book_id = order["book_id"]
        quantity_ordered = order["quantity"]

        print(f"Processing order {order_id}...")

        time.sleep(5)

        # Step 1: Decrement book quantity
        decrement_res = requests.put(
            f"{BOOKS_URL}/{book_id}",
            json={"quantity_ordered": quantity_ordered}
        )

        if decrement_res.status_code != 200:
            print(f"Error: {decrement_res.json().get('message')}")
            update_res = requests.put(f"{ORDERS_URL}/{order_id}", json={"status": f"failed"})
            if update_res.ok:
                print(f"Order {order_id} updated to 'failed'.")
            else:
                print(f"Failed to update order status.")
            return

        # Step 2: Update order status to completed
        update_res = requests.put(f"{ORDERS_URL}/{order_id}", json={"status": "completed"})

        if update_res.ok:
            print(f"Order {order_id} completed successfully.")
        else:
            print(f"Failed to update order status.")

    except Exception as e:
        print(f"Error processing order: {e}")
        update_res = requests.put(f"{ORDERS_URL}/{order_id}", json={"status": f"failed"})
        if update_res.ok:
            print(f"Order {order_id} updated to 'failed'.")
        else:
            print(f"Failed to update order status.")

    finally:
        ch.basic_ack(delivery_tag=method.delivery_tag)

client = RabbitMQClient()

if __name__ == "__main__":
    client.consume(process_order)