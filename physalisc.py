# -*- coding: utf-8 *-*
import clihelper

from physalis import PhysalisConsumer


def main():
    clihelper.setup('PhysalisConsumer', 'Physalis Consumer component to save '
        'messages from two RabbitMQ queues to MongoDB collections.', '0.0.1')
    clihelper.run(PhysalisConsumer)

if __name__ == "__main__":
    main()
