# -*- coding: utf-8 *-*
import logging

from motor import MotorClient


class MongoDBClient(object):

    def __init__(self, db_name, uri=None, **kwargs):
        self._db_name = db_name
        self._uri = uri or 'mongodb://localhost:27017'
        self._logger = kwargs.get('logger') or logging.getLogger(
            self.__class__.__name__)
        self._connection = MotorClient(self.uri).open_sync()[self.db_name]
        self._logger.debug('MongoDB connection opened')

    @property
    def uri(self):
        return self._uri

    @property
    def db_name(self):
        return self._db_name

    @property
    def connection(self):
        return self._connection

    def __getattr__(self, name):
        return self.connection[name]

    def __getitem__(self, name):
        return self.__getattr__(name)
