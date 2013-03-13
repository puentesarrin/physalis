# -*- coding: utf-8 *-*
from motor import Op
from physalis.clients import AMQPClient, MongoDBClient
from physalis.process import DaemonProcess
from physalis.validators import (ConsumerUsersValidator,
                                 ConsumerEntriesValidator)
from tornado import gen


class PhysalisConsumer(DaemonProcess):

    users_label = 'users'
    entries_label = 'entries'
    channels = []

    def _set_properties(self):
        self.users_queue = self._get_config('amqp_%s_queue_name' %
            self.users_label)
        self.entries_queue = self._get_config('amqp_%s_queue_name' %
            self.entries_label)
        self.consume_users_enabled = self._get_config('consume_%s_enabled' %
            self.users_label)
        self.consume_entries_enabled = self._get_config('consume_%s_enabled' %
            self.entries_label)
        self.validators_map = {self.users_label: ConsumerUsersValidator,
                               self.entries_label: ConsumerEntriesValidator}

    def process(self):
        self._set_properties()
        self.db = MongoDBClient(self._get_config('db_name'),
            self._get_config('db_uri'), logger=self.logger)
        self.amqp = AMQPClient(self._get_config('amqp_uri'), self.logger,
            on_connected_callback=self._create_channels)

    def _create_channels(self):
        if self.consume_users_enabled:
            self.amqp_users = self._create_channel(self.users_label)
        if self.consume_entries_enabled:
            self.amqp_entries = self._create_channel(self.entries_label)

    def _create_channel(self, label):
        channel_client = self.amqp[self.users_label]
        channel_client.setup_and_consume(
            on_consuming_callback=self._consume_messages,
            consumer_tag=self._get_config('amqp_%s_consumer_tag' % label),
            queue_name=self._get_config('amqp_%s_queue_name' % label),
            queue_passive=self._get_config('amqp_%s_queue_passive' % label),
            queue_durable=self._get_config('amqp_%s_queue_durable' % label),
            queue_exclusive=self._get_config('amqp_%s_queue_exclusive' %
                label),
            queue_auto_delete=self._get_config('amqp_%s_queue_auto_delete' %
                label),
            noack=self._get_config('amqp_%s_queue_noack' % label))
        self.channels.append(channel_client)
        return channel_client

    @gen.engine
    def _consume_messages(self, header, body, channel_client):
        try:
            validator = self.validators_map[channel_client.label](header, body)
            message = validator.message
            collection_name = self._get_collection_name(channel_client.label,
                message['producer_code'])
            yield Op(self.db[collection_name].insert, message)
            self.logger.debug('Saved message to %s collection.' %
                collection_name)
        except Exception as e:
            self.logger.error(e.message, exc_info=True)

    def _get_collection_name(self, channel_name, producer_name):
        if self._get_config('db_%s_collection_per_producer' % channel_name):
            return ('%s.%s' % (self._get_config('db_%s_collection_name' %
                channel_name), producer_name))
        else:
            return self._get_config('db_%s_collection_name' % channel_name)

    def finish(self):
        for channel in self.channels:
            channel.cancel_consume()
        self.amqp.close()
