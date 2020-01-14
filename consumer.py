import pika
import requests
import os
import logging
import json
import base64


def otherwise(x, default):
    return default if x is None else x


funnel_endpoint = otherwise(
    os.getenv('CS2D_FUNNEL_ENDPOINT'), 'http://localhost:8090/recv')
funnel_channel = otherwise(
    os.getenv('CS2D_FUNNEL_CHANNEL'), 'amqp')
host = otherwise(os.getenv('CS2D_AMQP_HOST'), 'localhost')
port = otherwise(os.getenv('CS2D_AMQP_PORT'), 5672)
exchange = otherwise(os.getenv('CS2D_AMQP_EXCHANGE'), 'cs2d')
queue = otherwise(os.getenv('CS2D_AMQP_QUEUE'), '')
routing_keys_env = otherwise(os.getenv('CS2D_AMQP_ROUTING_KEYS'), '')
logging_level = otherwise(os.getenv('CS2D_AMQP_LOGGING'), 'INFO')

logging.basicConfig(
    format='[%(levelname)s] %(asctime)s : %(message)s', level=getattr(logging, logging_level))


def callback(ch, method, properties, body):
    logging.info("Received message (routing key %r): %r" %
                 (method.routing_key, body))
    message = {
        "chan": funnel_channel,
        "data": json.dumps({
            "exchange": exchange,
            "queue": queue,
            "routing_key": method.routing_key,
            "body": base64.b64encode(body).decode("utf-8"),
        }),
    }
    requests.get(funnel_endpoint, params=message)


def main():
    global queue
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=host, port=port))
    channel = connection.channel()

    channel.exchange_declare(exchange=exchange, exchange_type='topic')
    logging.debug('Declared exchange %s', exchange)

    result = channel.queue_declare(queue=queue, exclusive=True)
    queue = result.method.queue

    routing_keys = routing_keys_env.split(',')

    for routing_key in routing_keys:
        channel.queue_bind(exchange=exchange,
                           queue=queue, routing_key=routing_key)
        logging.debug('Bound queue %s with routing key %s',
                      queue, routing_key)

    logging.info('Waiting for messages')

    channel.basic_consume(
        queue=queue, on_message_callback=callback, auto_ack=True)

    channel.start_consuming()


if __name__ == "__main__":
    main()
