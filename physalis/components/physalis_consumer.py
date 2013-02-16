# -*- coding: utf-8 *-*
import logging
import pika

from motor import Op
from physalis.process import DaemonProcess
from physalis.validators import (ConsumerUsersValidator,
                                ConsumerEntriesValidator)
from pika.adapters.tornado_connection import TornadoConnection
from tornado import gen

logger = logging.getLogger('PhysalisConsumer')


class PhysalisConsumer(DaemonProcess):

    def process(self):
        self.amqp_channels = {}
        self.amqp_channels_map = {1: 'users', 2: 'entries'}
        self.validators_map = {'users': ConsumerUsersValidator,
            'entries': ConsumerEntriesValidator}
        self.amqp = TornadoConnection(
            parameters=pika.URLParameters(self._get_config('amqp_uri')),
            on_open_callback=self._on_amqp_opened)

    @gen.engine
    def _consume_messages(self, channel, method, header, body):
        try:
            channel_name = self.amqp_channels_map[channel.channel_number]
            logger.debug('Received message from %s channel: %s' % (
                channel_name, body))
            validator = self.validators_map[channel_name](self, header, body)
            message = validator.message
            collection_name = self._get_collection_name(channel_name,
                message['producer_code'])
            yield Op(self.db[collection_name].insert, message)
            logger.debug('Saved message to %s collection.' % collection_name)
        except Exception as e:
            logger.error(e.message, exc_info=True)

    def _get_collection_name(self, channel_name, producer_name):
        if self._get_config('db_%s_collection_per_producer' % channel_name):
            return (self._get_config('db_%s_collection_name' % channel_name) +
                '.%s' % producer_name)
        else:
            return self._get_config('db_%s_collection_name' % channel_name)

    def _on_amqp_opened(self, connection):
        connection.channel(self._on_channel_open)
        connection.channel(self._on_channel_open)

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
