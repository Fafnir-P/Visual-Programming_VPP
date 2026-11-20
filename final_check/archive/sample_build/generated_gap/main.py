"""Generated from the card graph. Run order: n1 .. n8 (see request.json "order")."""
import os
import sys

# card_templates (the shared runtime) lives two folders up from this file.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

import json

from card_templates.runtime import CardError, Context, Store
from cards import (app_end, app_start, calculate_from_two_values, enter_number,
                   format_currency_value, show_message_banner, validate_number_range)

# GAP: the Enter Number cards (n2, n3) have no value source in the graph (their optional
# "value" input is not linked and the card has no setting for it). The numbers a user
# would type are given here so the program can run. Set an entry to None to leave it empty.
USER_ENTRIES = {'n2': 12.5, 'n3': 7.25}

# Links used (edges): e1 n2.value->n4.first, e2 n3.value->n4.second, e3 n4.result->n5.value,
# e4 n5.value->n6.value, e5 n6.text->n7.message, e6 n1.event->n8.finish


def main():
    ctx = Context(store=Store())
    n1 = app_start(ctx, description='App starts')
    n2 = enter_number(ctx, value=USER_ENTRIES['n2'], name='number', label='Number', required=False,
                      min_value=None, max_value=None, placeholder='', help_text='')
    n3 = enter_number(ctx, value=USER_ENTRIES['n3'], name='number', label='Number', required=False,
                      min_value=None, max_value=None, placeholder='', help_text='')
    n4 = calculate_from_two_values(ctx, first=n2['value'], second=None, operation='add', places=2)
    n5 = validate_number_range(ctx, value=n4['result'], field='value', min=None, max=None)
    n6 = format_currency_value(ctx, value=n5['value'], symbol='$', separator=',', decimals=2)
    n7 = show_message_banner(ctx, message=n6['text'], variant='info', dismissible=True, icon='')
    print(json.dumps(n7['view'], indent=2))
    app_end(ctx, finish=n1['event'], message='The app has finished')
    return n6['text']


if __name__ == '__main__':
    try:
        print('RESULT:', main())
    except CardError as e:
        print('CARD ERROR', e.code if hasattr(e, 'code') else '', '-', e)
        sys.exit(1)

