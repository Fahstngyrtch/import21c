#!/usr/bin/python
# -*- coding: utf-8 -*-
""" ...
    Импорт данных в 1С
    
    Модуль содержит профильные классы для создания документов с разными наборами проводок
"""
import logging

import connector
import export_constants
from export_constants import LOG_ALIAS, CONN_MAP, DEFAULT
from documentor import Predictor

logger = logging.getLogger(LOG_ALIAS)


def make_settings(mode):
    """ Определение настроек согласно указанному режиму работы """
    logger.debug("Work mode: {0}".format(mode))
    work_mode = CONN_MAP[mode] if mode in CONN_MAP else CONN_MAP[DEFAULT]
    return work_mode[1:]


class Corrector(object):
    """ Базовый класс """
    def __init__(self, org, doc_date, doc_sum):
        try:
            self.__predictor = Predictor(org, doc_date, doc_sum)
        except Exception as exc:
            logger.error(exc)
            self.__predictor = None
        else:
            self.get_agent = self.__predictor.get_agent
            self.get_deal = self.__predictor.get_deal
            self.get_explanation = self.__predictor.get_explanation

        self.__comment = ""
        self.__explanation = None
        self.__dt = ""
        self.__kt = ""
        self.__ext_dt = []
        self.__ext_kt = []

    @property
    def predictor(self):
        """ Объект типа Predictor, работающий с проводками по документу """
        return self.__predictor

    def get_agent(self, _):
        """ Контрагент """
        raise NotImplementedError()

    def get_deal(self, _):
        """ Договор """
        raise NotImplementedError()

    def get_explanation(self, _):
        """ Содержание документа """
        raise NotImplementedError()

    @property
    def dt(self):
        """ Дебетовый счет """
        return self.__dt

    @dt.setter
    def dt(self, value):
        """ Установка дебетового счета """
        self.__dt = value

    @property
    def kt(self):
        """ Кредитовый счет """
        return self.__kt

    @kt.setter
    def kt(self, value):
        """ Установка кредитового счета """
        self.__kt = value

    @property
    def comment(self):
        """ Комментарий к документу """
        return self.__comment

    @comment.setter
    def comment(self, value):
        """ Назначение комментария """
        self.__comment = value

    @property
    def explanation(self):
        """ Операция по счету """
        return self.__explanation

    @explanation.setter
    def explanation(self, value):
        """ Назначение операции по счету """
        self.__explanation = value

    def fill_dt(self, *ext):
        """ Запись нескольких дебетовых проводок """
        for item in ext:
            self.__ext_dt.append(item)

    def fill_kt(self, *ext):
        """ Запись нескольких кредитовых проводок """
        for item in ext:
            self.__ext_kt.append(item)

    def make(self, *_):
        logger.debug("1: Connector: init")
        self.predictor.init(self.dt, self.kt, self.comment)
        logger.debug("2: Call predictor.make")
        return self.predictor.make(ext_dt=self.__ext_dt, ext_kt=self.__ext_kt)


class IncomeCorrector(Corrector):
    """ Родительский класс для семейства документов, работающих по счетам 50.06 : 62.01 """
    def __init__(self, org, doc_date, doc_sum, comment):
        logger.info("IncomeCorrector")
        super(IncomeCorrector, self).__init__(org, doc_date, doc_sum)
        self.dt, self.kt = "50.06", "62.01"
        self.comment = comment

    def make(self, agent_id, doc_num):
        logger.info("IncomeCorrector: make")
        agent = self.get_agent(agent_id)
        if agent is None:
            logger.error("Agent {} is not found".format(agent_id))
            return False

        deal = self.get_deal(doc_num)
        if deal is None:
            logger.error("Deal {} is not found".format(doc_num))
            return False

        self.fill_kt(("Контрагенты", agent), ("Договоры", deal))
        return super(IncomeCorrector, self).make()


class ClearProfitCorrector(Corrector):
    """ Родительский класс для семейства документов, работающих по счетам 50.06 : 90.01.1 """
    def __init__(self, org, doc_date, doc_sum, comment, explanation):
        super(ClearProfitCorrector, self).__init__(org, doc_date, doc_sum)
        self.dt, self.kt = "50.06", "90.01.1"
        self.comment = comment
        self.explanation = explanation

    def make(self, *_):
        expl = self.get_explanation(self.explanation)
        if expl is None:
            logger.error("Explanation is not found")
            return False

        self.fill_kt(("Номенклатурные группы", expl))
        return super(ClearProfitCorrector, self).make()


class ProfitCorrector(Corrector):
    """ Родительский класс для семейства документов, работающих по счетам 62.01 : 90.01.1 """
    def __init__(self, org, doc_date, doc_sum, comment, explanation):
        super(ProfitCorrector, self).__init__(org, doc_date, doc_sum)
        self.dt, self.kt = "62.01", "90.01.1"
        self.comment = comment
        self.explanation = explanation

    def make(self, agent_id, doc_num):
        agent = self.get_agent(agent_id)
        if agent is None:
            logger.error("Agent {} is not found".format(agent_id))
            return False

        deal = self.get_deal(doc_num)
        if deal is None:
            logger.error("Deal {} is not found".format(doc_num))
            return False

        expl = self.get_explanation(self.explanation)
        if expl is None:
            logger.error("Explanation {} is not found".format(doc_num))
            return False

        self.fill_dt(("Контрагенты", agent), ("Договоры", deal))
        self.fill_kt(("Номенклатурные группы", expl))
        return super(ProfitCorrector, self).make()


class AccGeneral(IncomeCorrector):
    """ Реализация пассажирских билетов """
    def __init__(self, org, doc_date, doc_sum):
        logger.info("AccGeneral")
        super(AccGeneral, self).__init__(org, doc_date, doc_sum, "Реализация пассажирских билетов")


class AccGeneralAcq(IncomeCorrector):
    """ Реализация пассажирских билетов (эквайринг) """
    def __init__(self, org, doc_date, doc_sum):
        super(AccGeneralAcq, self).__init__(org, doc_date, doc_sum, "Реализация пассажирских билетов (эквайринг)")


class AccBagage(IncomeCorrector):
    """ Реализация багажных билетов """
    def __init__(self, org, doc_date, doc_sum):
        super(AccBagage, self).__init__(org, doc_date, doc_sum, "Реализация багажных билетов")


class AccBagageAcq(IncomeCorrector):
    """ Реализация багажных билетов (эквайринг) """
    def __init__(self, org, doc_date, doc_sum):
        super(AccBagageAcq, self).__init__(org, doc_date, doc_sum, "Реализация багажных билетов (эквайринг)")


class AccKomsbProfit(ClearProfitCorrector):
    """ Предварительная продажа билетов """
    def __init__(self, org, doc_date, doc_sum):
        super(AccKomsbProfit, self).__init__(org, doc_date, doc_sum, "Предварительная продажа билетов", "Комиссионный Сбор")


class AccKomsbProfitAcq(ClearProfitCorrector):
    """ Предварительная продажа билетов (эквайринг) """
    def __init__(self, org, doc_date, doc_sum):
        super(AccKomsbProfitAcq, self).__init__(org, doc_date, doc_sum, "Предварительная продажа билетов (эквайринг)", "Комиссионный Сбор")


class AccBroneProfit(ClearProfitCorrector):
    """ Бронь """
    def __init__(self, org, doc_date, doc_sum):
        super(AccBroneProfit, self).__init__(org, doc_date, doc_sum, "Бронь", "Бронь")


class AccBroneProfitAcq(ClearProfitCorrector):
    """ Бронь (эквайринг) """
    def __init__(self, org, doc_date, doc_sum):
        super(AccBroneProfitAcq, self).__init__(org, doc_date, doc_sum, "Бронь (эквайринг)", "Бронь")


class AccBrokenProfit(ClearProfitCorrector):
    """ Доходы от невозвращенных билетов """
    def __init__(self, org, doc_date, doc_sum):
        super(AccBrokenProfit, self).__init__(org, doc_date, doc_sum, "Доходы от невозвращенных билетов", "Доходы от невозвращенных билетов")


class AccBrokenProfitAcq(ClearProfitCorrector):
    """ Доходы от невозвращенных билетов (эквайринг) """
    def __init__(self, org, doc_date, doc_sum):
        super(AccBrokenProfitAcq, self).__init__(org, doc_date, doc_sum, "Доходы от невозвращенных билетов (эквайринг)", "Доходы от невозвращенных билетов")


class AccReturns(ClearProfitCorrector):
    """ 25% Возврат билетов """
    def __init__(self, org, doc_date, doc_sum):
        super(AccReturns, self).__init__(org, doc_date, doc_sum, "25% Возврат билетов", "Доходы от % по возвращенным билетам")


class AccReturnsAcq(ClearProfitCorrector):
    """ 25% Возврат билетов (эквайринг) """
    def __init__(self, org, doc_date, doc_sum):
        super(AccReturnsAcq, self).__init__(org, doc_date, doc_sum, "25% Возврат билетов (эквайринг)", "Доходы от % по возвращенным билетам")


class AccVoluntaryReturns(ClearProfitCorrector):
    """ Возврат билетов """
    def __init__(self, org, doc_date, doc_sum):
        super(AccVoluntaryReturns, self).__init__(org, doc_date, doc_sum, "Возврат билетов", "Доходы от % по возвращенным билетам")


class AccVoluntaryReturnsAcq(ClearProfitCorrector):
    """ Возврат билетов (эквайринг) """
    def __init__(self, org, doc_date, doc_sum):
        super(AccVoluntaryReturnsAcq, self).__init__(org, doc_date, doc_sum, "Возврат билетов (эквайринг)", "Доходы от % по возвращенным билетам")


class AccGeneralProcent(ProfitCorrector):
    """ Процент от перевозки пассажиров """
    def __init__(self, org, doc_date, doc_sum):
        super(AccGeneralProcent, self).__init__(org, doc_date, doc_sum, "Процент от перевозки пассажиров", "% от перевозки пассажиров")


class AccGeneralProcentAcq(ProfitCorrector):
    """ Процент от перевозки пассажиров (эквайринг) """
    def __init__(self, org, doc_date, doc_sum):
        super(AccGeneralProcentAcq, self).__init__(org, doc_date, doc_sum, "Процент от перевозки пассажиров (эквайринг)", "% от перевозки пассажиров")


class AccBagageProcent(ProfitCorrector):
    """ Процент от перевозки багажа """
    def __init__(self, org, doc_date, doc_sum):
        super(AccBagageProcent, self).__init__(org, doc_date, doc_sum, "Процент от перевозки багажа", "% от перевозки багажа")


class AccBagageProcentAcq(ProfitCorrector):
    """ Процент от перевозки багажа (эквайринг) """
    def __init__(self, org, doc_date, doc_sum):
        super(AccBagageProcentAcq, self).__init__(org, doc_date, doc_sum, "Процент от перевозки багажа (эквайринг)", "% от перевозки багажа")


class AccMissingProfit(ProfitCorrector):
    """ Доходы от неявок """
    def __init__(self, org, doc_date, doc_sum):
        super(AccMissingProfit, self).__init__(org, doc_date, doc_sum, "Доходы от неявок", "Доходы от невозвращенных билетов")


class AccMissingProfitAcq(ProfitCorrector):
    """ Доходы от неявок (эквайринг) """
    def __init__(self, org, doc_date, doc_sum):
        super(AccMissingProfitAcq, self).__init__(org, doc_date, doc_sum, "Доходы от неявок (эквайринг)", "Доходы от невозвращенных билетов")


class AccOtherPrivilege(ProfitCorrector):
    """ Соц. работники и прочие льготные категории """
    def __init__(self, org, doc_date, doc_sum):
        super(AccOtherPrivilege, self).__init__(org, doc_date, doc_sum, "Соц. работники и прочие льготные категории", "Прочие льготники")


class AccStatePrivilege(ProfitCorrector):
    """ Региональные льготные категории """
    def __init__(self, org, doc_date, doc_sum):
        super(AccStatePrivilege, self).__init__(org, doc_date, doc_sum, "Региональные льготные категории", "Доходы по региональным льготникам")


class AccFederalPrivilege(ProfitCorrector):
    """ Федеральные льготные категории """
    def __init__(self, org, doc_date, doc_sum):
        super(AccFederalPrivilege, self).__init__(org, doc_date, doc_sum, "Федеральные льготные категории", "Доходы по федеральным льготникам")


class AccMedService(ProfitCorrector):
    """ Медосмотр """
    def __init__(self, org, doc_date, doc_sum):
        super(AccMedService, self).__init__(org, doc_date, doc_sum, "Медосмотр", "Медосмотр")


class AccBreakFine(ProfitCorrector):
    """ Срыв рейса """
    def __init__(self, org, doc_date, doc_sum):
        super(AccBreakFine, self).__init__(org, doc_date, doc_sum, "Срыв рейса", "Срыв рейса")


class AccParkingService(ProfitCorrector):
    """ Стоянка """
    def __init__(self, org, doc_date, doc_sum):
        super(AccParkingService, self).__init__(org, doc_date, doc_sum, "Стоянка", "Стоянка")


class AccTechService(ProfitCorrector):
    """ Техосмотр """
    def __init__(self, org, doc_date, doc_sum):
        super(AccTechService, self).__init__(org, doc_date, doc_sum, "Техосмотр", "Техосмотр")


class AccLateFine(ProfitCorrector):
    """ Опоздание """
    def __init__(self, org, doc_date, doc_sum):
        super(AccLateFine, self).__init__(org, doc_date, doc_sum, "Опоздание", "Опоздание")


class AccEquipFine(ProfitCorrector):
    """ Нарушение экипировки """
    def __init__(self, org, doc_date, doc_sum):
        super(AccEquipFine, self).__init__(org, doc_date, doc_sum, "Нарушение экипировки", "Нарушение экипировки")
