# -*- coding: utf-8 *-*
import logging


class MongoDBClient(object):

    def __init__(self, db_name, **kwargs):
        self.db_name = db_name
        self._logger = kwargs.get('logger') or logging.getLogger(
            self.__class__.__name__)
        self._setup_config(**kwargs)

    def _setup_config(self, **kwargs):
        self._uri = kwargs.get('uri', 'mongodb://localhost/?safe=true')
