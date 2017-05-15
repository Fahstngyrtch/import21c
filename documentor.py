# -*- coding: utf-8 -*-
""" ...
    Экспорт данных в 1С
    Классы для работы с документами
"""
import logging
import pythoncom

import connector
from export_constants import LOG_ALIAS

logger = logging.getLogger(LOG_ALIAS)


class Documentor(connector.Connector):
    """ Работа с документом 1С """
    def __init__(self, doc_date, doc_org, doc_sum, comment=""):
        """ Create 1C document """
        super(Documentor, self).__init__()
        try:
            self.__doc = getattr(self.connector.Documents, "ОперацияБух").CreateDocument()
        except pythoncom.com_error as com_error:
            logger.error(com_error.strerror)
            raise RuntimeError("Fail to create Documentor")
        except StandardError as std_err:
            logger.error(std_err)

        org = self.get_organization(doc_org)
        if org is None:
            raise ValueError("Организация {0} не найдена".format(doc_org))

        self.__org = org
        self.__doc.Date = doc_date

        setattr(self.__doc, "Организация", org.Ref)
        setattr(self.__doc, "Комментарий", comment)
        setattr(self.__doc, "Содержание", comment)
        setattr(self.__doc, "СуммаОперации", doc_sum)

    @property
    def doc(self):
        """ Возвращает документ (Документ) """
        return self.__doc

    @property
    def reference(self):
        """ Возвращает ссылку на документ (ДокументСсылка) """
        return self.__doc.Ref

    @property
    def org(self):
        """ Организация """
        return self.__org

    @property
    def org_ref(self):
        """ Ссылка на организацию """
        return self.__org.Ref

    def write(self):
        """ Запись документа в 1С """
        res = False
        try:
            self.__doc.write()
        except pythoncom.com_error as com_err:
            logger.error(com_err.strerror)
        except StandardError as std_err:
            logger.error(std_err)
        else:
            res = True
        return res


class Predictor(connector.Connector):
    """ Класс для работы с проводками по документу """
    def __init__(self, org_id, doc_date, doc_sum):
        super(Predictor, self).__init__()
        if (doc_sum is None) or (doc_sum <= 0):
            raise RuntimeError("Wrong document sum")
        else:
            self.__sum = doc_sum

        if doc_date is None:
            raise RuntimeError("Document date could not be empty")
        else:
            self.__date = doc_date

        org = self.get_organization(org_id)
        if org is None:
            raise RuntimeError("Could not find organization {}".format(org_id))

        self.__org = org_id
        self.__dt = None
        self.__kt = None
        self.__doc = None

    def init(self, dt, kt, comment):
        self.__dt = dt
        self.__kt = kt
        self.__doc = Documentor(self.__date, self.__org, self.__sum, comment)
        return self.__doc.write()

    def make(self, ext_dt=None, ext_kt=None):
        """ Создание проводок по документу """
        res = False
        # document accounts
        acc_register = getattr(self.connector.AccountingRegisters, "Хозрасчетный").CreateRecordSet()
        acc_register.Filter.Recorder.Set(self.__doc.reference)
        acc_record = acc_register.Add()
        acc_record.Period = self.__date
        setattr(acc_record, "Организация", self.__doc.org_ref)
        acc_record.AccountDr = getattr(self.connector.ChartsOfAccounts, "Хозрасчетный").FindByCode(self.__dt)
        acc_record.AccountCr = getattr(self.connector.ChartsOfAccounts, "Хозрасчетный").FindByCode(self.__kt)

        char_dict = getattr(self.connector.ChartsOfCharacteristicTypes, "ВидыСубконтоХозрасчетные")
        for desc, ref in (ext_dt or []):
            getattr(acc_record, "СубконтоДт").Insert(char_dict.FindByDescription(desc), ref)

        for desc, ref in (ext_kt or []):
            getattr(acc_record, "СубконтоКт").Insert(char_dict.FindByDescription(desc), ref)

        setattr(acc_record, "Сумма", self.__sum)

        try:
            acc_register.write()
        except pythoncom.com_error as com_err:
            logger.error(com_err.strerror)
            res = False
        else:
            res = True
        return res
