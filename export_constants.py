import logging

HOST = 'XXX.XXX.XXX.XXX'
SERVICE_PORT = XXXXX

V82CONN_STRING = 'File="XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX";Usr="XXXXXXXXXXXXXXXXXXXXX";Pwd="*******************************";'

ORG = XX
CH_NAME = 'EXPORT'

CONN_MAP = {'test': ('File="XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX";Usr="XXXXXXXXXXXXXXXXXXXXX";Pwd="*******************************";', XX, 'TEST_EXPORT'),
            'prod': ('File="XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX";Usr="XXXXXXXXXXXXXX";Pwd="******************";', XX, 'EXPORT'),
            }

DEFAULT = 'test'

LOG_ALIAS = "1CExport"
LOG_FILENAME = 'log\\Export.log'
LOG_LEVEL = logging.DEBUG

RECEIVE_CHANNELS = {'rmq': True, 'rpyc': True}
EXPORT_KEYS = ('general', 'general_acq', 'clean', 'clean_acq', 'return', 'return_acq',
               'broken', 'broken_acq', 'missing', 'missing_acq', 'state', 'p_other',
               'federal', 'services', 'fines')
