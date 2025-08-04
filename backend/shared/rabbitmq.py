import pika
import json
import time
from os import environ

class RabbitMQClient:
    def __init__(
        self,
        host='rabbitmq',
        port=5672,
        username=environ.get('RABBITMQ_DEFAULT_USER'),
        password=environ.get('RABBITMQ_DEFAULT_PASS'),
        exchange='orders',
        exchange_type='direct',
        queue='order_queue',
        routing_key='order.new'
    ):
        self.host = host
        self.port = port
        self.credentials = pika.PlainCredentials(username, password)
        self.exchange = exchange
        self.exchange_type = exchange_type
        self.queue = queue
        self.routing_key = routing_key

        self.connection = None
        self.channel = None

        self.check_setup()

    def is_connection_open(self):
        try:
            if self.connection and self.connection.is_open:
                self.connection.process_data_events()
                return True
        except pika.exceptions.AMQPError as e:
            print("[x] AMQP Error:", e)
        return False

    def check_setup(self):
        if not self.is_connection_open():
            print("[!] Creating RabbitMQ connection...")
            params = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                credentials=self.credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            self.connection = pika.BlockingConnection(params)
            self.channel = self.connection.channel()

        if not self.channel or self.channel.is_closed:
            print("[!] Creating RabbitMQ channel...")
            self.channel = self.connection.channel()

        # Declare exchange and queue
        self.channel.exchange_declare(exchange=self.exchange, exchange_type=self.exchange_type, durable=True)
        self.channel.queue_declare(queue=self.queue, durable=True)
        self.channel.queue_bind(exchange=self.exchange, queue=self.queue, routing_key=self.routing_key)

    def publish(self, payload):
        self.check_setup()
        self.channel.basic_publish(
            exchange=self.exchange,
            routing_key=self.routing_key,
            body=json.dumps(payload),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        print(f"[→] Sent: {payload}")

    def consume(self, callback):
        while True:
            try:
                self.check_setup()
                self.channel.basic_qos(prefetch_count=1)
                self.channel.basic_consume(queue=self.queue, on_message_callback=callback)
                print(" [*] Consumer waiting for messages...")
                self.channel.start_consuming()
            except pika.exceptions.AMQPError as e:
                print(f"[!] AMQP error: {e}")
            except Exception as e:
                print(f"[!] Unexpected error: {e}")
            finally:
                if self.connection and self.connection.is_open:
                    try:
                        self.connection.close()
                    except Exception:
                        pass
                print(f"[!] Reconnecting in 2 seconds...\n")
                time.sleep(2)


''' PUBLISHER SAMPLE
from rabbitmq import RabbitMQClient
import time

client = RabbitMQClient()

if __name__ == "__main__":
    while True:
        time.sleep(2)
        client.publish({"msg": "hi"})
'''

''' CONSUMER SAMPLE
from rabbitmq import RabbitMQClient
import json
import time

def process_order(ch, method, properties, body):
    data = json.loads(body)
    print(f" [✓] Processing order: {data}")
    time.sleep(5)
    ch.basic_ack(delivery_tag=method.delivery_tag)

client = RabbitMQClient()

if __name__ == "__main__":
    client.consume(process_order)
'''