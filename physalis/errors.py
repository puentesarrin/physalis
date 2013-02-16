# -*- coding: utf-8 *-*


class PhysalisError(Exception):
    pass


class BadFormat(PhysalisError):

    def __init__(self, message, message_queue):
        self.message_queue = message_queue
        super(BadFormat, self).__init__(message)


class InvalidModel(PhysalisError):

    def __init__(self, message, message_queue):
        self.message_queue = message_queue
        super(InvalidModel, self).__init__(message)


class InvalidJSONFormat(BadFormat):

    def __init__(self, message_queue):
        super(InvalidJSONFormat, self).__init__(
            'Unsupported JSON message received.', message_queue)


class InvalidBSONFormat(BadFormat):

    def __init__(self, message_queue):
        super(InvalidBSONFormat, self).__init__(
            'Unsupported BSON message received.', message_queue)


class UnexpectedFormat(BadFormat):

    def __init__(self, message_queue):
        super(UnexpectedFormat, self).__init__(
            'Unsupported format from message received.', message_queue)
