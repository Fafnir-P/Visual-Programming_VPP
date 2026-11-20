# cards.py: written by the app from the card templates. Do not edit by hand.


from card_templates.runtime import CardError, as_text, coerce_value, is_blank, round_half_up, to_number, view


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


def check_field_is_required(ctx, *, value, field: str='value') -> dict:
    if is_blank(value):
        raise CardError('required', f'{field} is required.', {'field': field})
    return {'value': value}


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
