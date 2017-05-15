#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" ...
    Импорт данных в 1С

    Бухгалтерия должна иметь следующие настройки:
        Идентификаторы контрагентов должны совпадать в 1С и ....
        Справочник "ВидыСубконтоХозрасчетные" должен содержать элементы:
            - Комиссионный Сбор
            - Бронь
            - Доходы от невозвращенных билетов
            - Доходы от % по возвращенным билетам
            - % от перевозки пассажиров
            - % от перевозки багажа
            - Доходы от невозвращенных билетов
            - Прочие льготники
            - Доходы по региональным льготникам
            - Доходы по федеральным льготникам
            - Медосмотр
            - Срыв рейса
            - Стоянка
            - Техосмотр
            - Опоздание
            - Нарушение экипировки
"""
import sys
import logging
import logging.handlers
from threading import Thread

from export_constants import LOG_ALIAS, LOG_LEVEL, LOG_FILENAME
from export_constants import RECEIVE_CHANNELS
import accounter
import receiver
from rmq_receive_channel import run as rmq_run
from rpyc_receive_channel import run as rpyc_run

logger = logging.getLogger(LOG_ALIAS)
logger.setLevel(LOG_LEVEL)
handler = logging.handlers.RotatingFileHandler(LOG_FILENAME,
                                               maxBytes=512000,
                                               backupCount=10)
logger.addHandler(handler)

MODE = 'test_av'    # режим работы системы
try:
    org, alias = accounter.make_settings(MODE)
except Exception as exc:
    logger.error(exc)
    sys.exit(1)

receiver.org.org = org
# режимы приема данных  rmq - посредством RabbitMQ, rpyc - посредством RPyC
listeners = {'rmq': rmq_run, 'rpyc': rpyc_run}


def run():
    # запуск потоков прослушивания по используемым режимам приема даных
    for channel, in_use in RECEIVE_CHANNELS.items():
        if in_use:
            thr = Thread(target=listeners[channel])
            thr.setDaemon(True)
            thr.start()

    receiver.work()


if __name__ == '__main__':
    logger.info("Service started")
    run()
    logger.info("Service stopped")
