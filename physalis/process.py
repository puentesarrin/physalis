# -*- coding: utf-8 *-*
import clihelper
import logging

from tornado import ioloop


class DaemonProcess(clihelper.Controller):

    def _setup(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def start_loop(self):
        self.logger.debug('Starting IOLoop')
        self._ioloop = ioloop.IOLoop.instance()
        self._ioloop.start()

    def _process(self):
        self.process()
        self.start_loop()

    def process(self):
        raise NotImplementedError

    def _cleanup(self):
        self.finish()
        self.stop_loop()

    def finish(self):
        pass

    def stop_loop(self):
        self.logger.debug('Stopping IOLoop')
        self._ioloop.stop()
