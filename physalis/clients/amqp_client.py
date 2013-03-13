# -*- coding: utf-8 *-*
import logging
import pika

from physalis.clients.amqp_channel_client import AMQPChannelClient
from pika.adapters.tornado_connection import TornadoConnection


class AMQPClient(object):

    channels = {}

    def __init__(self, uri, logger, on_connected_callback=None):
        self._uri = uri or 'amqp://guest:guest@localhost:5672/%2f'
        self._logger = logger or logging.getLogger(self.__class__.__name__)
        self._on_connected_callback = on_connected_callback
        self._amqp_connect()

    @property
    def uri(self):
        return self._uri

    @property
    def connection(self):
        return self._connection

    def __getattr__(self, name):
        if name in self.channels.keys():
            return self.channels[name]
        self.channels[name] = AMQPChannelClient(self, name)
        return self.channels[name]

    def __getitem__(self, name):
        return self.__getattr__(name)

    def create_channel(self, on_channel_open):
        return self._connection.channel(on_channel_open)

    def _amqp_connect(self):
        self._connection = TornadoConnection(pika.URLParameters(self.uri),
            on_open_callback=self._on_amqp_opened, stop_ioloop_on_close=True)

    def _on_amqp_opened(self, connection):
        self._logger.debug('AMQP connection opened')
        self.connection.add_on_close_callback(self._on_connection_closed)
        if self._on_connected_callback:
            self._on_connected_callback()

    def _on_connection_closed(self, connection):
        #TODO: Log disconnection details...
        #self.log.warning('Server closed connection, reopening: (%s) %s',
                         #method_frame.method.reply_code,
                         #method_frame.method.reply_text)
        #self.log.debug(connection._is_method_frame())
        self._connection = self._amqp_connect()

    def close(self):
        for channel in self.channels.values():
            channel.cancel_consume()
        self._logger.debug('Closing AMQP connection')
        self._connection.close()
