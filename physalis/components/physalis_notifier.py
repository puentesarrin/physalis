# -*- coding: utf-8 *-*
import logging

from physalis.process import DaemonProcess


logger = logging.getLogger('PhysalisNotifier')


class PhysalisNotifier(DaemonProcess):

    def process(self):
        pass
