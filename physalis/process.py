# -*- coding: utf-8 *-*
import clihelper

from tornado import ioloop


class DaemonProcess(clihelper.Controller):

    def start_loop(self):
        self.log.debug('Starting IOLoop')
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
        self.log.debug('Stopping IOLoop')
        self._ioloop.stop()
