# -*- coding: utf-8 *-*
import logging
import pika

from pika.adapters.tornado_connection import TornadoConnection


class AMQPClient(object):

    def __init__(self, callback, tag, queue_name, consumer_tag, **kwargs):
        self._callback = callback
        self._tag = tag
        self._queue_name = queue_name
        self._consumer_tag = consumer_tag
        self._logger = kwargs.get('logger') or logging.getLogger(
            self.__class__.__name__)
        self._setup_config(**kwargs)
        self._amqp_connect()
        self._channel = None

    @property
    def tag(self):
        return self._tag

    @property
    def uri(self):
        return self._uri

    @property
    def connection(self):
        return self._connection

    def _setup_config(self, **kwargs):
        self._uri = kwargs.get('uri', 'amqp://guest:guest@localhost:5672/%2f')
        self._queue_passive = kwargs.get('queue_passive', False)
        self._queue_durable = kwargs.get('queue_durable', True)
        self._queue_exclusive = kwargs.get('queue_exclusive', False)
        self._queue_auto_delete = kwargs.get('queue_auto_delete', False)
        self._noack = kwargs.get('noack', True)

    def _amqp_connect(self):
        self._connection = TornadoConnection(pika.URLParameters(self.uri),
            on_open_callback=self._on_amqp_opened)

    def _on_amqp_opened(self, connection):
        self._logger.debug('AMQP connection opened "%s"' % self.tag)
        self.connection.add_on_close_callback(self._on_connection_closed)
        connection.channel(self._on_channel_open)

    def _on_connection_closed(self, connection):
        #TODO: Log disconnection details...
        #self.log.warning('Server closed connection, reopening: (%s) %s',
                         #method_frame.method.reply_code,
                         #method_frame.method.reply_text)
        #self.log.debug(connection._is_method_frame())
        self._connection = self._amqp_connect()

    def _on_channel_open(self, new_channel):
        self._channel = new_channel
        self._channel.queue_declare(self._on_queue_declare,
            queue=self._queue_name, passive=self._queue_passive,
            durable=self._queue_durable, exclusive=self._queue_exclusive,
            auto_delete=self._queue_auto_delete)

    def _on_queue_declare(self, frame):
        self._channel.basic_consume(self._consume_messages,
            queue=self._queue_name, no_ack=self._noack,
            consumer_tag=self._consumer_tag)

    def _consume_messages(self, channel, method, header, body):
        self._logger.debug('Received message from "%s" tag: %s' % (self.tag,
            body))
        self._callback(header, body, self.tag)

    def close(self):
        self._logger.debug('Sending a Basic.Cancel RPC command to AMQP server '
            '"%s"' % self.tag)
        self._channel.basic_cancel(self.on_cancelok, self._consumer_tag)

    def on_cancelok(self, unused_frame):
        self._logger.debug('Closing AMQP connection "%s"' % self.tag)
        self._connection.close()
