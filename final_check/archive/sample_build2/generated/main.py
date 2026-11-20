import argparse
import json

from card_templates.runtime import Context, Store
from cards import (enter_text, trim_whitespace, change_text_case,
                   check_field_is_required, show_message_banner)

parser = argparse.ArgumentParser()
parser.add_argument('--text', default=None)
args = parser.parse_args()

ctx = Context(store=Store())

r2 = enter_text(ctx, value=args.text, name='text', label='Text', required=False, max_length=100, placeholder='', help_text='')
r3 = trim_whitespace(ctx, text=r2['value'])
r4 = change_text_case(ctx, text=r3['text'], case='upper')
r5 = check_field_is_required(ctx, value=r4['text'], field='value')
r6 = show_message_banner(ctx, message=r5['value'], variant='info', dismissible=True, icon='')

print(json.dumps(r6['view'], indent=2))
