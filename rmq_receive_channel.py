#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" ...
    Экспорт данных в 1С
    Работа на основе очереди сообщений RabbitMQ
"""
import sys
import time
import pika
import json
import logging

import receiver
from export_constants import HOST, LOG_ALIAS

logger = logging.getLogger(LOG_ALIAS)


def callback(ch, method, properties, body):
    """ Обработчик сообщений """
    try:
        data = json.loads(body)
        key = method.routing_key
        receiver.receive(key, data)
    except ValueError, v_err:
        logger.error("Broken message")
        logger.debug(body)
        logger.error(v_err)
    except StandardError as s_err:
        logger.error(s_err)


def run():
    logger.info("Start pika listener")
    from export_constants import CH_NAME, EXPORT_KEYS
    credentials = pika.PlainCredentials('agent', 'agent')
    parameters = pika.ConnectionParameters(host=HOST, credentials=credentials)
    connection = pika.BlockingConnection(parameters)

    export_channel = connection.channel()
    export_channel.exchange_declare(exchange=CH_NAME, type='direct')

    result = export_channel.queue_declare(exclusive=True)
    queue_name = result.method.queue
    for key in EXPORT_KEYS:
        export_channel.queue_bind(exchange=CH_NAME, queue=queue_name, routing_key=key)

    export_channel.basic_consume(callback, queue=queue_name, no_ack=True)

    try:
        export_channel.start_consuming()
    except KeyboardInterrupt:
        logger.info("Service stopped")
    except StandardError as std_err:
        logger.fatal(std_err)

    if connection:
        connection.close()
