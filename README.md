# CS2D Funnel: AMQP module

This is a simple message broker that consumes messages from an AMQP queue and
passes them to Funnel with some AMQP metadata. This module may be used in your
projects; however, it is opinionated in several aspects:

* It implements the subscriber part of a pub/sub system; the `examples` directory
contains an example Lua script which implements the publisher part for publishing
game chat messages to the AMQP queue (CS2D JIT and `amqp-client` required).
* It uses a `topic` exchange. Other exchange types are not supported in this module.

As always, this is a simple system primarily built for illustrative purposes.
It may be prone to security issues and instabilities. However, PRs are always
welcome!

## Docker example

In an example Docker configuration, suppose we have:
* A prepared CS2D server instance in `/srv/cs2d_server1` on the host (with XCH
and the example `chat_publisher.lua` script installed and set up to run)
* A network called `amqp`
* A `rabbitmq` container connected to that network (called `rabbitmq` for
simplicity)

A Docker compose file would then look something like this:

```yml
version: '3.1'

services:
  server:
    image: engin33r/cs2djit:latest
    restart: always
    ports:
      - "36960:36963/udp"
    volumes:
      - "/srv/cs2d_server1:/cs2d"
      - "luarocks:/root/rocks"
    networks:
      - amqp
  funnel:
    image: engin33r/cs2d-funnel:latest
    restart: always
    volumes:
      - "/srv/cs2d_server1:/out"
    networks:
      - funnel
  funnelmq:
    image: cs2d-funnel-amqp:latest
    restart: always
    env_file:
      - ./.env
    networks:
      - funnel
      - amqp

volumes:
  luarocks:

networks:
  funnel:
  amqp:
    external: true
```

Now we just need our AMQP Funnel module to point to the Funnel and RabbitMQ
containers using their names as addresses, instead of the default `localhost`.
We configure this in the `.env` file:

```
CS2D_FUNNEL_ENDPOINT=http://funnel:8090/recv
CS2D_AMQP_HOST=rabbitmq
CS2D_AMQP_ROUTING_KEYS=chat
```

We can then start the containers with `docker-compose up -d`, join the server,
send a chat message and verify the messages are being communicated by inspecting
`docker-compose logs funnel` and `docker-compose logs funnelmq`.

Creating further Docker compose configurations and adjusting the server IDs in
the example `chat_publisher.lua` script will allow you to see the messages, as
long as you're monitoring both servers simultaneously, or if you've got a friend
to test it with.

## Configuration

Configuration is performed using environment variables, as the module is mainly
designed to run in a Docker context.

| Variable | Default value | Description |
| -------- | ------------- | ----------- |
| `CS2D_FUNNEL_ENDPOINT` | `http://localhost:8090/recv` | Endpoint of the Funnel instance |
| `CS2D_FUNNEL_CHANNEL` | `amqp` | Channel that will be used for Funnel communications (`chan`) |
| `CS2D_AMQP_HOST` | `localhost` | AMQP message broker hostname |
| `CS2D_AMQP_PORT` | `5672` | AMQP message broker port |
| `CS2D_AMQP_EXCHANGE` | `cs2d` | AMQP exchange name |
| `CS2D_AMQP_QUEUE` |  | AMQP queue name (empty by default for random queue name) |
| `CS2D_AMQP_ROUTING_KEYS` |  | Comma-separated list of routing keys for consumption |
| `CS2D_AMQP_LOGGING` | `INFO` | Logging level for internal logs (incl. Pika logging) |

## Message format

This module passes data of the following format to Funnel (example values):

```json
{
    "exchange": "cs2d",
    "queue": "amq.gen-XXXXXXX",
    "routing_key": "chat",
    "body": "...",
}
```

`body` is a base64 representation of the consumed AMQP message.