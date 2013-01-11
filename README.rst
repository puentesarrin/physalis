Physalis
********

Physalis is a e-mail notifier using entries and customizable user settings.


Workflow
========

Physalis works with a very simple workflow:

#. Producers send data (users and entries) to RabbitMQ queues.

#. Physalis consumer (physalisc) consume data and save it into MongoDB
   collections.

#. Physalis notifier (physalisn) process data and send email messages via SMTP
   to users email addresses.


Components
==========

Physalis consumer (physalisc)
-----------------------------

Consumer component to save messages from two RabbitMQ queues (``users`` and
``entries``) to MongoDB collections validating *or not* customizables fields.

Messages from ``users`` queue must have the following basic JSON format:

* ``user_code``: Unique user code
* ``producer_code``: Unique producer code
* ``email``: User e-mail address
* ``settings``: Custom fields settings

E.g.::

    {
        user_code: "3455",
        producer_code: "5353454",
        email: "physalis@example.com",
        join: "2011-02-11T15:21:20",
        settings: {
            category: "politics"
        }
    }

Messages from ``entries`` queue must have the following basic JSON format:

* ``entry_code``: Unique entry code
* ``producer_code``: Unique producer code
* ``data``: Entry data
   * ``deadline``: Deadline date
   * Others fields can be added, but these will be validated matching with
     producer fields settings

E.g.::

    {
        entry_code: "4535326",
        producer_code: "5353454",
        data: {
            category: "politics",
            title: "Good news from southern country",
            subtitle: "Bonanza",
            content: "This is a very long text...",
            votes: 23.34,
            deadline: "2012-12-21T15:00:00"
        }
    }


Physalis notifier (physalisn)
-----------------------------

Notifier component to send email messages to users registered with a summary
including filtered entries.
