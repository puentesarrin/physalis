# -*- coding: utf-8 *-*
import logging
import pika

from pika.adapters.tornado_connection import TornadoConnection


class AMQPClient(object):

    def __init__(self, uri='amqp://guest:guest@localhost:5672/%2f',
        logger=None, on_connected_callback=None):
        self._uri = uri
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
        return AMQPChannelClient(self, name)

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
        self._logger.debug('Closing AMQP connection')
        self._connection.close()


class AMQPChannelClient(object):

    _configured = False
    _subscribed = False

    def __init__(self, client, label, **kwargs):
        self._client = client
        self._logger = client._logger
        self._label = label

    @property
    def label(self):
        return self._label

    @property
    def queue_name(self):
        return self._queue_name

    @property
    def configured(self):
        return self._configured

    @property
    def subscribed(self):
        return self._subscribed

    def setup(self, consumer_tag, queue_name, **kwargs):
        self._consumer_tag = consumer_tag
        self._queue_name = queue_name
        self._queue_passive = kwargs.get('queue_passive', False)
        self._queue_durable = kwargs.get('queue_durable', True)
        self._queue_exclusive = kwargs.get('queue_exclusive', False)
        self._queue_auto_delete = kwargs.get('queue_auto_delete', False)
        self._noack = kwargs.get('noack', True)
        self._configured = True

    def consume(self, on_consuming_callback):
        self._on_consuming_callback = on_consuming_callback
        self._client.create_channel(self._on_channel_open)

    def setup_and_consume(self, on_consuming_callback, consumer_tag,
        queue_name, **kwargs):
        self.setup(consumer_tag, queue_name, **kwargs)
        self.consume(on_consuming_callback)

    def _on_channel_open(self, new_channel):
        self._logger.debug('AMQP channel opened for "%s" queue' %
            self.queue_name)
        self._channel = new_channel
        self._channel.queue_declare(self._on_queue_declare,
            queue=self._queue_name, passive=self._queue_passive,
            durable=self._queue_durable, exclusive=self._queue_exclusive,
            auto_delete=self._queue_auto_delete)

    def _on_queue_declare(self, frame):
        self._channel.basic_consume(self._consume_messages,
            queue=self._queue_name, no_ack=self._noack,
            consumer_tag=self._consumer_tag)
        self._logger.debug('Waiting for messages from "%s" queue' %
            self.queue_name)
        self._subscribed = True

    def _consume_messages(self, channel, method, header, body):
        self._logger.debug('Received message from "%s" queue: %s' %
            (self.queue_name, body))
        self._on_consuming_callback(header, body, self)

    def cancel_consume(self, on_cancel_consuming_callback=None):
        self._logger.debug('Sending Basic.Cancel to AMQP channel "%s"' %
            self.queue_name)
        self._on_cancel_consuming_callback = on_cancel_consuming_callback
        self._channel.basic_cancel(self._on_cancelok, self._consumer_tag)

    def _on_cancelok(self, unused_frame):
        self._subscribed = False
        self._logger.debug('Cancelled consuming to AMQP channel "%s"' %
            self.queue_name)
        if not self.on_cancel_consuming_callback:
            self.on_cancel_consuming_callback()
