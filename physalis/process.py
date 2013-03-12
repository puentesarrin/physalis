# -*- coding: utf-8 *-*
import clihelper
import logging

from tornado import ioloop


class DaemonProcess(clihelper.Controller):

    def _setup(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.ioloop = ioloop.IOLoop.instance()

    def start_loop(self):
        self.logger.debug('Starting IOLoop')
        self.ioloop.start()

    def _process(self):
        self.process()
        self.start_loop()

    def process(self):
        raise NotImplementedError

    def _shutdown(self):
        self.stop_loop()
        self.finish()

    def finish(self):
        pass

    def stop_loop(self):
        self.logger.debug('Stopping IOLoop')
        self.ioloop.stop()
