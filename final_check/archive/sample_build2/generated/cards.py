from card_templates.runtime import Context, Store, CardError, iso, coerce_value, view, as_text, is_blank


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


def show_message_banner(ctx, *, message, variant: str='info', dismissible: bool=True, icon: str='') -> dict:
    if not isinstance(message, str):
        message = str(message)
    if not message.strip():
        raise CardError('required', 'Banner needs a message.')
    if variant not in ('success', 'info', 'warning', 'error'):
        variant = 'info'
    node = view('display.banner', message=message, variant=variant, dismissible=dismissible, icon=icon)
    return {'view': node}
