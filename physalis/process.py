# -*- coding: utf-8 *-*
import clihelper

from motor import MotorClient
from tornado import ioloop


class DaemonProcess(clihelper.Controller):

    def _loop(self):
        self._ioloop = ioloop.IOLoop.instance()
        self._ioloop.start()

    def _process(self):
        self.db = MotorClient(self._get_config('db_uri')).open_sync()[
            self._get_config('db_name')]
        self.process()
        self._loop()

    def _shutdown(self):
        self._ioloop.stop()
