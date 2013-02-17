# -*- coding: utf-8 *-*
import clihelper

from physalis import PhysalisNotifier


def main():
    clihelper.setup('PhysalisNotifier', 'Physalis Notifier component to send '
        'email messages to users registered with a summary including filtered '
        'entries.', '0.0.1')
    clihelper.run(PhysalisNotifier)

if __name__ == "__main__":
    main()
