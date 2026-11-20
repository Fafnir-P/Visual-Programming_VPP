"""Card template code, copied unchanged from the request (templateCode of each card)."""
from card_templates.runtime import CardError, coerce_value, iso, round_half_up, to_number, view

def app_start(ctx, *, description: str='App starts') -> dict:
    ctx.require_preview()
    if not isinstance(description, str):
        raise CardError('invalid_input', 'The note must be text.')
    now = iso(ctx.now())
    return {'event': {'kind': 'app_start', 'at': now, 'description': description}, 'started_at': now}


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


def validate_number_range(ctx, *, value, field: str='value', min: float | None=None, max: float | None=None) -> dict:
    spec = {'type': 'number', 'required': True, 'min': min, 'max': max}
    clean = coerce_value(spec, value, field)
    return {'value': clean}


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


def show_message_banner(ctx, *, message, variant: str='info', dismissible: bool=True, icon: str='') -> dict:
    if not isinstance(message, str):
        message = str(message)
    if not message.strip():
        raise CardError('required', 'Banner needs a message.')
    if variant not in ('success', 'info', 'warning', 'error'):
        variant = 'info'
    node = view('display.banner', message=message, variant=variant, dismissible=dismissible, icon=icon)
    return {'view': node}


def app_end(ctx, *, finish, message: str='The app has finished') -> dict:
    if finish is None:
        raise CardError('invalid_input', 'Nothing has reached the end.')
    if not isinstance(message, str):
        raise CardError('invalid_input', 'The message must be text.')
    ctx.store.log_event('app_end', message, {'at': iso(ctx.now())})
    return {}

