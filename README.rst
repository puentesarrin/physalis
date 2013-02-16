Physalis
********

Physalis is an e-mail notifier using entries and customizable user settings.
Physalis is written on top of Tornado, Motor & Pika using completely
asynchronous programming.


Requirements
============

* `MongoDB`_
* `RabbitMQ`_
* `CliHelper`_
* `Tornado`_
* `PyMongo`_
* `Motor`_
* `Pika`_
* `Schematics`_


Workflow
========

Physalis works with a very simple workflow:

#. Producers send data (users and entries) to RabbitMQ exchanges.

#. Physalis consumer (``physalisc``) consume data from RabbitMQ queues and save
   it into MongoDB collections.

#. Physalis processor (``physalisp``) process matching data (between users and
   entries), and send the results to a RabbitMQ exchange.

#. Physalis notifier (``physalisn``) consume data from RabbitMQ queue and send
   email messages via SMTP to users email addresses.


Components
==========

Physalis consumer (``physalisc``)
---------------------------------

Consumer component to save messages from two RabbitMQ queues (``users`` and
``entries``) to MongoDB collections validating *or not* customizables fields.

Messages from ``users`` queue must have the following basic format (`MongoDB
Extended JSON`_ or `BSON`_ are allowed):

* ``user_code``: Unique user code
* ``producer_code``: Unique producer code [1]_
* ``email``: User e-mail address
* ``settings``: Custom fields settings

E.g.::

    {
        user_code: "3455",
        producer_code: "5353454",
        email: "physalis@example.com",
        join: {
            $date: "2011-02-11T15:21:20"
        },
        settings: {
            category: "politics"
        }
    }

Messages from ``entries`` queue must have the following basic JSON format
(`MongoDB Extended JSON`_ or `BSON`_ are allowed):

* ``entry_code``: Unique entry code
* ``producer_code``: Unique producer code [1]_
* ``deadline``: Deadline date
* ``data``: Entry data
   * All of fields can be added, but these will be validated matching with
     producer fields settings

E.g.::

    {
        entry_code: "4535326",
        producer_code: "5353454",
        deadline: {
            $date: "2012-12-21T15:00:00"
        },
        data: {
            category: "politics",
            title: "Good news from southern country",
            subtitle: "Bonanza",
            content: "This is a very long text...",
            votes: 23.34
        }
    }

Physalis processor (``physalisp``)
----------------------------------

Processor component to match data and prepare to send the results to a RabbitMQ
exchange. These summaries includes filtered entries only.


Physalis notifier (``physalisn``)
---------------------------------

Notifier component to send email messages to users registered with the result
processed by Physalis processor.


.. [1] Producer code can be sent via ``app_id`` header of AMQP message. If
       ``producer_code`` field of AMQP message body has a value, this will
       overwrite the ``app_id`` header.

.. _MongoDB: http://www.mongodb.org
.. _RabbitMQ: http://www.rabbitmq.com
.. _CliHelper: https://github.com/gmr/clihelper
.. _Tornado: http://www.tornadoweb.org
.. _PyMongo: http://api.mongodb.org/python/current/
.. _Motor: https://github.com/mongodb/motor
.. _Pika: https://github.com/pika/pika
.. _Schematics: https://github.com/j2labs/schematics
.. _MongoDB Extended JSON: http://docs.mongodb.org/manual/reference/mongodb-extended-json/
.. _BSON: http://bsonspec.org
