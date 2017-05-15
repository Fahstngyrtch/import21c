# -*- coding: utf-8 -*-
""" ...
    Экспорт данных в 1С
    Работа основана на использовании RPyC
"""
import rpyc
from rpyc.utils.server import ThreadedServer
import json
import logging

import receiver
from export_constants import HOST, SERVICE_PORT, LOG_ALIAS, EXPORT_KEYS

logger = logging.getLogger(LOG_ALIAS)


class ExportService(rpyc.Service):
    def exposed_export(self, key, body):
        """ Обработчик сообщений
        :param key: тип экспортируемых данных
        :param body: данные для экспорта
        """
        try:
            data = json.loads(body)
            receiver.receive(key, data)
        except ValueError as v_err:
            logger.error("Broken message")
            logger.debug(body)
            logger.error(v_err)
            return []
        except StandardError as s_err:
            logger.error(s_err)


def run():
    logger.info("Start RPyC listener")
    ThreadedServer(ExportService, port=SERVICE_PORT).start()
