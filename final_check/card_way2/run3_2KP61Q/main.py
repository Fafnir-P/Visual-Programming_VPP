import os, sys
d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isdir(os.path.join(d, 'card_templates')) and os.path.dirname(d) != d: d = os.path.dirname(d)
sys.path.insert(0, d)
import argparse
import json

from card_templates.runtime import Context, Store, CardError
from cards import enter_text, trim_whitespace, change_text_case, check_field_is_required, enter_number, calculate_from_two_values, format_currency_value, build_summary_record


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--customer', dest='f_n2', default=None)
    ap.add_argument('--qty', dest='f_n6', default=None)
    ap.add_argument('--price', dest='f_n7', default=None)
    args = ap.parse_args()
    ctx = Context(store=Store())
    try:
        n_n2 = enter_text(ctx, value=args.f_n2, name='customer', label='Customer', required=False, max_length=100, placeholder='', help_text='')
        n_n3 = trim_whitespace(ctx, text=n_n2['value'])
        n_n4 = change_text_case(ctx, text=n_n3['text'], case='title')
        n_n5 = check_field_is_required(ctx, value=n_n4['text'], field='customer')
        n_n6 = enter_number(ctx, value=args.f_n6, name='qty', label='Qty', required=False, placeholder='', help_text='')
        n_n7 = enter_number(ctx, value=args.f_n7, name='price', label='Price', required=False, placeholder='', help_text='')
        n_n8 = calculate_from_two_values(ctx, first=n_n6['value'], second=n_n7['value'], operation='multiply', places=2)
        n_n9 = format_currency_value(ctx, value=n_n8['result'], symbol='$', separator=',', decimals=2)
        n_n10 = build_summary_record(ctx, value_1=n_n5['value'], value_2=n_n9['text'], labels=['customer', 'total'])
        result = n_n10['record']
    except (CardError, ValueError, ArithmeticError) as e:
        print((str(e).splitlines() or [type(e).__name__])[0], file=sys.stderr)
        sys.exit(1)
    print(json.dumps(result, default=str))


if __name__ == '__main__':
    main()
