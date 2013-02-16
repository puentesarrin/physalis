# -*- coding: utf-8 *-*
import bson

from bson import json_util
from physalis import errors, models


class Validator(object):

    def __init__(self):
        pass

    def is_valid(self):
        pass


class ConsumerValidator(Validator):

    def __init__(self, process, header, body):
        self.process = process
        self.message_header = header
        self.message_body = body
        super(ConsumerValidator, self).__init__()

    def _validate_headers(self):
        for header in self.headers:
            if not getattr(self.message_header, header, None):
                raise ValueError('%s header message no received.' % header)

    def _parse_message(self):
        if self.message_header.content_type == 'application/json':
            try:
                message = json_util.loads(self.message_body)
                if not isinstance(message, dict):
                    raise ValueError('Received message must be an object, no '
                                     'a list of objects.')
                self.__message = message
            except:
                raise errors.InvalidJSON(self.message_body)
        elif bson.is_valid(self.message_body):
            try:
                message = bson.decode_all(self.message_body)
                if not (isinstance(message, list) or len(message) == 1):
                    raise ValueError('Received message must be an object, no '
                                     'a list of objects.')
                self.__message = message[0]
            except:
                raise errors.InvalidBSON(self.message_body)
        else:
            raise errors.UnexpectedFormat(self.message_body)
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

    def validate(self):
        self._validate_headers()
        self._parse_message()
        self._validate_model()

    @property
    def message(self):
        if not hasattr(self, '__message'):
            self.validate()
        return self.__message


class ConsumerUsersValidator(ConsumerValidator):

    headers = []
    model = models.UserModel


class ConsumerEntriesValidator(ConsumerValidator):

    headers = []
    model = models.EntryModel
