# -*- coding: utf-8 *-*
import bson

from bson import json_util
from physalis import errors, models

__all__ = ['ConsumerUsersValidator', 'ConsumerEntriesValidator']


class Validator(object):

    def __init__(self):
        self.parser_methods = {
            'application/bson': self._parse_message_to_bson,
            'application/json': self._parse_message_to_json
        }

    def _parse_message(self, header, body):
        parser = self.parser_methods.get(header.content_type, None)
        if parser:
            return parser(body)
        raise errors.UnexpectedFormat(body)

    def _parse_message_to_bson(self, message_body):
        try:
            if not bson.is_valid(self.message_body):
                raise
            message = bson.decode_all(message_body)
            if not (isinstance(message, list) or len(message) == 1):
                raise ValueError('Received message must be an object, not '
                                 'a list.')
            return message[0]
        except:
            raise errors.InvalidBSON(message_body)

    def _parse_message_to_json(self, message_body):
        try:
            message = json_util.loads(message_body)
            if not isinstance(message, dict):
                raise ValueError('Received message must be an object, not '
                                 'a list.')
            return message
        except:
            raise errors.InvalidJSON(message_body)


class ConsumerValidator(Validator):

    def __init__(self, header, body):
        self.message_header = header
        self.message_body = body
        super(ConsumerValidator, self).__init__()

    def _validate_headers(self):
        for header in self.headers:
            if not getattr(self.message_header, header, None):
                raise ValueError('%s header message no received.' % header)

    def _build_message(self):
        self.__message = self._parse_message(self.message_header,
            self.message_body)
        if not 'producer_code' in self.__message:
            if not getattr(self.message_header, 'app_id', None):
                raise ValueError("Producer code doesn't exists on message "
                                 "body or header.")
            else:
                self.__message['producer_code'] = self.message_header.app_id

    def _validate_model(self):
        try:
            self.model(**self.__message).validate()
        except Exception as e:
            raise errors.InvalidModel(e.reason, self.__message)

    def validate_and_build_message(self):
        self._validate_headers()
        self._build_message()
        self._validate_model()

    @property
    def message(self):
        if not hasattr(self, '__message'):
            self.validate_and_build_message()
        return self.__message


class ConsumerUsersValidator(ConsumerValidator):

    headers = []
    model = models.UserModel


class ConsumerEntriesValidator(ConsumerValidator):

    headers = []
    model = models.EntryModel
