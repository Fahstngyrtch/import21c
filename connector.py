#!/usr/bin/python
# -*- coding: utf-8 -*-
""" ...
    Экспорт данных в 1С
    Работа с подключением к базе 1С на основе COM-объекта
"""
import logging
import pythoncom
import win32com.client

from export_constants import CONN_MAP, DEFAULT, LOG_ALIAS

logger = logging.getLogger(LOG_ALIAS)


def connection():
    """ Функция возвращает COM-объект, хранящий открытое подключение к 1С
        Если объект не существует, то он создается
    """
    if not hasattr(connection, 'conn'):
        make_connection()
    return connection.conn



def make_connection():
    """ Открытие соединения с 1С, создание COM-объекта """
    pythoncom.CoInitialize()
    try:
        conn = win32com.client.Dispatch("VXX.COMConnector.1")
    except pythoncom.com_error as com_error:
        logger.error(com_error.strerror)
    except StandardError as std_err:
        logger.error(std_err)
    else:
        res = None
        c_str, org, channel = CONN_MAP[DEFAULT]
        try:
            logger.debug("Connect to {0}".format(c_str))
            res = conn.Connect(c_str)
        except StandardError as std_err:
            logger.error(std_err)
        else:
            connection.conn = res


def disconnect():
    """ Закрытие соединения """
    if hasattr(connection, 'conn'):
        del connection.conn
    pythoncom.CoUninitialize()


class Connector(object):
    """ Базовый класс для работы с подключением к 1C 
        Класс содержит ряд вспомогательных методов для работы со справочниками
    """
    def __init__(self):
        logger.debug("Init connection")
        self.connector = connection()

    def _get_object(self, instance):
        logger.debug("Call GetObject of instance")
        try:
            return instance.GetObject()
        except pythoncom.com_error as com_error:
            logger.error(com_error.strerror)
        except StandardError as std_err:
            logging.error(std_err)

        return None

    def get_organization(self, org_id):
        """ Поиск организации по ID """
        logger.debug("Get organization {0}".format(org_id))
        try:
            dicts = getattr(connection().Catalogs, "Организации").FindByCode("%09d" % org_id)
        except pythoncom.com_error as com_error:
            logger.error(com_error.strerror)
            return None
        except StandardError as std_err:
            logger.error(std_err)
            return None
        return self._get_object(dicts)

    def get_agent(self, agent_id, reference=True):
        """ Поиск контрагента по ID """
        logger.debug("Get agent")
        try:
            agent = getattr(connection().Catalogs, "Контрагенты").FindByCode("%d" % agent_id)
            res = self._get_object(agent)
        except pythoncom.com_error as com_error:
            logger.error(com_error.strerror)
            res = None

        if reference:
            return res.Ref if res is not None else None

    def get_explanation(self, title, reference=True):
        """ Поиск номенклатурной группы """
        logger.debug("Get explanation")
        try:
            groups = getattr(connection().Catalogs, "НоменклатурныеГруппы").FindByDescription(title)
            res = self._get_object(groups)
        except pythoncom.com_error as com_error:
            logger.error(com_error.strerror)
            res = None

        if reference:
            return res.Ref if res is not None else None
        return res

    def get_deal(self, number, reference=True):
        """ Поиск договора по номеру """
        logger.debug("Get deal")
        try:
            deal = getattr(connection().Catalogs, "ДоговорыКонтрагентов").FindByCode("%09d" % number)
            res = self._get_object(deal)
        except pythoncom.com_error as com_error:
            logger.error(com_error.strerror)
            res = None

        if reference:
            return res.Ref if res is not None else None
        return res
