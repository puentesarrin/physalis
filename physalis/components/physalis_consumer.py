# -*- coding: utf-8 *-*
from motor import MotorClient, Op
from physalis.clients import AMQPClient
from physalis.process import DaemonProcess
from physalis.validators import (ConsumerUsersValidator,
                                 ConsumerEntriesValidator)
from tornado import gen


class PhysalisConsumer(DaemonProcess):

    def process(self):
        self.tag_users = 'users'
        self.tag_entries = 'entries'
        self.validators_map = {self.tag_users: ConsumerUsersValidator,
                               self.tag_entries: ConsumerEntriesValidator}
        self.db = self.db_connect()
        self.users_amqp_client = AMQPClient(callback=self._consume_messages,
            tag=self.tag_users,
            queue_name=self._get_config('amqp_users_queue_name'),
            consumer_tag=self._get_config('amqp_users_consumer_tag'),
            logger=self.logger, uri=self._get_config('amqp_uri'),
            queue_passive=self._get_config('amqp_users_queue_passive'),
            queue_durable=self._get_config('amqp_users_queue_durable'),
            queue_exclusive=self._get_config('amqp_users_queue_exclusive'),
            queue_auto_delete=self._get_config('amqp_users_queue_auto_delete'),
            noack=self._get_config('amqp_users_queue_noack'))
        self.entries_amqp_client = AMQPClient(callback=self._consume_messages,
            tag=self.tag_entries,
            queue_name=self._get_config('amqp_entries_queue_name'),
            consumer_tag=self._get_config('amqp_entries_consumer_tag'),
            logger=self.logger, uri=self._get_config('amqp_uri'),
            queue_passive=self._get_config('amqp_entries_queue_passive'),
            queue_durable=self._get_config('amqp_entries_queue_durable'),
            queue_exclusive=self._get_config('amqp_entries_queue_exclusive'),
            queue_auto_delete=self._get_config(
                'amqp_entries_queue_auto_delete'),
            noack=self._get_config('amqp_entries_queue_noack'))

    def db_connect(self):
        return MotorClient(self._get_config('db_uri')).open_sync()[
            self._get_config('db_name')]

    @gen.engine
    def _consume_messages(self, header, body, tag):
        try:
            validator = self.validators_map[tag](self, header, body)
            message = validator.message
            collection_name = self._get_collection_name(tag,
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
        self.users_amqp_client.close()
        self.entries_amqp_client.close()
