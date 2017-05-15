# -*- coding: utf-8 -*-
""" ...
    Импорт данных в 1С
    
    Модуль содержит фкнкции обхода очереди принятых сообщений, а также отображение управляющих слов сообщения на множество методов импорта данных
"""
import time
import json
import logging
from Queue import Queue, Empty

from connector import disconnect
from export_constants import LOG_ALIAS
from accounter import AccGeneral, AccGeneralAcq, AccBagage, AccBagageAcq, AccKomsbProfit, AccKomsbProfitAcq, AccBroneProfit, AccEquipFine, \
        AccBroneProfitAcq, AccBrokenProfit, AccBrokenProfitAcq, AccReturns, AccReturnsAcq, AccVoluntaryReturns, AccVoluntaryReturnsAcq, \
        AccGeneralProcent, AccGeneralProcentAcq, AccBagageProcent, AccBagageProcentAcq, AccMissingProfit, AccMissingProfitAcq, AccLateFine, \
        AccOtherPrivilege, AccStatePrivilege, AccFederalPrivilege, AccMedService, AccBreakFine, AccParkingService, AccTechService

key_map = {"general": {'pas_sum': 'general', 'bag_sum': 'bagage', 'komsb': 'komsb', 'brone': 'brone', 'returned': 'return25', 'g_proc': 'g_proc', 'b_proc': 'b_proc',
                       'acq_pas_sum': 'general_acq', 'acq_bag_sum': 'bagage_acq', 'acq_komsb': 'komsb_acq', 'acq_brone': 'brone_acq', 'acq_returned': 'return25_acq',
                       'acq_g_proc': 'g_proc_acq', 'acq_b_proc': 'b_proc_acq'},
           "clean": {'pas_clean': 'g_proc', 'bag_clean': 'b_proc', 'acq_pas_clean': 'g_proc_acq', 'acq_bag_clean': 'b_proc_acq'},
           "return": {'return_sum': 'return', 'acq_return_sum': 'return_acq'},
           "p_other": {'clean_sum': 'p_other'},
           "missing": {'missing': 'missing', 'acq_missing': 'missing_acq'},
           "broken": {'broken': 'broken', 'acq_broken': 'broken_acq'},
           "state": {'state': 'state'},
           "federal": {'federal': 'federal'},
           "services": {'srv_med': 'srv_med', 'srv_tech':'srv_tech', 'srv_parking': 'srv_parking'},
           "fines": {'fn_break': 'fn_break', 'fn_late': 'fn_late', 'fn_equip': 'fn_equip'}
           }
action_map = {"general": lambda org, date, _sum, agent, deal: AccGeneral(org, date, _sum).make(agent, deal),
              "general_acq": lambda org, date, _sum, agent, deal: AccGeneralAcq(org, date, _sum).make(agent, deal),
              "bagage": lambda org, date, _sum, agent, deal: AccBagage(org, date, _sum).make(agent, deal),
              "bagage_acq": lambda org, date, _sum, agent, deal: AccBagageAcq(org, date, _sum).make(agent, deal),
              "g_proc": lambda org, date, _sum, agent, deal: AccGeneralProcent(org, date, _sum).make(agent, deal),
              "g_proc_acq": lambda org, date, _sum, agent, deal: AccGeneralProcentAcq(org, date, _sum).make(agent, deal),
              "b_proc": lambda org, date, _sum, agent, deal: AccBagageProcent(org, date, _sum).make(agent, deal),
              "b_proc_acq": lambda org, date, _sum, agent, deal: AccBagageProcentAcq(org, date, _sum).make(agent, deal),
              "komsb": lambda org, date, _sum, *_: AccKomsbProfit(org, date, _sum).make(),
              "komsb_acq": lambda org, date, _sum, *_: AccKomsbProfitAcq(org, date, _sum).make(),
              "brone": lambda org, date, _sum, *_: AccBrokenProfit(org, date, _sum).make(),
              "brone_acq": lambda org, date, _sum, *_: AccBroneProfitAcq(org, date, _sum).make(),
              "missing": lambda org, date, _sum, agent, deal: AccMissingProfit(org, date, _sum).make(agent, deal),
              "missing_acq": lambda org, date, _sum, agent, deal: AccMissingProfitAcq(org, date, _sum).make(agent, deal),
              "broken": lambda org, date, _sum, *_: AccBrokenProfit(org, date, _sum).make(),
              "broken_acq": lambda org, date, _sum, *_: AccBrokenProfitAcq(org, date, _sum).make(),
              "return25": lambda org, date, _sum, *_: AccReturns(org, date, _sum).make(),
              "return25_acq": lambda org, date, _sum, *_: AccReturnsAcq(org, date, _sum).make(),
              "return": lambda org, date, _sum, *_: AccVoluntaryReturns(org, date, _sum).make(),
              "return_acq": lambda org, date, _sum, *_: AccVoluntaryReturnsAcq(org, date, _sum).make(),
              "p_other": lambda org, date, _sum, agent, deal: AccOtherPrivilege(org, date, _sum).make(agent, deal),
              "state": lambda org, date, _sum, agent, deal: AccStatePrivilege(org, date, _sum).make(agent, deal),
              "federal": lambda org, date, _sum, agent, deal: AccFederalPrivilege(org, date, _sum).make(agent, deal),
              "srv_med": lambda org, date, _sum, agent, deal: AccMedService(org, date, _sum).make(agent, deal),
              "srv_tech": lambda org, date, _sum, agent, deal: AccTechService(org, date, _sum).make(agent, deal),
              "srv_parking": lambda org, date, _sum, agent, deal: AccParkingService(org, date, _sum).make(agent, deal),
              "fn_break": lambda org, date, _sum, agent, deal: AccBreakFine(org, date, _sum).make(agent, deal),
              "fn_late": lambda org, date, _sum, agent, deal: AccLateFine(org, date, _sum).make(agent, deal),
              "fn_equip": lambda org, date, _sum, agent, deal: AccEquipFine(org, date, _sum).make(agent, deal)}
exch = Queue()
logger = logging.getLogger(LOG_ALIAS)


def org():
    """ Функция хранит и возвращает код организации """
    return org.org


def receive(key, data):
    """ Прием сообщений
        Функция вызывается в потоках, запущенных в starter.py
    """
    if key in key_map:
        logger.debug(data)

        d_export, n_key = data.get('doc_date'), data.get('carrier')     # определение даты и контргагента
        doc_num = int(data.get('doc_num') or 0)     # номер договора с контрагентом
        _map = key_map[key]
        loads = []
        # подготовка данных к импорту, разбиение данных на отдельные порции
        for key, alias in _map.items():
            if (key in data) and (float(data[key] or 0) > 0):
                loads.append({'key': alias, 'carrier': n_key, 'doc_num': doc_num, 'reg_sum': data[key]})
        logger.debug(loads)
        exch.put((d_export, loads))
        del loads


def make_export(doc_date, lst_data):
    """ Импорт данных в 1С путем вызова необходимой lambda функции из action_map """
    logger.info("Start export")
    ret_list = []
    for item in lst_data:
        if item['key'] in action_map:
            ret_list.append(action_map[item['key']](org(), doc_date, item['reg_sum'], item.get('carrier'), item.get('doc_num')))
    logger.info("Complete")
    return ret_list


def work():
    """ Изъятие очередной записи из очереди и операция импорта """
    while True:
        try:
            d_export, loads = exch.get(block=True, timeout=5)
        except Empty:
            logging.info("Session closed")
            disconnect()
            time.sleep(5)
            continue

        logging.info("Start new task (%s)" % d_export)
        try:
            make_export(d_export, loads)
        except BaseException as b_exc:
            logger.error(b_exc)
        finally:
            exch.task_done()

def run():
    thr = Thread(target=work)
    thr.setDaemon(True)
    thr.start()
