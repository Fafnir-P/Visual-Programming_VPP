import os, sys
d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isdir(os.path.join(d, 'card_templates')) and os.path.dirname(d) != d: d = os.path.dirname(d)
sys.path.insert(0, d)
import argparse
import json

from card_templates.runtime import Context, Store, CardError
from cards import enter_text, trim_whitespace, change_text_case, replace_text_in_field, enter_number, calculate_from_two_values, round_numeric_value, format_currency_value, change_value_by_percent, calculate_percentage_change, build_summary_record


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--customer', dest='f_t1', default=None)
    ap.add_argument('--qty', dest='f_a1', default=None)
    ap.add_argument('--price', dest='f_a2', default=None)
    ap.add_argument('--shipping', dest='f_b1', default=None)
    ap.add_argument('--handling', dest='f_b2', default=None)
    ap.add_argument('--old', dest='f_c1', default=None)
    ap.add_argument('--new', dest='f_c2', default=None)
    args = ap.parse_args()
    ctx = Context(store=Store())
    try:
        n_t1 = enter_text(ctx, value=args.f_t1, name='customer', label='Customer', required=False, max_length=100, placeholder='', help_text='')
        n_t2 = trim_whitespace(ctx, text=n_t1['value'])
        n_t3 = change_text_case(ctx, text=n_t2['text'], case='title')
        n_t4 = replace_text_in_field(ctx, text=n_t3['text'], find='-', replace=' ')
        n_t5 = trim_whitespace(ctx, text=n_t4['text'])
        n_a1 = enter_number(ctx, value=args.f_a1, name='qty', label='Qty', required=False, placeholder='', help_text='')
        n_a2 = enter_number(ctx, value=args.f_a2, name='price', label='Price', required=False, placeholder='', help_text='')
        n_a3 = calculate_from_two_values(ctx, first=n_a1['value'], second=n_a2['value'], operation='multiply', places=2)
        n_a4 = round_numeric_value(ctx, value=n_a3['result'], places=2)
        n_a5 = format_currency_value(ctx, value=n_a4['value'], symbol='$', separator=',', decimals=2)
        n_b1 = enter_number(ctx, value=args.f_b1, name='shipping', label='Shipping', required=False, placeholder='', help_text='')
        n_b2 = enter_number(ctx, value=args.f_b2, name='handling', label='Handling', required=False, placeholder='', help_text='')
        n_b3 = calculate_from_two_values(ctx, first=n_b1['value'], second=n_b2['value'], operation='add', places=2)
        n_b4 = change_value_by_percent(ctx, value=n_b3['result'], percent=10, direction='increase', places=2)
        n_b5 = round_numeric_value(ctx, value=n_b4['result'], places=2)
        n_b6 = format_currency_value(ctx, value=n_b5['value'], symbol='EUR ', separator=',', decimals=2)
        n_c1 = enter_number(ctx, value=args.f_c1, name='old', label='Old', required=False, placeholder='', help_text='')
        n_c2 = enter_number(ctx, value=args.f_c2, name='new', label='New', required=False, placeholder='', help_text='')
        n_c3 = calculate_percentage_change(ctx, old_value=n_c1['value'], new_value=n_c2['value'], places=2)
        n_c4 = round_numeric_value(ctx, value=n_c3['change'], places=1)
        n_b7 = build_summary_record(ctx, value_1=n_t5['text'], value_2=n_a5['text'], value_3=n_b6['text'], value_4=n_c4['value'], labels=['customer', 'total', 'with_shipping', 'change_pct'])
        result = n_b7['record']
    except (CardError, ValueError, ArithmeticError) as e:
        print((str(e).splitlines() or [type(e).__name__])[0], file=sys.stderr)
        sys.exit(1)
    print(json.dumps(result, default=str))


if __name__ == '__main__':
    main()
