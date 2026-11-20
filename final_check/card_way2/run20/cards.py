# cards.py: written by the app from the card templates. Do not edit by hand.


from card_templates.runtime import CardError, as_text, coerce_value, round_half_up, to_number, view


def enter_text(ctx, *, value=None, name: str='text', label: str='Text', required: bool=False, max_length: int=100, placeholder: str='', help_text: str='') -> dict:
    spec = {'type': 'text', 'required': required, 'max_length': max_length}
    clean = coerce_value(spec, value, label)
    node = view('input.text', id=name, label=label, value=clean or '', required=required, maxLength=max_length, placeholder=placeholder, help=help_text)
    return {'view': node, 'value': clean}


def trim_whitespace(ctx, *, text) -> dict:
    s = as_text(text, 'text')
    return {'text': s.strip()}


def change_text_case(ctx, *, text, case: str='upper') -> dict:
    s = as_text(text, 'text')
    if case == 'upper':
        return {'text': s.upper()}
    if case == 'lower':
        return {'text': s.lower()}
    if case == 'title':
        return {'text': s.title()}
    raise CardError('invalid_input', f'Case must be upper, lower or title (got {case!r}).')


def replace_text_in_field(ctx, *, text, find: str, replace: str='') -> dict:
    s = as_text(text, 'text')
    if not isinstance(find, str) or find == '':
        raise CardError('invalid_input', 'Say which text to find.')
    return {'text': s.replace(find, replace)}


def enter_number(ctx, *, value=None, name: str='number', label: str='Number', required: bool=False, min_value=None, max_value=None, placeholder: str='', help_text: str='') -> dict:
    spec = {'type': 'number', 'required': required, 'min': min_value, 'max': max_value}
    clean = coerce_value(spec, value, label)
    node = view('input.number', id=name, label=label, value=clean, required=required, min=min_value, max=max_value, placeholder=placeholder, help=help_text)
    return {'view': node, 'value': clean}


def calculate_from_two_values(ctx, *, first, second, operation: str='add', places: int=2) -> dict:
    a = to_number(first, 'first')
    b = to_number(second, 'second')
    if operation == 'add':
        result = a + b
    elif operation == 'subtract':
        result = a - b
    elif operation == 'multiply':
        result = a * b
    elif operation == 'divide':
        if b == 0:
            raise CardError('divide_by_zero', 'Cannot divide by zero.')
        result = a / b
    else:
        raise CardError('invalid_input', f'Unknown operation: {operation}. Use add, subtract, multiply or divide.')
    return {'result': round_half_up(result, places)}


def round_numeric_value(ctx, *, value, places: int=2) -> dict:
    num = to_number(value, 'value')
    return {'value': round_half_up(num, places)}


def format_currency_value(ctx, *, value, symbol: str='$', separator: str=',', decimals: int=2) -> dict:
    num = round_half_up(to_number(value, 'value'), decimals)
    sign = '-' if num < 0 else ''
    num = abs(num)
    parts = f'{num:.{decimals}f}'.split('.')
    whole = parts[0]
    if separator:
        whole = f'{int(whole):,}'.replace(',', separator)
    text = f'{sign}{symbol}{whole}.{parts[1]}'
    return {'text': text}


def change_value_by_percent(ctx, *, value, percent, direction: str='increase', places: int=2) -> dict:
    val = to_number(value, 'value')
    pct = to_number(percent, 'percent')
    if pct < 0:
        raise CardError('too_small', 'Percent cannot be negative.')
    if direction not in ('increase', 'decrease'):
        raise CardError('invalid_input', f'Direction must be increase or decrease, not {direction}.')
    change = val * (pct / 100)
    result = val + change if direction == 'increase' else val - change
    return {'result': round_half_up(result, places)}


def calculate_percentage_change(ctx, *, old_value, new_value, places: int=2) -> dict:
    old = to_number(old_value, 'old_value')
    new = to_number(new_value, 'new_value')
    if old == 0:
        raise CardError('divide_by_zero', 'Cannot calculate percentage change: old value is zero.')
    change = (new - old) / old * 100
    return {'change': round_half_up(change, places)}


def build_summary_record(ctx, *, value_1=None, value_2=None, value_3=None, value_4=None, labels: list | None=None) -> dict:
    if labels is not None and (not isinstance(labels, list) or not all((isinstance(x, str) and x.strip() for x in labels))):
        raise CardError('invalid_input', 'Labels must be a list of texts.')
    names = [labels[i].strip() if labels and i < len(labels) else f'Value {i + 1}' for i in range(4)]
    values = [value_1, value_2, value_3, value_4]
    used = [(n, v) for n, v in zip(names, values) if v is not None]
    if not used:
        raise CardError('required', 'Link at least one value.')
    seen = set()
    for n, _ in used:
        if n.casefold() in seen:
            raise CardError('duplicate_value', f'The label {n} is used twice.', {'label': n})
        seen.add(n.casefold())
    return {'record': {n: v for n, v in used}, 'rows': [{'label': n, 'value': v} for n, v in used]}
