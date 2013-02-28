# -*- coding: utf-8 *-*
import logging
import pika

from motor import MotorClient, Op
from physalis.process import DaemonProcess
from physalis.validators import (ConsumerUsersValidator,
                                 ConsumerEntriesValidator)
from pika.adapters.tornado_connection import TornadoConnection
from tornado import gen


class PhysalisConsumer(DaemonProcess):

    def _setup(self):
        self.log = logging.getLogger('PhysalisConsumer')

    def process(self):
        self.amqp_channels = {}
        self.amqp_channels_map = {1: 'users', 2: 'entries'}
        self.validators_map = {'users': ConsumerUsersValidator,
                               'entries': ConsumerEntriesValidator}
        self.db = self.db_connect()
        self.amqp = self.amqp_connect()

    def db_connect(self):
        return MotorClient(self._get_config('db_uri')).open_sync()[
            self._get_config('db_name')]

    def amqp_connect(self):
        return TornadoConnection(
            parameters=pika.URLParameters(self._get_config('amqp_uri')),
            on_open_callback=self._on_amqp_opened)

    @gen.engine
    def _consume_messages(self, channel, method, header, body):
        try:
            channel_name = self.amqp_channels_map[channel.channel_number]
            self.log.debug('Received message from %s channel: %s' % (
                channel_name, body))
            validator = self.validators_map[channel_name](self, header, body)
            message = validator.message
            collection_name = self._get_collection_name(channel_name,
                message['producer_code'])
            yield Op(self.db[collection_name].insert, message)
            self.log.debug('Saved message to %s collection.' % collection_name)
        except Exception as e:
            self.log.error(e.message, exc_info=True)

    def _get_collection_name(self, channel_name, producer_name):
        if self._get_config('db_%s_collection_per_producer' % channel_name):
            return ('%s.%s' % (self._get_config('db_%s_collection_name' %
                channel_name), producer_name))
        else:
            return self._get_config('db_%s_collection_name' % channel_name)

    def _on_amqp_opened(self, connection):
        self.log.debug('AMQP connection opened')
        self.amqp.add_on_close_callback(self.on_connection_closed)
        connection.channel(self._on_channel_open)
        connection.channel(self._on_channel_open)

    def on_connection_closed(self, connection):
        #TODO: Log disconnection details...
        #self.log.warning('Server closed connection, reopening: (%s) %s',
                         #method_frame.method.reply_code,
                         #method_frame.method.reply_text)
        #self.log.debug(connection._is_method_frame())
        self.amqp_channels = {}
        self.amqp = self.amqp_connect()

    def _on_channel_open(self, new_channel):
        channel_name = self.amqp_channels_map[new_channel.channel_number]
        self.amqp_channels[channel_name] = new_channel
        self.amqp_channels[channel_name].queue_declare(self._on_queue_declare,
            queue=self._get_config('amqp_%s_queue_name' % channel_name),
            passive=self._get_config('amqp_%s_queue_passive' % channel_name),
            durable=self._get_config('amqp_%s_queue_durable' % channel_name),
            exclusive=self._get_config('amqp_%s_queue_exclusive' %
                channel_name),
            auto_delete=self._get_config('amqp_%s_queue_auto_delete' %
                channel_name))

    def _on_queue_declare(self, frame):
        channel_name = self.amqp_channels_map[frame.channel_number]
        self.amqp_channels[channel_name].basic_consume(self._consume_messages,
            queue=self._get_config('amqp_%s_queue_name' % channel_name),
            no_ack=self._get_config('amqp_%s_noack' % channel_name),
            consumer_tag=self._get_config('amqp_%s_consumer_tag' %
                channel_name))

    def on_cancelok(self, unused_frame):
        self.log.debug('Closing AMQP connection')
        self.amqp.close()

    def finish(self):
        self.log.debug('Sending a Basic.Cancel RPC command to AMQP server')
        for channel_name in self.amqp_channels:
            self.log.debug(channel_name)
            self.amqp_channels[channel_name].basic_cancel(self.on_cancelok,
                self._get_config('amqp_%s_consumer_tag' % channel_name))
