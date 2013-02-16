# -*- coding: utf-8 *-*
from schematics.models import Model
from schematics.types import DateTimeType, DictType, EmailType, StringType


class UserModel(Model):

    user_code = StringType(required=True)
    producer_code = StringType()
    email = EmailType(required=True)
    settings = DictType(required=True)


class EntryModel(Model):

    entry_code = StringType(required=True)
    producer_code = StringType()
    deadline = DateTimeType(required=True)
    data = DictType(required=True)
