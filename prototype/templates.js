// ============================================================================
// CARD TEMPLATES  (GENERATED: do not edit by hand)
// ============================================================================
// Written by:  python -m card_templates.templates_export
// One entry per card title: Python source of the template (no examples), its settings with
// defaults, inputs, outputs, the names it uses from the shared runtime, and own-module helpers.
// Loaded before bedrock.js, which sends only the templates of the cards on the canvas.
const CARD_TEMPLATES = {
 "Accept AI Answer": {
  "function": "accept_ai_answer",
  "source": "def accept_ai_answer(ctx, *, text, format: str='text') -> dict:\n    if not isinstance(text, str) or not text.strip():\n        raise CardError('required', 'AI answer cannot be empty.')\n    text = text.strip()\n    if len(text) > MAX_TEXT_LENGTH:\n        raise CardError('too_long', f'AI answer is too long (max {MAX_TEXT_LENGTH} characters).')\n    valid_formats = {'text', 'json', 'lines'}\n    if format not in valid_formats:\n        raise CardError('invalid_input', f'Format must be text, json, or lines (got {format}).')\n    if format == 'text':\n        return {'answer': text, 'format': 'text'}\n    if format == 'json':\n        try:\n            parsed = json.loads(text)\n        except (json.JSONDecodeError, RecursionError):\n            raise CardError('bad_format', 'AI answer is not valid JSON.') from None\n        return {'answer': parsed, 'format': 'json'}\n    if format == 'lines':\n        lines = [line.strip() for line in text.splitlines() if line.strip()]\n        return {'answer': lines, 'format': 'lines'}\n    raise CardError('invalid_input', f'Unknown format: {format}.')",
  "settings": [
   {
    "name": "format",
    "default": "text"
   }
  ],
  "inputs": [
   "text"
  ],
  "outputs": [
   "answer",
   "format"
  ],
  "runtime": [
   "CardError",
   "MAX_TEXT_LENGTH",
   "json"
  ],
  "imports": []
 },
 "Add Calculated Field": {
  "function": "add_calculated_field",
  "source": "def add_calculated_field(ctx, *, table: str, field: str, expression: str, type: str='number') -> dict:\n    check_identifier(field, 'field name')\n    spec = {'name': field, 'type': type, 'computed': {'expr': expression}}\n    ctx.store.add_field(table, spec)\n    return {'field_name': field}",
  "settings": [
   {
    "name": "table",
    "required": true
   },
   {
    "name": "field",
    "required": true
   },
   {
    "name": "expression",
    "required": true
   },
   {
    "name": "type",
    "default": "number"
   }
  ],
  "inputs": [],
  "outputs": [
   "field_name"
  ],
  "runtime": [
   "check_identifier"
  ],
  "imports": []
 },
 "Add Field To Table": {
  "function": "add_field_to_table",
  "source": "def add_field_to_table(ctx, *, table: str, field: str, type: str, required: bool=False, unique: bool=False, default=None, choices: list | None=None, min=None, max=None, min_length: int | None=None, max_length: int | None=None, pattern: str | None=None) -> dict:\n    check_identifier(field, 'field name')\n    spec: dict = {'name': field, 'type': type, 'required': required, 'unique': unique}\n    if default is not None:\n        spec['default'] = default\n    if choices is not None:\n        spec['choices'] = choices\n    if min is not None:\n        spec['min'] = min\n    if max is not None:\n        spec['max'] = max\n    if min_length is not None:\n        spec['min_length'] = min_length\n    if max_length is not None:\n        spec['max_length'] = max_length\n    if pattern is not None:\n        spec['pattern'] = pattern\n    ctx.store.add_field(table, spec)\n    return {'field_name': field}",
  "settings": [
   {
    "name": "table",
    "required": true
   },
   {
    "name": "field",
    "required": true
   },
   {
    "name": "type",
    "required": true
   },
   {
    "name": "required",
    "default": false
   },
   {
    "name": "unique",
    "default": false
   },
   {
    "name": "default",
    "default": null
   },
   {
    "name": "choices",
    "default": null
   },
   {
    "name": "min",
    "default": null
   },
   {
    "name": "max",
    "default": null
   },
   {
    "name": "min_length",
    "default": null
   },
   {
    "name": "max_length",
    "default": null
   },
   {
    "name": "pattern",
    "default": null
   }
  ],
  "inputs": [],
  "outputs": [
   "field_name"
  ],
  "runtime": [
   "check_identifier"
  ],
  "imports": []
 },
 "Adjust Slider": {
  "function": "adjust_slider",
  "source": "def adjust_slider(ctx, *, value=None, label: str='Value', name: str='slider', min_value: int | float=0, max_value: int | float=100, step: int | float=1) -> dict:\n    low, high = (min_value, max_value)\n    if low >= high:\n        raise CardError('invalid_input', 'Slider min_value must be less than max_value.')\n    clean = coerce_value({'type': 'number'}, value, label)\n    if clean is not None:\n        clean = low if clean < low else high if clean > high else clean\n    node = view('input.slider', id=name, label=label, value=clean, min=low, max=high, step=step)\n    return {'view': node, 'value': clean}",
  "settings": [
   {
    "name": "label",
    "default": "Value"
   },
   {
    "name": "name",
    "default": "slider"
   },
   {
    "name": "min_value",
    "default": 0
   },
   {
    "name": "max_value",
    "default": 100
   },
   {
    "name": "step",
    "default": 1
   }
  ],
  "inputs": [
   "value"
  ],
  "outputs": [
   "view",
   "value"
  ],
  "runtime": [
   "CardError",
   "coerce_value",
   "view"
  ],
  "imports": []
 },
 "App End": {
  "function": "app_end",
  "source": "def app_end(ctx, *, finish, message: str='The app has finished') -> dict:\n    if finish is None:\n        raise CardError('invalid_input', 'Nothing has reached the end.')\n    if not isinstance(message, str):\n        raise CardError('invalid_input', 'The message must be text.')\n    ctx.store.log_event('app_end', message, {'at': iso(ctx.now())})\n    return {}",
  "settings": [
   {
    "name": "message",
    "default": "The app has finished"
   }
  ],
  "inputs": [
   "finish"
  ],
  "outputs": [],
  "runtime": [
   "CardError",
   "iso"
  ],
  "imports": []
 },
 "App Start": {
  "function": "app_start",
  "source": "def app_start(ctx, *, description: str='App starts') -> dict:\n    ctx.require_preview()\n    if not isinstance(description, str):\n        raise CardError('invalid_input', 'The note must be text.')\n    now = iso(ctx.now())\n    return {'event': {'kind': 'app_start', 'at': now, 'description': description}, 'started_at': now}",
  "settings": [
   {
    "name": "description",
    "default": "App starts"
   }
  ],
  "inputs": [],
  "outputs": [
   "event",
   "started_at"
  ],
  "runtime": [
   "CardError",
   "iso"
  ],
  "imports": []
 },
 "Archive Or Restore Record": {
  "function": "archive_or_restore_record",
  "source": "def archive_or_restore_record(ctx, *, id, table: str='records', action: str='archive') -> dict:\n    if action not in ('archive', 'restore'):\n        raise CardError('invalid_input', f'Unknown action: {action}. Use archive or restore.')\n    try:\n        rec_id = int(id)\n    except (TypeError, ValueError):\n        raise CardError('invalid_input', 'ID must be a number.') from None\n    record = ctx.store.set_archived(table, rec_id, action == 'archive')\n    return {'record': record}",
  "settings": [
   {
    "name": "table",
    "default": "records"
   },
   {
    "name": "action",
    "default": "archive"
   }
  ],
  "inputs": [
   "id"
  ],
  "outputs": [
   "record"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Arrange In Grid": {
  "function": "arrange_in_grid",
  "source": "def arrange_in_grid(ctx, *, children=None, columns: int=2, gap: int=16) -> dict:\n    if columns < 1:\n        raise CardError('invalid_input', 'Grid needs at least 1 column.')\n    if gap < 0:\n        raise CardError('invalid_input', 'Gap cannot be negative.')\n    kids = children if isinstance(children, list) else []\n    node = view('layout.grid', children=kids, columns=columns, gap=gap)\n    return {'view': node}",
  "settings": [
   {
    "name": "columns",
    "default": 2
   },
   {
    "name": "gap",
    "default": 16
   }
  ],
  "inputs": [
   "children"
  ],
  "outputs": [
   "view"
  ],
  "runtime": [
   "CardError",
   "view"
  ],
  "imports": []
 },
 "Branch On Yes/No": {
  "function": "branch_on_yes_no",
  "source": "def branch_on_yes_no(ctx, *, condition, value=None) -> dict:\n    if not isinstance(condition, bool):\n        raise CardError('invalid_input', 'Branch On Yes/No needs a yes or no answer.')\n    return {'route': 'yes' if condition else 'no', 'value': value}",
  "settings": [],
  "inputs": [
   "condition",
   "value"
  ],
  "outputs": [
   "yes",
   "no"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Build Data File": {
  "function": "build_data_file",
  "source": "def build_data_file(ctx, *, records: list[dict], format: str='json', instructions: str='Upload this file to the other tool.') -> dict:\n    if not isinstance(records, list):\n        raise CardError('invalid_input', 'Records must be a list.')\n    if format not in ('json', 'csv'):\n        raise CardError('invalid_input', \"Format must be 'json' or 'csv'.\")\n    bounded(records, 10000, 'records')\n    if format == 'json':\n        content = json.dumps(records, default=iso)\n    elif not records:\n        content = ''\n    else:\n        import csv\n        import io\n        headers = [k for k in records[0].keys() if not k.startswith('_')]\n        output = io.StringIO()\n        writer = csv.DictWriter(output, fieldnames=headers, extrasaction='ignore')\n        writer.writeheader()\n        writer.writerows([{k: csv_safe_cell(v) for k, v in r.items()} for r in records])\n        content = output.getvalue()\n    payload = {'format': format, 'content': content}\n    return {'payload': payload, 'instructions': instructions}",
  "settings": [
   {
    "name": "format",
    "default": "json"
   },
   {
    "name": "instructions",
    "default": "Upload this file to the other tool."
   }
  ],
  "inputs": [
   "records"
  ],
  "outputs": [
   "payload",
   "instructions"
  ],
  "runtime": [
   "CardError",
   "bounded",
   "csv_safe_cell",
   "iso",
   "json"
  ],
  "imports": []
 },
 "Build Email Text": {
  "function": "build_email_text",
  "source": "def build_email_text(ctx, *, data: dict, template: str | None=None) -> dict:\n    if not isinstance(data, dict):\n        raise CardError('invalid_input', 'Data must be a record.')\n    if template:\n        text = template\n        import re\n        placeholders = re.findall('\\\\{(\\\\w+)\\\\}', template)\n        for ph in placeholders:\n            if ph not in data:\n                raise CardError('missing_field', f\"Template uses field '{ph}' which is not in data.\")\n            text = text.replace(f'{{{ph}}}', str(data[ph]))\n        payload = {'text': text}\n    else:\n        payload = dict(data)\n    return {'payload': payload, 'instructions': 'Copy this text and send it by email.'}",
  "settings": [
   {
    "name": "template",
    "default": null
   }
  ],
  "inputs": [
   "data"
  ],
  "outputs": [
   "payload",
   "instructions"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Build Order Request": {
  "function": "build_order_request",
  "source": "def build_order_request(ctx, *, order: dict, format: str='json', instructions: str='Submit this order request to the supplier.') -> dict:\n    if not isinstance(order, dict):\n        raise CardError('invalid_input', 'Order must be a record.')\n    if format not in ('json', 'text'):\n        raise CardError('invalid_input', \"Format must be 'json' or 'text'.\")\n    if format == 'json':\n        payload = dict(order)\n    else:\n        lines = []\n        for key, value in order.items():\n            lines.append(f'{key}: {value}')\n        payload = {'text': '\\n'.join(lines)}\n    return {'payload': payload, 'instructions': instructions}",
  "settings": [
   {
    "name": "format",
    "default": "json"
   },
   {
    "name": "instructions",
    "default": "Submit this order request to the supplier."
   }
  ],
  "inputs": [
   "order"
  ],
  "outputs": [
   "payload",
   "instructions"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Build Record From Fields": {
  "function": "build_record_from_fields",
  "source": "def build_record_from_fields(ctx, *, fields: dict) -> dict:\n    if not isinstance(fields, dict):\n        raise CardError('invalid_input', 'Fields must be a record.')\n    return {'record': fields.copy()}",
  "settings": [
   {
    "name": "fields",
    "required": true
   }
  ],
  "inputs": [],
  "outputs": [
   "record"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Build Shipment Notice": {
  "function": "build_shipment_notice",
  "source": "def build_shipment_notice(ctx, *, shipment: dict, instructions: str='Send this shipment notice to the recipient.') -> dict:\n    if not isinstance(shipment, dict):\n        raise CardError('invalid_input', 'Shipment must be a record.')\n    if not shipment:\n        raise CardError('invalid_input', 'Shipment cannot be empty.')\n    payload = dict(shipment)\n    return {'payload': payload, 'instructions': instructions}",
  "settings": [
   {
    "name": "instructions",
    "default": "Send this shipment notice to the recipient."
   }
  ],
  "inputs": [
   "shipment"
  ],
  "outputs": [
   "payload",
   "instructions"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Build Spreadsheet Export": {
  "function": "build_spreadsheet_export",
  "source": "def build_spreadsheet_export(ctx, *, records: list[dict], headers: list[str] | None=None) -> dict:\n    if not isinstance(records, list):\n        raise CardError('invalid_input', 'Records must be a list.')\n    bounded(records, 10000, 'records')\n    if headers is not None and (not isinstance(headers, list)):\n        raise CardError('invalid_input', 'Headers must be a list of field names.')\n    if headers is None:\n        if records:\n            headers = [k for k in records[0].keys() if not k.startswith('_')]\n        else:\n            headers = []\n    rows = []\n    for rec in records:\n        if not isinstance(rec, dict):\n            raise CardError('invalid_input', 'Each record must be a dict.')\n        row = [csv_safe_cell(get_field(rec, h, '')) for h in headers]\n        rows.append(row)\n    payload = {'headers': headers, 'rows': rows}\n    return {'payload': payload, 'instructions': 'Paste this table into a spreadsheet.'}",
  "settings": [
   {
    "name": "headers",
    "default": null
   }
  ],
  "inputs": [
   "records"
  ],
  "outputs": [
   "payload",
   "instructions"
  ],
  "runtime": [
   "CardError",
   "bounded",
   "csv_safe_cell",
   "get_field"
  ],
  "imports": []
 },
 "Build Summary Record": {
  "function": "build_summary_record",
  "source": "def build_summary_record(ctx, *, value_1=None, value_2=None, value_3=None, value_4=None, labels: list | None=None) -> dict:\n    if labels is not None and (not isinstance(labels, list) or not all((isinstance(x, str) and x.strip() for x in labels))):\n        raise CardError('invalid_input', 'Labels must be a list of texts.')\n    names = [labels[i].strip() if labels and i < len(labels) else f'Value {i + 1}' for i in range(4)]\n    values = [value_1, value_2, value_3, value_4]\n    used = [(n, v) for n, v in zip(names, values) if v is not None]\n    if not used:\n        raise CardError('required', 'Link at least one value.')\n    seen = set()\n    for n, _ in used:\n        if n.casefold() in seen:\n            raise CardError('duplicate_value', f'The label {n} is used twice.', {'label': n})\n        seen.add(n.casefold())\n    return {'record': {n: v for n, v in used}, 'rows': [{'label': n, 'value': v} for n, v in used]}",
  "settings": [
   {
    "name": "labels",
    "default": null
   }
  ],
  "inputs": [
   "value_1",
   "value_2",
   "value_3",
   "value_4"
  ],
  "outputs": [
   "record",
   "rows"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Build Supplier Message": {
  "function": "build_supplier_message",
  "source": "def build_supplier_message(ctx, *, message: dict, instructions: str='Send this message to the supplier.') -> dict:\n    if not isinstance(message, dict):\n        raise CardError('invalid_input', 'Message must be a record.')\n    if not message:\n        raise CardError('invalid_input', 'Message cannot be empty.')\n    payload = dict(message)\n    return {'payload': payload, 'instructions': instructions}",
  "settings": [
   {
    "name": "instructions",
    "default": "Send this message to the supplier."
   }
  ],
  "inputs": [
   "message"
  ],
  "outputs": [
   "payload",
   "instructions"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Calculate Average Value": {
  "function": "calculate_average_value",
  "source": "def calculate_average_value(ctx, *, records, field: str='value', places: int=2) -> dict:\n    if not isinstance(records, list):\n        raise CardError('invalid_input', 'Average needs a list of records.')\n    values = []\n    for rec in bounded(records):\n        value = get_field(rec, field)\n        if not is_blank(value):\n            values.append(to_number(value, field))\n    if not values:\n        return {'average': 0}\n    avg = sum(values) / len(values)\n    return {'average': round_half_up(avg, places)}",
  "settings": [
   {
    "name": "field",
    "default": "value"
   },
   {
    "name": "places",
    "default": 2
   }
  ],
  "inputs": [
   "records"
  ],
  "outputs": [
   "average"
  ],
  "runtime": [
   "CardError",
   "bounded",
   "get_field",
   "is_blank",
   "round_half_up",
   "to_number"
  ],
  "imports": []
 },
 "Calculate Date Difference": {
  "function": "calculate_date_difference",
  "source": "def calculate_date_difference(ctx, *, start_date, end_date, unit: str='days') -> dict:\n    start = to_datetime(start_date, 'start_date')\n    end = to_datetime(end_date, 'end_date')\n    delta = end - start\n    if unit == 'days':\n        diff = delta.days + delta.seconds / 86400\n    elif unit == 'hours':\n        diff = delta.total_seconds() / 3600\n    elif unit == 'minutes':\n        diff = delta.total_seconds() / 60\n    elif unit == 'seconds':\n        diff = delta.total_seconds()\n    else:\n        raise CardError('invalid_input', f'Unknown unit: {unit}. Use days, hours, minutes or seconds.')\n    return {'difference': round(diff, 2)}",
  "settings": [
   {
    "name": "unit",
    "default": "days"
   }
  ],
  "inputs": [
   "start_date",
   "end_date"
  ],
  "outputs": [
   "difference"
  ],
  "runtime": [
   "CardError",
   "to_datetime"
  ],
  "imports": []
 },
 "Calculate From Two Values": {
  "function": "calculate_from_two_values",
  "source": "def calculate_from_two_values(ctx, *, first, second, operation: str='add', places: int=2) -> dict:\n    a = to_number(first, 'first')\n    b = to_number(second, 'second')\n    if operation == 'add':\n        result = a + b\n    elif operation == 'subtract':\n        result = a - b\n    elif operation == 'multiply':\n        result = a * b\n    elif operation == 'divide':\n        if b == 0:\n            raise CardError('divide_by_zero', 'Cannot divide by zero.')\n        result = a / b\n    else:\n        raise CardError('invalid_input', f'Unknown operation: {operation}. Use add, subtract, multiply or divide.')\n    return {'result': round_half_up(result, places)}",
  "settings": [
   {
    "name": "operation",
    "default": "add"
   },
   {
    "name": "places",
    "default": 2
   }
  ],
  "inputs": [
   "first",
   "second"
  ],
  "outputs": [
   "result"
  ],
  "runtime": [
   "CardError",
   "round_half_up",
   "to_number"
  ],
  "imports": []
 },
 "Calculate Percentage Change": {
  "function": "calculate_percentage_change",
  "source": "def calculate_percentage_change(ctx, *, old_value, new_value, places: int=2) -> dict:\n    old = to_number(old_value, 'old_value')\n    new = to_number(new_value, 'new_value')\n    if old == 0:\n        raise CardError('divide_by_zero', 'Cannot calculate percentage change: old value is zero.')\n    change = (new - old) / old * 100\n    return {'change': round_half_up(change, places)}",
  "settings": [
   {
    "name": "places",
    "default": 2
   }
  ],
  "inputs": [
   "old_value",
   "new_value"
  ],
  "outputs": [
   "change"
  ],
  "runtime": [
   "CardError",
   "round_half_up",
   "to_number"
  ],
  "imports": []
 },
 "Calculate Percentage Of Total": {
  "function": "calculate_percentage_of_total",
  "source": "def calculate_percentage_of_total(ctx, *, value, total, places: int=2) -> dict:\n    num = to_number(value, 'value')\n    den = to_number(total, 'total')\n    if den == 0:\n        raise CardError('divide_by_zero', 'Cannot calculate percentage: total is zero.')\n    pct = num / den * 100\n    return {'percentage': round_half_up(pct, places)}",
  "settings": [
   {
    "name": "places",
    "default": 2
   }
  ],
  "inputs": [
   "value",
   "total"
  ],
  "outputs": [
   "percentage"
  ],
  "runtime": [
   "CardError",
   "round_half_up",
   "to_number"
  ],
  "imports": []
 },
 "Calculate Reorder Quantity": {
  "function": "calculate_reorder_quantity",
  "source": "def calculate_reorder_quantity(ctx, *, average_use, lead_time, safety_factor: float=1.2) -> dict:\n    use = to_number(average_use, 'average_use')\n    lead = to_number(lead_time, 'lead_time')\n    factor = to_number(safety_factor, 'safety_factor')\n    if use < 0:\n        raise CardError('too_small', 'Average use cannot be negative.')\n    if lead < 0:\n        raise CardError('too_small', 'Lead time cannot be negative.')\n    if factor < 0:\n        raise CardError('too_small', 'Safety factor cannot be negative.')\n    quantity = use * lead * factor\n    return {'quantity': round_half_up(quantity, 0)}",
  "settings": [
   {
    "name": "safety_factor",
    "default": 1.2
   }
  ],
  "inputs": [
   "average_use",
   "lead_time"
  ],
  "outputs": [
   "quantity"
  ],
  "runtime": [
   "CardError",
   "round_half_up",
   "to_number"
  ],
  "imports": []
 },
 "Calculate Running Total": {
  "function": "calculate_running_total",
  "source": "def calculate_running_total(ctx, *, records, field: str='value', output_field: str='running_total', initial: float=0) -> dict:\n    if not isinstance(records, list):\n        raise CardError('invalid_input', 'Running total needs a list of records.')\n    results = []\n    total = to_number(initial, 'initial')\n    for rec in bounded(records):\n        value = get_field(rec, field)\n        if not is_blank(value):\n            total += to_number(value, field)\n        new_rec = {**rec, output_field: total}\n        results.append(new_rec)\n    return {'records': results}",
  "settings": [
   {
    "name": "field",
    "default": "value"
   },
   {
    "name": "output_field",
    "default": "running_total"
   },
   {
    "name": "initial",
    "default": 0
   }
  ],
  "inputs": [
   "records"
  ],
  "outputs": [
   "records"
  ],
  "runtime": [
   "CardError",
   "bounded",
   "get_field",
   "is_blank",
   "to_number"
  ],
  "imports": []
 },
 "Calculate Stock Level": {
  "function": "calculate_stock_level",
  "source": "def calculate_stock_level(ctx, *, starting, incoming, outgoing) -> dict:\n    start = to_number(starting, 'starting')\n    inc = to_number(incoming, 'incoming')\n    out = to_number(outgoing, 'outgoing')\n    stock = start + inc - out\n    return {'stock': stock}",
  "settings": [],
  "inputs": [
   "starting",
   "incoming",
   "outgoing"
  ],
  "outputs": [
   "stock"
  ],
  "runtime": [
   "to_number"
  ],
  "imports": []
 },
 "Calculate Sum Of Field": {
  "function": "calculate_sum_of_field",
  "source": "def calculate_sum_of_field(ctx, *, records, field: str='value') -> dict:\n    if not isinstance(records, list):\n        raise CardError('invalid_input', 'Sum needs a list of records.')\n    total = 0\n    for rec in bounded(records):\n        value = get_field(rec, field)\n        if not is_blank(value):\n            total += to_number(value, field)\n    return {'sum': total}",
  "settings": [
   {
    "name": "field",
    "default": "value"
   }
  ],
  "inputs": [
   "records"
  ],
  "outputs": [
   "sum"
  ],
  "runtime": [
   "CardError",
   "bounded",
   "get_field",
   "is_blank",
   "to_number"
  ],
  "imports": []
 },
 "Calculate Working Days": {
  "function": "calculate_working_days",
  "source": "def calculate_working_days(ctx, *, start_date, end_date, holidays: list[str] | None=None) -> dict:\n    start = to_date(start_date, 'start_date')\n    end = to_date(end_date, 'end_date')\n    if end < start:\n        raise CardError('invalid_input', 'end_date must be on or after start_date.')\n    holiday_set = set()\n    if holidays:\n        for h in holidays:\n            holiday_set.add(to_date(h, 'holiday').isoformat())\n    max_days = 36600\n    if (end - start).days > max_days:\n        raise CardError('limit_exceeded', f'The date range is too long (limit {max_days} days).')\n    count = 0\n    current = start\n    while True:\n        if current.weekday() < 5 and current.isoformat() not in holiday_set:\n            count += 1\n        if current >= end:\n            break\n        current += dt.timedelta(days=1)\n    return {'working_days': count}",
  "settings": [
   {
    "name": "holidays",
    "default": null
   }
  ],
  "inputs": [
   "start_date",
   "end_date"
  ],
  "outputs": [
   "working_days"
  ],
  "runtime": [
   "CardError",
   "dt",
   "to_date"
  ],
  "imports": []
 },
 "Change Text Case": {
  "function": "change_text_case",
  "source": "def change_text_case(ctx, *, text, case: str='upper') -> dict:\n    s = as_text(text, 'text')\n    if case == 'upper':\n        return {'text': s.upper()}\n    if case == 'lower':\n        return {'text': s.lower()}\n    if case == 'title':\n        return {'text': s.title()}\n    raise CardError('invalid_input', f'Case must be upper, lower or title (got {case!r}).')",
  "settings": [
   {
    "name": "case",
    "default": "upper"
   }
  ],
  "inputs": [
   "text"
  ],
  "outputs": [
   "text"
  ],
  "runtime": [
   "CardError",
   "as_text"
  ],
  "imports": []
 },
 "Change Value By Percent": {
  "function": "change_value_by_percent",
  "source": "def change_value_by_percent(ctx, *, value, percent, direction: str='increase', places: int=2) -> dict:\n    val = to_number(value, 'value')\n    pct = to_number(percent, 'percent')\n    if pct < 0:\n        raise CardError('too_small', 'Percent cannot be negative.')\n    if direction not in ('increase', 'decrease'):\n        raise CardError('invalid_input', f'Direction must be increase or decrease, not {direction}.')\n    change = val * (pct / 100)\n    result = val + change if direction == 'increase' else val - change\n    return {'result': round_half_up(result, places)}",
  "settings": [
   {
    "name": "percent",
    "required": true
   },
   {
    "name": "direction",
    "default": "increase"
   },
   {
    "name": "places",
    "default": 2
   }
  ],
  "inputs": [
   "value"
  ],
  "outputs": [
   "result"
  ],
  "runtime": [
   "CardError",
   "round_half_up",
   "to_number"
  ],
  "imports": []
 },
 "Chart Over Time": {
  "function": "chart_over_time",
  "source": "def chart_over_time(ctx, *, data, date_field: str='date', value_field: str='value', title: str='Chart', chart_type: str='line') -> dict:\n    if not isinstance(data, list):\n        raise CardError('invalid_input', 'Chart data must be a list of records.')\n    if not data:\n        raise CardError('invalid_input', 'Chart needs at least one data point.')\n    points = bounded(data, limit=10000, what='chart points')\n    if chart_type not in ('line', 'bar', 'area'):\n        chart_type = 'line'\n    node = view('display.chart', title=title, chart_type=chart_type, data=points, date_field=date_field, value_field=value_field)\n    return {'view': node}",
  "settings": [
   {
    "name": "date_field",
    "default": "date"
   },
   {
    "name": "value_field",
    "default": "value"
   },
   {
    "name": "title",
    "default": "Chart"
   },
   {
    "name": "chart_type",
    "default": "line"
   }
  ],
  "inputs": [
   "data"
  ],
  "outputs": [
   "view"
  ],
  "runtime": [
   "CardError",
   "bounded",
   "view"
  ],
  "imports": []
 },
 "Check Answer Shape": {
  "function": "check_answer_shape",
  "source": "def check_answer_shape(ctx, *, answer, expected_type: str='dict', required_keys: list | None=None, min_length: int | None=None, max_length: int | None=None) -> dict:\n    valid_types = {'dict', 'list', 'text'}\n    if expected_type not in valid_types:\n        raise CardError('invalid_input', f'Expected type must be dict, list, or text (got {expected_type}).')\n    if expected_type == 'dict' and (not isinstance(answer, dict)):\n        raise CardError('invalid_input', f'Answer must be a dict (got {type(answer).__name__}).')\n    if expected_type == 'list' and (not isinstance(answer, list)):\n        raise CardError('invalid_input', f'Answer must be a list (got {type(answer).__name__}).')\n    if expected_type == 'text' and (not isinstance(answer, str)):\n        raise CardError('invalid_input', f'Answer must be text (got {type(answer).__name__}).')\n    valid = True\n    if expected_type == 'dict' and required_keys:\n        missing = [k for k in required_keys if k not in answer]\n        if missing:\n            valid = False\n    if expected_type in ('list', 'text'):\n        length = len(answer)\n        if min_length is not None and length < min_length:\n            valid = False\n        if max_length is not None and length > max_length:\n            valid = False\n    return {'value': answer, 'valid': valid}",
  "settings": [
   {
    "name": "expected_type",
    "default": "dict"
   },
   {
    "name": "required_keys",
    "default": null
   },
   {
    "name": "min_length",
    "default": null
   },
   {
    "name": "max_length",
    "default": null
   }
  ],
  "inputs": [
   "answer"
  ],
  "outputs": [
   "value",
   "valid"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Check Field Is Required": {
  "function": "check_field_is_required",
  "source": "def check_field_is_required(ctx, *, value, field: str='value') -> dict:\n    if is_blank(value):\n        raise CardError('required', f'{field} is required.', {'field': field})\n    return {'value': value}",
  "settings": [
   {
    "name": "field",
    "default": "value"
   }
  ],
  "inputs": [
   "value"
  ],
  "outputs": [
   "value"
  ],
  "runtime": [
   "CardError",
   "is_blank"
  ],
  "imports": []
 },
 "Check Text Length": {
  "function": "check_text_length",
  "source": "def check_text_length(ctx, *, value, field: str='value', min_length: int | None=None, max_length: int | None=None) -> dict:\n    spec = {'type': 'text', 'required': True, 'min_length': min_length, 'max_length': max_length}\n    clean = coerce_value(spec, value, field)\n    return {'value': clean}",
  "settings": [
   {
    "name": "field",
    "default": "value"
   },
   {
    "name": "min_length",
    "default": null
   },
   {
    "name": "max_length",
    "default": null
   }
  ],
  "inputs": [
   "value"
  ],
  "outputs": [
   "value"
  ],
  "runtime": [
   "coerce_value"
  ],
  "imports": []
 },
 "Check Valid Status Transition": {
  "function": "check_valid_status_transition",
  "source": "def check_valid_status_transition(ctx, *, record, old_field: str='old_status', new_field: str='new_status', allowed_transitions: dict=None) -> dict:\n    if not isinstance(record, dict):\n        raise CardError('invalid_input', 'Check Valid Status Transition needs a record.')\n    transitions = allowed_transitions or {'pending': ['approved', 'rejected'], 'approved': ['shipped', 'cancelled'], 'shipped': ['delivered']}\n    old_status = str(get_field(record, old_field, '')).strip()\n    new_status = str(get_field(record, new_field, '')).strip()\n    if old_status == new_status:\n        return {'record': record}\n    if old_status not in transitions:\n        raise CardError('invalid_transition', f'Unknown status: {old_status}.')\n    if new_status not in transitions[old_status]:\n        allowed = ', '.join(transitions[old_status])\n        raise CardError('invalid_transition', f'Cannot change from {old_status} to {new_status}. Allowed: {allowed}.')\n    return {'record': record}",
  "settings": [
   {
    "name": "old_field",
    "default": "old_status"
   },
   {
    "name": "new_field",
    "default": "new_status"
   },
   {
    "name": "allowed_transitions",
    "default": null
   }
  ],
  "inputs": [
   "record"
  ],
  "outputs": [
   "record"
  ],
  "runtime": [
   "CardError",
   "get_field"
  ],
  "imports": []
 },
 "Choose File": {
  "function": "choose_file",
  "source": "def choose_file(ctx, *, filename=None, label: str='Choose file', name: str='file', accept: str='', multiple: bool=False) -> dict:\n    clean = None\n    if filename is not None:\n        if not isinstance(filename, str):\n            raise CardError('invalid_input', 'Filename must be text.')\n        clean = filename.strip() if filename.strip() else None\n    node = view('input.file', id=name, label=label, accept=accept, multiple=multiple, value=clean)\n    return {'view': node, 'filename': clean}",
  "settings": [
   {
    "name": "label",
    "default": "Choose file"
   },
   {
    "name": "name",
    "default": "file"
   },
   {
    "name": "accept",
    "default": ""
   },
   {
    "name": "multiple",
    "default": false
   }
  ],
  "inputs": [
   "filename"
  ],
  "outputs": [
   "view",
   "filename"
  ],
  "runtime": [
   "CardError",
   "view"
  ],
  "imports": []
 },
 "Choose From Dropdown": {
  "function": "choose_from_dropdown",
  "source": "def choose_from_dropdown(ctx, *, value=None, name: str='dropdown', label: str='Choose', choices: list=None, required: bool=False, placeholder: str='', help_text: str='') -> dict:\n    if not choices:\n        choices = []\n    spec = {'type': 'choice', 'required': required, 'choices': choices}\n    clean = coerce_value(spec, value, label)\n    node = view('input.dropdown', id=name, label=label, value=clean, choices=choices, required=required, placeholder=placeholder, help=help_text)\n    return {'view': node, 'value': clean}",
  "settings": [
   {
    "name": "name",
    "default": "dropdown"
   },
   {
    "name": "label",
    "default": "Choose"
   },
   {
    "name": "choices",
    "default": null
   },
   {
    "name": "required",
    "default": false
   },
   {
    "name": "placeholder",
    "default": ""
   },
   {
    "name": "help_text",
    "default": ""
   }
  ],
  "inputs": [
   "value"
  ],
  "outputs": [
   "view",
   "value"
  ],
  "runtime": [
   "coerce_value",
   "view"
  ],
  "imports": []
 },
 "Choose One Option": {
  "function": "choose_one_option",
  "source": "def choose_one_option(ctx, *, value=None, name: str='radio', label: str='Choose One', choices: list=None, required: bool=False, help_text: str='') -> dict:\n    if not choices:\n        choices = []\n    spec = {'type': 'choice', 'required': required, 'choices': choices}\n    clean = coerce_value(spec, value, label)\n    node = view('input.radio', id=name, label=label, value=clean, choices=choices, required=required, help=help_text)\n    return {'view': node, 'value': clean}",
  "settings": [
   {
    "name": "name",
    "default": "radio"
   },
   {
    "name": "label",
    "default": "Choose One"
   },
   {
    "name": "choices",
    "default": null
   },
   {
    "name": "required",
    "default": false
   },
   {
    "name": "help_text",
    "default": ""
   }
  ],
  "inputs": [
   "value"
  ],
  "outputs": [
   "view",
   "value"
  ],
  "runtime": [
   "coerce_value",
   "view"
  ],
  "imports": []
 },
 "Click Button": {
  "function": "click_button",
  "source": "def click_button(ctx, *, label: str='', variant: str='primary', icon: str='', disabled: bool=False, name: str='action') -> dict:\n    if not label.strip():\n        raise CardError('required', 'Button needs a label.')\n    node = view('action.button', id=name, label=label, variant=variant, icon=icon, disabled=disabled)\n    return {'view': node}",
  "settings": [
   {
    "name": "label",
    "default": ""
   },
   {
    "name": "variant",
    "default": "primary"
   },
   {
    "name": "icon",
    "default": ""
   },
   {
    "name": "disabled",
    "default": false
   },
   {
    "name": "name",
    "default": "action"
   }
  ],
  "inputs": [],
  "outputs": [
   "view"
  ],
  "runtime": [
   "CardError",
   "view"
  ],
  "imports": []
 },
 "Collapse Section": {
  "function": "collapse_section",
  "source": "def collapse_section(ctx, *, children=None, title: str='', collapsed: bool=False) -> dict:\n    if not title or not isinstance(title, str) or (not title.strip()):\n        raise CardError('required', 'Section title is required.')\n    if not isinstance(children, list):\n        raise CardError('invalid_input', 'Children must be a list of view nodes.')\n    node = view('layout.collapsible', children=children, title=title.strip(), collapsed=collapsed)\n    return {'view': node}",
  "settings": [
   {
    "name": "title",
    "default": ""
   },
   {
    "name": "collapsed",
    "default": false
   }
  ],
  "inputs": [
   "children"
  ],
  "outputs": [
   "view"
  ],
  "runtime": [
   "CardError",
   "view"
  ],
  "imports": []
 },
 "Collect Error Records": {
  "function": "collect_error_records",
  "source": "def collect_error_records(ctx, *, records, error_flag: str='_error') -> dict:\n    if not isinstance(records, list):\n        raise CardError('invalid_input', 'Collect Error Records needs a list of records.')\n    if not error_flag:\n        raise CardError('invalid_input', 'Error flag field name is required.')\n    items = bounded(records)\n    errors = []\n    valid = []\n    for rec in items:\n        if isinstance(rec, dict) and rec.get(error_flag):\n            errors.append(rec)\n        else:\n            valid.append(rec)\n    return {'errors': errors, 'valid': valid}",
  "settings": [
   {
    "name": "error_flag",
    "default": "_error"
   }
  ],
  "inputs": [
   "records"
  ],
  "outputs": [
   "errors",
   "valid"
  ],
  "runtime": [
   "CardError",
   "bounded"
  ],
  "imports": []
 },
 "Combine Multiple Fields": {
  "function": "combine_multiple_fields",
  "source": "def combine_multiple_fields(ctx, *, record, fields: list, separator: str=' ') -> dict:\n    if not fields:\n        raise CardError('invalid_input', 'At least one field is required.')\n    parts = []\n    for f in fields:\n        val = get_field(record, f)\n        if not is_blank(val):\n            parts.append(str(val))\n    return {'text': separator.join(parts)}",
  "settings": [
   {
    "name": "fields",
    "required": true
   },
   {
    "name": "separator",
    "default": " "
   }
  ],
  "inputs": [
   "record"
  ],
  "outputs": [
   "text"
  ],
  "runtime": [
   "CardError",
   "get_field",
   "is_blank"
  ],
  "imports": []
 },
 "Compare Two Dates": {
  "function": "compare_two_dates",
  "source": "def compare_two_dates(ctx, *, first_date, second_date) -> dict:\n    first = to_datetime(first_date, 'first_date')\n    second = to_datetime(second_date, 'second_date')\n    if first < second:\n        comparison = 'before'\n    elif first > second:\n        comparison = 'after'\n    else:\n        comparison = 'equal'\n    return {'comparison': comparison}",
  "settings": [],
  "inputs": [
   "first_date",
   "second_date"
  ],
  "outputs": [
   "comparison"
  ],
  "runtime": [
   "to_datetime"
  ],
  "imports": []
 },
 "Compare Two Fields": {
  "function": "compare_two_fields",
  "source": "def compare_two_fields(ctx, *, value, field_a: str='field_a', field_b: str='field_b', operator: str='gt') -> dict:\n    val_a = get_field(value, field_a)\n    val_b = get_field(value, field_b)\n    if operator in ('gt', 'gte', 'lt', 'lte'):\n        num_a = to_number(val_a, field_a)\n        num_b = to_number(val_b, field_b)\n        passes = num_a > num_b if operator == 'gt' else num_a >= num_b if operator == 'gte' else num_a < num_b if operator == 'lt' else num_a <= num_b\n    elif operator == 'eq':\n        passes = val_a == val_b\n    elif operator == 'ne':\n        passes = val_a != val_b\n    else:\n        raise CardError('invalid_input', f'Unknown operator: {operator}.')\n    if not passes:\n        raise CardError('comparison_failed', f'{field_a} must be {operator} {field_b}.', {'field_a': field_a, 'field_b': field_b})\n    return {'value': value}",
  "settings": [
   {
    "name": "field_a",
    "default": "field_a"
   },
   {
    "name": "field_b",
    "default": "field_b"
   },
   {
    "name": "operator",
    "default": "gt"
   }
  ],
  "inputs": [
   "value"
  ],
  "outputs": [
   "value"
  ],
  "runtime": [
   "CardError",
   "get_field",
   "to_number"
  ],
  "imports": []
 },
 "Compare Two Numbers": {
  "function": "compare_two_numbers",
  "source": "def compare_two_numbers(ctx, *, first, second, operator: str='gt') -> dict:\n    if operator not in _COMPARE_OPERATORS:\n        raise CardError('invalid_input', f\"Operator must be one of: {', '.join(_COMPARE_OPERATORS)}.\")\n    a = to_number(first, 'first')\n    b = to_number(second, 'second')\n    same = math.isclose(a, b, rel_tol=1e-09, abs_tol=1e-09)\n    answer = {'eq': same, 'ne': not same, 'gt': a > b and (not same), 'gte': a > b or same, 'lt': a < b and (not same), 'lte': a < b or same}[operator]\n    return {'result': answer}",
  "settings": [
   {
    "name": "operator",
    "default": "gt"
   }
  ],
  "inputs": [
   "first",
   "second"
  ],
  "outputs": [
   "result"
  ],
  "runtime": [
   "CardError",
   "math",
   "to_number"
  ],
  "imports": [],
  "helpers": [
   {
    "name": "_COMPARE_OPERATORS",
    "source": "_COMPARE_OPERATORS = ('eq', 'ne', 'gt', 'gte', 'lt', 'lte')"
   }
  ]
 },
 "Confirm Action": {
  "function": "confirm_action",
  "source": "def confirm_action(ctx, *, message: str='', title: str='Confirm', confirm_label: str='Confirm', cancel_label: str='Cancel') -> dict:\n    if not message.strip():\n        raise CardError('required', 'Confirmation needs a message.')\n    node = view('dialog.confirm', title=title, message=message, confirm_label=confirm_label, cancel_label=cancel_label)\n    return {'view': node}",
  "settings": [
   {
    "name": "message",
    "default": ""
   },
   {
    "name": "title",
    "default": "Confirm"
   },
   {
    "name": "confirm_label",
    "default": "Confirm"
   },
   {
    "name": "cancel_label",
    "default": "Cancel"
   }
  ],
  "inputs": [],
  "outputs": [
   "view"
  ],
  "runtime": [
   "CardError",
   "view"
  ],
  "imports": []
 },
 "Confirm Destructive Action": {
  "function": "confirm_destructive_action",
  "source": "def confirm_destructive_action(ctx, *, confirmed, action: str='delete', count: int=1, require_for_single: bool=False) -> dict:\n    if count == 1 and (not require_for_single):\n        return {'proceed': True}\n    if not confirmed:\n        items = 'record' if count == 1 else f'{count} records'\n        raise CardError('confirmation_required', f'Confirm to {action} {items}.')\n    return {'proceed': True}",
  "settings": [
   {
    "name": "action",
    "default": "delete"
   },
   {
    "name": "count",
    "default": 1
   },
   {
    "name": "require_for_single",
    "default": false
   }
  ],
  "inputs": [
   "confirmed"
  ],
  "outputs": [
   "proceed"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Convert Field Type": {
  "function": "convert_field_type",
  "source": "def convert_field_type(ctx, *, record, field: str='value', target_type: str='text') -> dict:\n    rec = dict(record)\n    value = get_field(rec, field)\n    spec = {'type': target_type}\n    rec[field] = coerce_value(spec, value, field)\n    return {'record': rec}",
  "settings": [
   {
    "name": "field",
    "default": "value"
   },
   {
    "name": "target_type",
    "default": "text"
   }
  ],
  "inputs": [
   "record"
  ],
  "outputs": [
   "record"
  ],
  "runtime": [
   "coerce_value",
   "get_field"
  ],
  "imports": []
 },
 "Copy Record": {
  "function": "copy_record",
  "source": "def copy_record(ctx, *, id, table: str='records', changes: dict | None=None) -> dict:\n    if changes is not None and (not isinstance(changes, dict)):\n        raise CardError('invalid_input', 'Changes must be a record.')\n    try:\n        rec_id = int(id)\n    except (TypeError, ValueError):\n        raise CardError('invalid_input', 'ID must be a number.') from None\n    source = ctx.store.get(table, rec_id)\n    if source is None:\n        raise CardError('not_found', f'Record {rec_id} not found in {table}.')\n    new_values = {k: v for k, v in source.items() if k not in ('id', '_version', '_created_at', '_updated_at', '_archived')}\n    if changes:\n        new_values.update(changes)\n    record = ctx.store.insert(table, new_values)\n    return {'record': record}",
  "settings": [
   {
    "name": "table",
    "default": "records"
   },
   {
    "name": "changes",
    "default": null
   }
  ],
  "inputs": [
   "id"
  ],
  "outputs": [
   "record"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Count Records Matching Condition": {
  "function": "count_records_matching_condition",
  "source": "def count_records_matching_condition(ctx, *, records, condition: dict | None=None) -> dict:\n    if not isinstance(records, list):\n        raise CardError('invalid_input', 'Count needs a list of records.')\n    if condition is None:\n        return {'count': len(bounded(records))}\n    validate_condition(condition)\n    count = sum((1 for rec in bounded(records) if matches(rec, condition)))\n    return {'count': count}",
  "settings": [
   {
    "name": "condition",
    "default": null
   }
  ],
  "inputs": [
   "records"
  ],
  "outputs": [
   "count"
  ],
  "runtime": [
   "CardError",
   "bounded",
   "matches",
   "validate_condition"
  ],
  "imports": []
 },
 "Create Multiple Records": {
  "function": "create_multiple_records",
  "source": "def create_multiple_records(ctx, *, records, table: str='records', limit: int=MAX_LOOP_ITEMS) -> dict:\n    if not isinstance(records, (list, tuple)):\n        raise CardError('invalid_input', 'Records must be a list.')\n    items = bounded(records, limit, 'records')\n    inserted = ctx.store.insert_many(table, items)\n    return {'records': inserted, 'count': len(inserted)}",
  "settings": [
   {
    "name": "table",
    "default": "records"
   },
   {
    "name": "limit",
    "default": 10000
   }
  ],
  "inputs": [
   "records"
  ],
  "outputs": [
   "records",
   "count"
  ],
  "runtime": [
   "CardError",
   "MAX_LOOP_ITEMS",
   "bounded"
  ],
  "imports": []
 },
 "Create New Record": {
  "function": "create_new_record",
  "source": "def create_new_record(ctx, *, values, table: str='records') -> dict:\n    if not isinstance(values, dict):\n        raise CardError('invalid_input', 'Values must be a record.')\n    record = ctx.store.insert(table, values)\n    return {'record': record}",
  "settings": [
   {
    "name": "table",
    "default": "records"
   }
  ],
  "inputs": [
   "values"
  ],
  "outputs": [
   "record"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Create Or Update Record": {
  "function": "create_or_update_record",
  "source": "def create_or_update_record(ctx, *, values, table: str='records', key_field: str='id') -> dict:\n    if not isinstance(values, dict):\n        raise CardError('invalid_input', 'Values must be a record.')\n    if key_field not in values:\n        raise CardError('missing_field', f\"Key field '{key_field}' not found in values.\", {'field': key_field})\n    key_value = values[key_field]\n    existing = ctx.store.find(table, where={'field': key_field, 'op': 'eq', 'value': key_value}, limit=1)\n    if existing:\n        record = ctx.store.update(table, existing[0]['id'], values)\n        return {'record': record, 'created': False}\n    record = ctx.store.insert(table, values)\n    return {'record': record, 'created': True}",
  "settings": [
   {
    "name": "table",
    "default": "records"
   },
   {
    "name": "key_field",
    "default": "id"
   }
  ],
  "inputs": [
   "values"
  ],
  "outputs": [
   "record",
   "created"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Define App Settings": {
  "function": "define_app_settings",
  "source": "def define_app_settings(ctx, *, settings: dict, table: str='app_settings') -> dict:\n    if not isinstance(settings, dict) or not settings:\n        raise CardError('invalid_input', 'Settings must be a non-empty record.')\n    with ctx.store.transaction():\n        return _save_settings(ctx, settings, table)",
  "settings": [
   {
    "name": "table",
    "default": "app_settings"
   }
  ],
  "inputs": [
   "settings"
  ],
  "outputs": [
   "record"
  ],
  "runtime": [
   "CardError",
   "check_identifier"
  ],
  "imports": [],
  "helpers": [
   {
    "name": "_save_settings",
    "source": "def _save_settings(ctx, settings: dict, table: str) -> dict:\n    if table not in ctx.store.tables():\n        fields = []\n        for key, value in settings.items():\n            check_identifier(key, 'setting name')\n            if isinstance(value, bool):\n                field_type = 'bool'\n            elif isinstance(value, int):\n                field_type = 'integer'\n            elif isinstance(value, float):\n                field_type = 'number'\n            else:\n                field_type = 'text'\n            fields.append({'name': key, 'type': field_type})\n        ctx.store.define_table(table, fields, if_exists='skip')\n    existing = ctx.store.find(table, limit=1)\n    if existing:\n        record = ctx.store.update(table, existing[0]['id'], settings)\n    else:\n        record = ctx.store.insert(table, settings)\n    return {'record': record}"
   }
  ]
 },
 "Define Choice List": {
  "function": "define_choice_list",
  "source": "def define_choice_list(ctx, *, table: str, field: str, choices: list, type: str='choice', required: bool=False) -> dict:\n    check_identifier(field, 'field name')\n    if not choices:\n        raise CardError('invalid_input', 'Choices list cannot be empty.')\n    if type not in ('choice', 'multichoice'):\n        raise CardError('invalid_input', \"Type must be 'choice' or 'multichoice'.\")\n    spec = {'name': field, 'type': type, 'choices': choices, 'required': required}\n    ctx.store.add_field(table, spec)\n    return {'field_name': field}",
  "settings": [
   {
    "name": "table",
    "required": true
   },
   {
    "name": "field",
    "required": true
   },
   {
    "name": "type",
    "default": "choice"
   },
   {
    "name": "required",
    "default": false
   }
  ],
  "inputs": [
   "choices"
  ],
  "outputs": [
   "field_name"
  ],
  "runtime": [
   "CardError",
   "check_identifier"
  ],
  "imports": []
 },
 "Define Data Table": {
  "function": "define_data_table",
  "source": "def define_data_table(ctx, *, table: str, description: str='', if_exists: str='error') -> dict:\n    check_identifier(table, 'table name')\n    if if_exists not in ('error', 'skip'):\n        raise CardError('invalid_input', \"if_exists must be 'error' or 'skip'.\")\n    ctx.store.define_table(table, [], if_exists=if_exists)\n    return {'table_name': table}",
  "settings": [
   {
    "name": "table",
    "required": true
   },
   {
    "name": "description",
    "default": ""
   },
   {
    "name": "if_exists",
    "default": "error"
   }
  ],
  "inputs": [],
  "outputs": [
   "table_name"
  ],
  "runtime": [
   "CardError",
   "check_identifier"
  ],
  "imports": []
 },
 "Delete Multiple Records": {
  "function": "delete_multiple_records",
  "source": "def delete_multiple_records(ctx, *, ids, table: str='records', limit: int=MAX_LOOP_ITEMS) -> dict:\n    if not isinstance(ids, (list, tuple)):\n        raise CardError('invalid_input', 'IDs must be a list.')\n    id_list = bounded(ids, limit, 'records')\n    ctx.store.schema(table)\n    numbers = [as_int(rec_id, 'id') for rec_id in id_list]\n    count = 0\n    with ctx.store.transaction():\n        for rec_id in numbers:\n            try:\n                ctx.store.delete(table, rec_id)\n                count += 1\n            except CardError as err:\n                if err.code != 'not_found':\n                    raise\n    return {'count': count}",
  "settings": [
   {
    "name": "table",
    "default": "records"
   },
   {
    "name": "limit",
    "default": 10000
   }
  ],
  "inputs": [
   "ids"
  ],
  "outputs": [
   "count"
  ],
  "runtime": [
   "CardError",
   "MAX_LOOP_ITEMS",
   "as_int",
   "bounded"
  ],
  "imports": []
 },
 "Delete Record": {
  "function": "delete_record",
  "source": "def delete_record(ctx, *, id, table: str='records') -> dict:\n    try:\n        rec_id = int(id)\n    except (TypeError, ValueError):\n        raise CardError('invalid_input', 'ID must be a number.') from None\n    record = ctx.store.delete(table, rec_id)\n    return {'record': record}",
  "settings": [
   {
    "name": "table",
    "default": "records"
   }
  ],
  "inputs": [
   "id"
  ],
  "outputs": [
   "record"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Display Barcode From Code": {
  "function": "display_barcode_from_code",
  "source": "def display_barcode_from_code(ctx, *, value='', format: str='code128', width: int=2, height: int=50) -> dict:\n    if not value or (isinstance(value, str) and (not value.strip())):\n        raise CardError('required', 'Barcode value is required.')\n    allowed = ('code128', 'ean13', 'upca', 'qr')\n    if format not in allowed:\n        raise CardError('invalid_input', f\"Format must be one of: {', '.join(allowed)}.\")\n    if width < 1:\n        raise CardError('invalid_input', 'Width must be at least 1.')\n    if height < 1:\n        raise CardError('invalid_input', 'Height must be at least 1.')\n    text = str(value).strip() if isinstance(value, str) else str(value)\n    node = view('display.barcode', value=text, format=format, width=width, height=height)\n    return {'view': node}",
  "settings": [
   {
    "name": "format",
    "default": "code128"
   },
   {
    "name": "width",
    "default": 2
   },
   {
    "name": "height",
    "default": 50
   }
  ],
  "inputs": [
   "value"
  ],
  "outputs": [
   "view"
  ],
  "runtime": [
   "CardError",
   "view"
  ],
  "imports": []
 },
 "Display Record Card": {
  "function": "display_record_card",
  "source": "def display_record_card(ctx, *, record=None, fields=None, layout: str='rows') -> dict:\n    if not isinstance(record, dict):\n        raise CardError('invalid_input', 'Record must be a dict.')\n    flds = fields if isinstance(fields, list) else []\n    for i, fld in enumerate(flds):\n        if not isinstance(fld, dict):\n            raise CardError('invalid_input', f'Field {i + 1} must be a record.')\n        if 'name' not in fld or not isinstance(fld['name'], str):\n            raise CardError('invalid_input', f'Field {i + 1} needs a name.')\n        if 'label' not in fld:\n            fld['label'] = fld['name']\n    if layout not in ('rows', 'compact'):\n        raise CardError('invalid_input', \"Layout must be 'rows' or 'compact'.\")\n    node = view('display.card', record=record, fields=flds, layout=layout)\n    return {'view': node}",
  "settings": [
   {
    "name": "fields",
    "default": null
   },
   {
    "name": "layout",
    "default": "rows"
   }
  ],
  "inputs": [
   "record"
  ],
  "outputs": [
   "view"
  ],
  "runtime": [
   "CardError",
   "view"
  ],
  "imports": []
 },
 "Draft Acceptance Checklist": {
  "function": "draft_acceptance_checklist",
  "source": "def draft_acceptance_checklist(ctx, *, proposal) -> dict:\n    if not isinstance(proposal, dict) or 'checklist' not in proposal:\n        raise CardError('invalid_input', \"Proposal must have a 'checklist' list.\")\n    if not isinstance(proposal['checklist'], list) or not proposal['checklist']:\n        raise CardError('invalid_input', 'Checklist must have at least one item.')\n    valid_categories = {'basic', 'edge_case', 'error_handling'}\n    cleaned = []\n    for item in proposal['checklist']:\n        if not isinstance(item, dict) or 'item' not in item:\n            raise CardError('invalid_input', \"Each checklist item needs an 'item' field.\")\n        category = item.get('category', 'basic')\n        if category not in valid_categories:\n            raise CardError('invalid_input', f'Category must be basic, edge_case, or error_handling (got {category}).')\n        cleaned.append({'item': str(item['item']), 'category': category})\n    return {'checklist': cleaned}",
  "settings": [],
  "inputs": [
   "proposal"
  ],
  "outputs": [
   "checklist"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Draft Field Help Text": {
  "function": "draft_field_help_text",
  "source": "def draft_field_help_text(ctx, *, proposal, max_length: int=200) -> dict:\n    if not isinstance(proposal, dict) or 'help' not in proposal:\n        raise CardError('invalid_input', \"Proposal must have a 'help' list.\")\n    if not isinstance(proposal['help'], list):\n        raise CardError('invalid_input', 'Help must be a list.')\n    cleaned = []\n    for item in proposal['help']:\n        if not isinstance(item, dict) or 'field' not in item or 'text' not in item:\n            raise CardError('invalid_input', \"Each help item needs 'field' and 'text'.\")\n        text = str(item['text']).strip()\n        if len(text) > max_length:\n            raise CardError('too_long', f\"Help text for {item['field']} must be at most {max_length} characters.\")\n        cleaned.append({'field': str(item['field']), 'text': text})\n    return {'help': cleaned}",
  "settings": [
   {
    "name": "max_length",
    "default": 200
   }
  ],
  "inputs": [
   "proposal"
  ],
  "outputs": [
   "help"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Draft Sample Records": {
  "function": "draft_sample_records",
  "source": "def draft_sample_records(ctx, *, proposal, schema: dict) -> dict:\n    if not isinstance(proposal, dict) or 'records' not in proposal:\n        raise CardError('invalid_input', \"Proposal must have a 'records' list.\")\n    if not isinstance(proposal['records'], list) or not proposal['records']:\n        raise CardError('invalid_input', 'Proposal must have at least one record.')\n    if not isinstance(schema, dict):\n        raise CardError('invalid_input', 'Schema must be a field map.')\n    validated = []\n    for rec in proposal['records']:\n        clean = validate_against(schema, rec)\n        validated.append(clean)\n    return {'records': validated}",
  "settings": [
   {
    "name": "schema",
    "required": true
   }
  ],
  "inputs": [
   "proposal"
  ],
  "outputs": [
   "records"
  ],
  "runtime": [
   "CardError",
   "validate_against"
  ],
  "imports": []
 },
 "Draft Validation Rules": {
  "function": "draft_validation_rules",
  "source": "def draft_validation_rules(ctx, *, proposal) -> dict:\n    if not isinstance(proposal, dict) or 'rules' not in proposal:\n        raise CardError('invalid_input', \"Proposal must have a 'rules' list.\")\n    if not isinstance(proposal['rules'], list):\n        raise CardError('invalid_input', 'Rules must be a list.')\n    valid_check_types = {'required', 'range', 'length', 'format', 'unique', 'pattern'}\n    cleaned = []\n    for rule in proposal['rules']:\n        if not isinstance(rule, dict) or 'field' not in rule or 'checks' not in rule:\n            raise CardError('invalid_input', \"Each rule needs 'field' and 'checks'.\")\n        if not isinstance(rule['checks'], list):\n            raise CardError('invalid_input', 'Checks must be a list.')\n        clean_checks = []\n        for check in rule['checks']:\n            if not isinstance(check, dict) or 'type' not in check:\n                raise CardError('invalid_input', \"Each check needs a 'type'.\")\n            if check['type'] not in valid_check_types:\n                raise CardError('invalid_input', f\"Unknown check type: {check['type']}.\")\n            clean_check = {'type': check['type']}\n            if 'params' in check:\n                clean_check['params'] = check['params']\n            clean_checks.append(clean_check)\n        cleaned.append({'field': str(rule['field']), 'checks': clean_checks})\n    return {'rules': cleaned}",
  "settings": [],
  "inputs": [
   "proposal"
  ],
  "outputs": [
   "rules"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Enable Change History Tracking": {
  "function": "enable_change_history_tracking",
  "source": "def enable_change_history_tracking(ctx, *, table: str, keep_versions: int=10) -> dict:\n    if keep_versions < 1:\n        raise CardError('invalid_input', 'keep_versions must be at least 1.')\n    ctx.store.enable_history(table, keep=keep_versions)\n    return {'table_name': table}",
  "settings": [
   {
    "name": "table",
    "required": true
   },
   {
    "name": "keep_versions",
    "default": 10
   }
  ],
  "inputs": [],
  "outputs": [
   "table_name"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Enable Or Disable Field": {
  "function": "enable_or_disable_field",
  "source": "def enable_or_disable_field(ctx, *, record, depends_on_field: str, enable_when_value: str | list=None) -> dict:\n    if not isinstance(record, dict):\n        raise CardError('invalid_input', 'Enable Or Disable Field needs a record.')\n    value = str(get_field(record, depends_on_field, '')).strip().lower()\n    if enable_when_value is None:\n        enabled = True\n    elif isinstance(enable_when_value, list):\n        enabled = any((value == str(v).strip().lower() for v in enable_when_value))\n    else:\n        enabled = value == str(enable_when_value).strip().lower()\n    return {'record': record, 'enabled': enabled}",
  "settings": [
   {
    "name": "depends_on_field",
    "required": true
   },
   {
    "name": "enable_when_value",
    "default": null
   }
  ],
  "inputs": [
   "record"
  ],
  "outputs": [
   "record",
   "enabled"
  ],
  "runtime": [
   "CardError",
   "get_field"
  ],
  "imports": []
 },
 "Enforce Lead Time Limit": {
  "function": "enforce_lead_time_limit",
  "source": "def enforce_lead_time_limit(ctx, *, record, order_field: str='order_date', delivery_field: str='delivery_date', min_days: int=3) -> dict:\n    if not isinstance(record, dict):\n        raise CardError('invalid_input', 'Enforce Lead Time Limit needs a record.')\n    from ..runtime import to_date\n    order_date = to_date(get_field(record, order_field), order_field)\n    delivery_date = to_date(get_field(record, delivery_field), delivery_field)\n    actual_days = (delivery_date - order_date).days\n    if actual_days < min_days:\n        raise CardError('insufficient_lead_time', f'Delivery date must be at least {min_days} days after order date (only {actual_days} days).')\n    return {'record': record}",
  "settings": [
   {
    "name": "order_field",
    "default": "order_date"
   },
   {
    "name": "delivery_field",
    "default": "delivery_date"
   },
   {
    "name": "min_days",
    "default": 3
   }
  ],
  "inputs": [
   "record"
  ],
  "outputs": [
   "record"
  ],
  "runtime": [
   "CardError",
   "get_field"
  ],
  "imports": []
 },
 "Enforce Unique Field Value": {
  "function": "enforce_unique_field_value",
  "source": "def enforce_unique_field_value(ctx, *, table: str, field: str) -> dict:\n    schema = ctx.store.schema(table)['fields']\n    spec = next((f for f in schema if f['name'] == field), None)\n    if spec is None:\n        raise CardError('unknown_field', f\"Field '{field}' not found in table '{table}'.\", {'field': field})\n    ctx.store.update_field(table, field, {'unique': True})\n    return {'field_name': field}",
  "settings": [
   {
    "name": "table",
    "required": true
   },
   {
    "name": "field",
    "required": true
   }
  ],
  "inputs": [],
  "outputs": [
   "field_name"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Enter Currency Amount": {
  "function": "enter_currency_amount",
  "source": "def enter_currency_amount(ctx, *, value=None, name: str='amount', label: str='Amount', required: bool=False, min_value=None, max_value=None, currency: str='USD', help_text: str='') -> dict:\n    spec = {'type': 'currency', 'required': required, 'min': min_value, 'max': max_value}\n    clean = coerce_value(spec, value, label)\n    node = view('input.currency', id=name, label=label, value=clean, required=required, min=min_value, max=max_value, currency=currency, help=help_text)\n    return {'view': node, 'value': clean}",
  "settings": [
   {
    "name": "name",
    "default": "amount"
   },
   {
    "name": "label",
    "default": "Amount"
   },
   {
    "name": "required",
    "default": false
   },
   {
    "name": "min_value",
    "default": null
   },
   {
    "name": "max_value",
    "default": null
   },
   {
    "name": "currency",
    "default": "USD"
   },
   {
    "name": "help_text",
    "default": ""
   }
  ],
  "inputs": [
   "value"
  ],
  "outputs": [
   "view",
   "value"
  ],
  "runtime": [
   "coerce_value",
   "view"
  ],
  "imports": []
 },
 "Enter Email Address": {
  "function": "enter_email_address",
  "source": "def enter_email_address(ctx, *, value=None, name: str='email', label: str='Email Address', required: bool=False, placeholder: str='', help_text: str='') -> dict:\n    spec = {'type': 'email', 'required': required}\n    clean = coerce_value(spec, value, label)\n    node = view('input.email', id=name, label=label, value=clean or '', required=required, placeholder=placeholder, help=help_text)\n    return {'view': node, 'value': clean}",
  "settings": [
   {
    "name": "name",
    "default": "email"
   },
   {
    "name": "label",
    "default": "Email Address"
   },
   {
    "name": "required",
    "default": false
   },
   {
    "name": "placeholder",
    "default": ""
   },
   {
    "name": "help_text",
    "default": ""
   }
  ],
  "inputs": [
   "value"
  ],
  "outputs": [
   "view",
   "value"
  ],
  "runtime": [
   "coerce_value",
   "view"
  ],
  "imports": []
 },
 "Enter Number": {
  "function": "enter_number",
  "source": "def enter_number(ctx, *, value=None, name: str='number', label: str='Number', required: bool=False, min_value=None, max_value=None, placeholder: str='', help_text: str='') -> dict:\n    spec = {'type': 'number', 'required': required, 'min': min_value, 'max': max_value}\n    clean = coerce_value(spec, value, label)\n    node = view('input.number', id=name, label=label, value=clean, required=required, min=min_value, max=max_value, placeholder=placeholder, help=help_text)\n    return {'view': node, 'value': clean}",
  "settings": [
   {
    "name": "name",
    "default": "number"
   },
   {
    "name": "label",
    "default": "Number"
   },
   {
    "name": "required",
    "default": false
   },
   {
    "name": "min_value",
    "default": null
   },
   {
    "name": "max_value",
    "default": null
   },
   {
    "name": "placeholder",
    "default": ""
   },
   {
    "name": "help_text",
    "default": ""
   }
  ],
  "inputs": [
   "value"
  ],
  "outputs": [
   "view",
   "value"
  ],
  "runtime": [
   "coerce_value",
   "view"
  ],
  "imports": []
 },
 "Enter Outside Result": {
  "function": "enter_outside_result",
  "source": "def enter_outside_result(ctx, *, item, value=None, field_type: str='text', field_label: str='Result', required: bool=True) -> dict:\n    if not isinstance(item, dict):\n        raise CardError('invalid_input', 'Item must be a record.')\n    if 'key' not in item:\n        raise CardError('missing_field', \"Item must have a 'key' field.\", {'fields': ['key']})\n    spec = {'type': field_type, 'required': required}\n    clean = coerce_value(spec, value, field_label)\n    kind_map = {'text': 'input.text', 'number': 'input.number', 'integer': 'input.number', 'date': 'input.date', 'datetime': 'input.datetime', 'email': 'input.text', 'phone': 'input.text'}\n    kind = kind_map.get(field_type, 'input.text')\n    props = {'label': field_label, 'required': required, 'value': clean, 'item_key': str(item['key'])}\n    if field_type == 'integer':\n        props['integer_only'] = True\n    node = view(kind, props=props)\n    return {'view': node, 'value': clean}",
  "settings": [
   {
    "name": "value",
    "default": null
   },
   {
    "name": "field_type",
    "default": "text"
   },
   {
    "name": "field_label",
    "default": "Result"
   },
   {
    "name": "required",
    "default": true
   }
  ],
  "inputs": [
   "item"
  ],
  "outputs": [
   "view",
   "value"
  ],
  "runtime": [
   "CardError",
   "coerce_value",
   "view"
  ],
  "imports": []
 },
 "Enter Paragraph": {
  "function": "enter_paragraph",
  "source": "def enter_paragraph(ctx, *, value=None, name: str='paragraph', label: str='Paragraph', required: bool=False, max_length: int=1000, placeholder: str='', rows: int=4, help_text: str='') -> dict:\n    spec = {'type': 'text', 'required': required, 'max_length': max_length, 'strip': False}\n    clean = coerce_value(spec, value, label)\n    node = view('input.textarea', id=name, label=label, value=clean or '', required=required, maxLength=max_length, placeholder=placeholder, rows=rows, help=help_text)\n    return {'view': node, 'value': clean}",
  "settings": [
   {
    "name": "name",
    "default": "paragraph"
   },
   {
    "name": "label",
    "default": "Paragraph"
   },
   {
    "name": "required",
    "default": false
   },
   {
    "name": "max_length",
    "default": 1000
   },
   {
    "name": "placeholder",
    "default": ""
   },
   {
    "name": "rows",
    "default": 4
   },
   {
    "name": "help_text",
    "default": ""
   }
  ],
  "inputs": [
   "value"
  ],
  "outputs": [
   "view",
   "value"
  ],
  "runtime": [
   "coerce_value",
   "view"
  ],
  "imports": []
 },
 "Enter Phone Number": {
  "function": "enter_phone_number",
  "source": "def enter_phone_number(ctx, *, value=None, name: str='phone', label: str='Phone Number', required: bool=False, placeholder: str='', help_text: str='') -> dict:\n    spec = {'type': 'phone', 'required': required}\n    clean = coerce_value(spec, value, label)\n    node = view('input.phone', id=name, label=label, value=clean or '', required=required, placeholder=placeholder, help=help_text)\n    return {'view': node, 'value': clean}",
  "settings": [
   {
    "name": "name",
    "default": "phone"
   },
   {
    "name": "label",
    "default": "Phone Number"
   },
   {
    "name": "required",
    "default": false
   },
   {
    "name": "placeholder",
    "default": ""
   },
   {
    "name": "help_text",
    "default": ""
   }
  ],
  "inputs": [
   "value"
  ],
  "outputs": [
   "view",
   "value"
  ],
  "runtime": [
   "coerce_value",
   "view"
  ],
  "imports": []
 },
 "Enter Text": {
  "function": "enter_text",
  "source": "def enter_text(ctx, *, value=None, name: str='text', label: str='Text', required: bool=False, max_length: int=100, placeholder: str='', help_text: str='') -> dict:\n    spec = {'type': 'text', 'required': required, 'max_length': max_length}\n    clean = coerce_value(spec, value, label)\n    node = view('input.text', id=name, label=label, value=clean or '', required=required, maxLength=max_length, placeholder=placeholder, help=help_text)\n    return {'view': node, 'value': clean}",
  "settings": [
   {
    "name": "name",
    "default": "text"
   },
   {
    "name": "label",
    "default": "Text"
   },
   {
    "name": "required",
    "default": false
   },
   {
    "name": "max_length",
    "default": 100
   },
   {
    "name": "placeholder",
    "default": ""
   },
   {
    "name": "help_text",
    "default": ""
   }
  ],
  "inputs": [
   "value"
  ],
  "outputs": [
   "view",
   "value"
  ],
  "runtime": [
   "coerce_value",
   "view"
  ],
  "imports": []
 },
 "Exception List": {
  "function": "exception_list",
  "source": "def exception_list(ctx, *, records, title: str='Exceptions', columns: list=None, max_display: int=100) -> dict:\n    if not isinstance(records, list):\n        raise CardError('invalid_input', 'Exception records must be a list.')\n    items = bounded(records, limit=max_display, what='exception records')\n    cols = columns if columns else []\n    node = view('display.exceptions', title=title, records=items, columns=cols)\n    return {'view': node}",
  "settings": [
   {
    "name": "title",
    "default": "Exceptions"
   },
   {
    "name": "columns",
    "default": null
   },
   {
    "name": "max_display",
    "default": 100
   }
  ],
  "inputs": [
   "records"
  ],
  "outputs": [
   "view"
  ],
  "runtime": [
   "CardError",
   "bounded",
   "view"
  ],
  "imports": []
 },
 "Explain App In Plain Words": {
  "function": "explain_app_in_plain_words",
  "source": "def explain_app_in_plain_words(ctx, *, proposal, max_length: int=1000) -> dict:\n    if not isinstance(proposal, dict) or 'explanation' not in proposal:\n        raise CardError('invalid_input', \"Proposal must have an 'explanation' field.\")\n    text = str(proposal['explanation']).strip()\n    if not text:\n        raise CardError('invalid_input', 'Explanation cannot be empty.')\n    if len(text) > max_length:\n        raise CardError('too_long', f'Explanation must be at most {max_length} characters.')\n    return {'explanation': text}",
  "settings": [
   {
    "name": "max_length",
    "default": 1000
   }
  ],
  "inputs": [
   "proposal"
  ],
  "outputs": [
   "explanation"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Export Table": {
  "function": "export_table",
  "source": "def export_table(ctx, *, table: str, records: list | None=None, filename: str | None=None, format: str='csv', delimiter: str=',', pretty: bool=True) -> dict:\n    if format not in ('csv', 'json'):\n        raise CardError('invalid_input', f'Unknown format: {format}. Use csv or json.')\n    if records is None:\n        records = ctx.store.find(table)\n    if not records:\n        records = []\n    if filename is not None:\n        if not isinstance(filename, str):\n            raise CardError('invalid_input', 'The file name must be text.')\n        filename = _plain_filename(filename)\n    if format == 'json':\n        content = json.dumps(records, indent=2 if pretty else None, ensure_ascii=False)\n        return {'filename': filename or f'{table}.json', 'mime': 'application/json', 'content': content}\n    schema = ctx.store.schema(table)['fields']\n    field_names = [f['name'] for f in schema]\n    output = io.StringIO()\n    writer = csv.DictWriter(output, fieldnames=field_names, delimiter=delimiter, extrasaction='ignore')\n    writer.writeheader()\n    for record in records:\n        writer.writerow({k: csv_safe_cell(v) for k, v in record.items() if k in field_names})\n    return {'filename': filename or f'{table}.csv', 'mime': 'text/csv', 'content': output.getvalue()}",
  "settings": [
   {
    "name": "table",
    "required": true
   },
   {
    "name": "filename",
    "default": null
   },
   {
    "name": "format",
    "default": "csv"
   },
   {
    "name": "delimiter",
    "default": ","
   },
   {
    "name": "pretty",
    "default": true
   }
  ],
  "inputs": [
   "records"
  ],
  "outputs": [
   "filename",
   "mime",
   "content"
  ],
  "runtime": [
   "CardError",
   "csv_safe_cell",
   "json"
  ],
  "imports": [
   "import csv",
   "import io"
  ],
  "helpers": [
   {
    "name": "_plain_filename",
    "source": "def _plain_filename(filename: str) -> str:\n    name = filename.strip()\n    if not name or any((ch in name for ch in '/\\\\:\\x00')) or name in ('.', '..'):\n        raise CardError('bad_filename', 'The file name must be a plain name, with no folder.')\n    return name"
   }
  ]
 },
 "Extract Domain From Email": {
  "function": "extract_domain_from_email",
  "source": "def extract_domain_from_email(ctx, *, email) -> dict:\n    text = str(email).strip().lower() if email else ''\n    if '@' not in text or text.count('@') != 1:\n        raise CardError('bad_format', 'Email must contain one @ sign.')\n    domain = text.split('@')[1]\n    if not domain or '.' not in domain:\n        raise CardError('bad_format', 'Email domain is not valid.')\n    return {'domain': domain}",
  "settings": [],
  "inputs": [
   "email"
  ],
  "outputs": [
   "domain"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Extract Number From Text": {
  "function": "extract_number_from_text",
  "source": "def extract_number_from_text(ctx, *, text) -> dict:\n    s = as_text(text, 'text')\n    match = re.search('-?\\\\d+(?:\\\\.\\\\d+)?', s)\n    if not match:\n        raise CardError('not_a_number', 'No number found in text.')\n    num = try_number(match.group())\n    if num is None:\n        raise CardError('not_a_number', 'No number found in text.')\n    return {'number': num}",
  "settings": [],
  "inputs": [
   "text"
  ],
  "outputs": [
   "number"
  ],
  "runtime": [
   "CardError",
   "as_text",
   "re",
   "try_number"
  ],
  "imports": []
 },
 "Extract Substring": {
  "function": "extract_substring",
  "source": "def extract_substring(ctx, *, text, start: int=0, length: int=10) -> dict:\n    start = as_int(start, 'start')\n    length = as_int(length, 'length')\n    if start < 0:\n        raise CardError('invalid_input', 'Start position cannot be negative.')\n    if length < 0:\n        raise CardError('invalid_input', 'Length cannot be negative.')\n    s = as_text(text, 'text')\n    return {'text': s[start:start + length]}",
  "settings": [
   {
    "name": "start",
    "default": 0
   },
   {
    "name": "length",
    "default": 10
   }
  ],
  "inputs": [
   "text"
  ],
  "outputs": [
   "text"
  ],
  "runtime": [
   "CardError",
   "as_int",
   "as_text"
  ],
  "imports": []
 },
 "Fill Text Template": {
  "function": "fill_text_template",
  "source": "def fill_text_template(ctx, *, record, template: str='{value}') -> dict:\n    if not isinstance(record, dict):\n        raise CardError('invalid_input', 'Record must be a record.')\n    if not isinstance(template, str):\n        raise CardError('invalid_input', 'Template must be text.')\n\n    def value_for(match) -> str:\n        value = get_field(record, match.group(1), '')\n        return '' if value is None else str(value)\n    return {'text': re.sub('\\\\{([a-zA-Z0-9_.]+)\\\\}', value_for, template)}",
  "settings": [
   {
    "name": "template",
    "default": "{value}"
   }
  ],
  "inputs": [
   "record"
  ],
  "outputs": [
   "text"
  ],
  "runtime": [
   "CardError",
   "get_field",
   "re"
  ],
  "imports": []
 },
 "Filter Records By Condition": {
  "function": "filter_records_by_condition",
  "source": "def filter_records_by_condition(ctx, *, records, condition: dict) -> dict:\n    if not isinstance(records, list):\n        raise CardError('invalid_input', 'Records must be a list.')\n    validate_condition(condition)\n    records_list = bounded(records, what='records')\n    filtered = [rec for rec in records_list if isinstance(rec, dict) and matches(rec, condition)]\n    return {'records': filtered}",
  "settings": [
   {
    "name": "condition",
    "required": true
   }
  ],
  "inputs": [
   "records"
  ],
  "outputs": [
   "records"
  ],
  "runtime": [
   "CardError",
   "bounded",
   "matches",
   "validate_condition"
  ],
  "imports": []
 },
 "Filter Records By Date": {
  "function": "filter_records_by_date",
  "source": "def filter_records_by_date(ctx, *, records, compare_date, field: str, operator: str='before', keep_blank: bool=False) -> dict:\n    if not isinstance(records, list):\n        raise CardError('invalid_input', 'Records must be a list.')\n    if operator not in _DATE_OPERATORS:\n        raise CardError('invalid_input', f\"Operator must be one of: {', '.join(_DATE_OPERATORS)}.\")\n    if not isinstance(field, str) or not field.strip():\n        raise CardError('invalid_input', 'Say which date field to compare.')\n    limit = to_date(compare_date, 'compare_date')\n    keep = {'before': lambda d: d < limit, 'after': lambda d: d > limit, 'on': lambda d: d == limit, 'on_or_before': lambda d: d <= limit, 'on_or_after': lambda d: d >= limit}[operator]\n    out = []\n    for rec in bounded(records, what='records'):\n        raw = get_field(rec, field) if isinstance(rec, dict) else None\n        if is_blank(raw):\n            if keep_blank:\n                out.append(rec)\n            continue\n        if keep(to_date(raw, field)):\n            out.append(rec)\n    return {'records': out}",
  "settings": [
   {
    "name": "field",
    "required": true
   },
   {
    "name": "operator",
    "default": "before"
   },
   {
    "name": "keep_blank",
    "default": false
   }
  ],
  "inputs": [
   "records",
   "compare_date"
  ],
  "outputs": [
   "records"
  ],
  "runtime": [
   "CardError",
   "bounded",
   "get_field",
   "is_blank",
   "to_date"
  ],
  "imports": [],
  "helpers": [
   {
    "name": "_DATE_OPERATORS",
    "source": "_DATE_OPERATORS = ('before', 'after', 'on', 'on_or_before', 'on_or_after')"
   }
  ]
 },
 "Find First Matching Record": {
  "function": "find_first_matching_record",
  "source": "def find_first_matching_record(ctx, *, records, condition: dict) -> dict:\n    if not isinstance(records, list):\n        raise CardError('invalid_input', 'Records must be a list.')\n    validate_condition(condition)\n    records_list = bounded(records, what='records')\n    for rec in records_list:\n        if isinstance(rec, dict) and matches(rec, condition):\n            return {'record': rec, 'found': True}\n    return {'record': None, 'found': False}",
  "settings": [
   {
    "name": "condition",
    "required": true
   }
  ],
  "inputs": [
   "records"
  ],
  "outputs": [
   "record",
   "found"
  ],
  "runtime": [
   "CardError",
   "bounded",
   "matches",
   "validate_condition"
  ],
  "imports": []
 },
 "Find Smallest Or Largest Value": {
  "function": "find_smallest_or_largest_value",
  "source": "def find_smallest_or_largest_value(ctx, *, records, field: str='value', mode: str='smallest') -> dict:\n    if mode not in ('smallest', 'largest'):\n        raise CardError('invalid_input', f'Unknown mode: {mode}. Use smallest or largest.')\n    if not isinstance(records, list):\n        raise CardError('invalid_input', f'The {mode} value needs a list of records.')\n    values = []\n    for rec in bounded(records):\n        value = get_field(rec, field)\n        if not is_blank(value):\n            values.append(to_number(value, field))\n    if not values:\n        raise CardError('invalid_input', f'Cannot find the {mode} value: no numeric values found.')\n    return {'value': min(values) if mode == 'smallest' else max(values)}",
  "settings": [
   {
    "name": "field",
    "default": "value"
   },
   {
    "name": "mode",
    "default": "smallest"
   }
  ],
  "inputs": [
   "records"
  ],
  "outputs": [
   "value"
  ],
  "runtime": [
   "CardError",
   "bounded",
   "get_field",
   "is_blank",
   "to_number"
  ],
  "imports": []
 },
 "Flag Record With Error": {
  "function": "flag_record_with_error",
  "source": "def flag_record_with_error(ctx, *, record, has_error: bool=True, error_code: str='error', error_message: str='') -> dict:\n    if not isinstance(record, dict):\n        raise CardError('invalid_input', 'Flag Record With Error needs a record.')\n    if has_error and (not error_code):\n        raise CardError('invalid_input', 'Error code is required when flagging an error.')\n    flagged = dict(record)\n    if has_error:\n        flagged['_error'] = True\n        flagged['_error_code'] = error_code\n        if error_message:\n            flagged['_error_message'] = error_message\n    return {'record': flagged}",
  "settings": [
   {
    "name": "has_error",
    "default": true
   },
   {
    "name": "error_code",
    "default": "error"
   },
   {
    "name": "error_message",
    "default": ""
   }
  ],
  "inputs": [
   "record"
  ],
  "outputs": [
   "record"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Flag Reorder Level Reached": {
  "function": "flag_reorder_level_reached",
  "source": "def flag_reorder_level_reached(ctx, *, record, quantity_field: str='quantity', reorder_field: str='reorder_level') -> dict:\n    if not isinstance(record, dict):\n        raise CardError('invalid_input', 'Flag Reorder Level Reached needs a record.')\n    qty = to_number(get_field(record, quantity_field), quantity_field)\n    reorder = to_number(get_field(record, reorder_field), reorder_field)\n    flag = qty <= reorder\n    reason = f'Quantity {qty} is at or below reorder level {reorder}' if flag else ''\n    return {'record': record, 'flag': flag, 'reason': reason}",
  "settings": [
   {
    "name": "quantity_field",
    "default": "quantity"
   },
   {
    "name": "reorder_field",
    "default": "reorder_level"
   }
  ],
  "inputs": [
   "record"
  ],
  "outputs": [
   "record",
   "flag",
   "reason"
  ],
  "runtime": [
   "CardError",
   "get_field",
   "to_number"
  ],
  "imports": []
 },
 "Flag Unusual Records": {
  "function": "flag_unusual_records",
  "source": "def flag_unusual_records(ctx, *, records, field: str, min: float | None=None, max: float | None=None, flag_field: str='unusual') -> dict:\n    if not isinstance(records, list):\n        raise CardError('invalid_input', 'Records must be a list.')\n    if not field:\n        raise CardError('missing_field', 'A field name is required for checking unusual values.')\n    records_list = bounded(records, what='records')\n    flagged = []\n    for rec in records_list:\n        if not isinstance(rec, dict):\n            flagged.append(rec)\n            continue\n        new_rec = rec.copy()\n        value = get_field(rec, field)\n        unusual = False\n        try:\n            num = to_number(value, field)\n            if min is not None and num < min:\n                unusual = True\n            if max is not None and num > max:\n                unusual = True\n        except CardError:\n            unusual = True\n        new_rec[flag_field] = unusual\n        flagged.append(new_rec)\n    return {'records': flagged}",
  "settings": [
   {
    "name": "field",
    "required": true
   },
   {
    "name": "min",
    "default": null
   },
   {
    "name": "max",
    "default": null
   },
   {
    "name": "flag_field",
    "default": "unusual"
   }
  ],
  "inputs": [
   "records"
  ],
  "outputs": [
   "records"
  ],
  "runtime": [
   "CardError",
   "bounded",
   "get_field",
   "to_number"
  ],
  "imports": []
 },
 "Format Currency Value": {
  "function": "format_currency_value",
  "source": "def format_currency_value(ctx, *, value, symbol: str='$', separator: str=',', decimals: int=2) -> dict:\n    num = round_half_up(to_number(value, 'value'), decimals)\n    sign = '-' if num < 0 else ''\n    num = abs(num)\n    parts = f'{num:.{decimals}f}'.split('.')\n    whole = parts[0]\n    if separator:\n        whole = f'{int(whole):,}'.replace(',', separator)\n    text = f'{sign}{symbol}{whole}.{parts[1]}'\n    return {'text': text}",
  "settings": [
   {
    "name": "symbol",
    "default": "$"
   },
   {
    "name": "separator",
    "default": ","
   },
   {
    "name": "decimals",
    "default": 2
   }
  ],
  "inputs": [
   "value"
  ],
  "outputs": [
   "text"
  ],
  "runtime": [
   "round_half_up",
   "to_number"
  ],
  "imports": []
 },
 "Format Phone Number": {
  "function": "format_phone_number",
  "source": "def format_phone_number(ctx, *, phone, format: str='(###) ###-####') -> dict:\n    text = str(phone) if phone else ''\n    digits = re.sub('\\\\D', '', text)\n    needed = format.count('#')\n    if len(digits) != needed:\n        raise CardError('bad_format', f'Phone number must have {needed} digits (found {len(digits)}).')\n    result = []\n    idx = 0\n    for char in format:\n        if char == '#':\n            result.append(digits[idx])\n            idx += 1\n        else:\n            result.append(char)\n    return {'text': ''.join(result)}",
  "settings": [
   {
    "name": "format",
    "default": "(###) ###-####"
   }
  ],
  "inputs": [
   "phone"
  ],
  "outputs": [
   "text"
  ],
  "runtime": [
   "CardError",
   "re"
  ],
  "imports": []
 },
 "Generate Unique Identifier": {
  "function": "generate_unique_identifier",
  "source": "def generate_unique_identifier(ctx, *, record, field: str='code', prefix: str='ID', counter: str='default') -> dict:\n    if not isinstance(record, dict):\n        raise CardError('invalid_input', 'Record must be a record.')\n    rec = dict(record)\n    num = ctx.store.next_counter(counter)\n    rec[field] = f'{prefix}-{num}'\n    return {'record': rec}",
  "settings": [
   {
    "name": "field",
    "default": "code"
   },
   {
    "name": "prefix",
    "default": "ID"
   },
   {
    "name": "counter",
    "default": "default"
   }
  ],
  "inputs": [
   "record"
  ],
  "outputs": [
   "record"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Get Current Date And Time": {
  "function": "get_current_date_and_time",
  "source": "def get_current_date_and_time(ctx) -> dict:\n    now = ctx.now()\n    return {'date': now.date().isoformat(), 'time': now.time().replace(microsecond=0).isoformat(), 'datetime': iso(now)}",
  "settings": [],
  "inputs": [],
  "outputs": [
   "date",
   "time",
   "datetime"
  ],
  "runtime": [
   "iso"
  ],
  "imports": []
 },
 "Go Back To List": {
  "function": "go_back_to_list",
  "source": "def go_back_to_list(ctx, *, screen: str='list', label: str='Back') -> dict:\n    if not screen.strip():\n        raise CardError('invalid_input', 'Screen name cannot be empty.')\n    node = view('nav.back', screen=screen, label=label)\n    return {'view': node}",
  "settings": [
   {
    "name": "screen",
    "default": "list"
   },
   {
    "name": "label",
    "default": "Back"
   }
  ],
  "inputs": [],
  "outputs": [
   "view"
  ],
  "runtime": [
   "CardError",
   "view"
  ],
  "imports": []
 },
 "Group And Summarize Saved Data": {
  "function": "group_and_summarize_saved_data",
  "source": "def group_and_summarize_saved_data(ctx, *, table: str='records', group_by: str='status', aggregates: list[dict] | None=None, where: dict | None=None, include_archived: bool=False) -> dict:\n    aggs = aggregates if aggregates is not None else []\n    if not isinstance(aggs, list):\n        raise CardError('invalid_input', 'Aggregates must be a list.')\n    records = ctx.store.find(table, where=where, include_archived=include_archived)\n    groups_dict: dict[str, dict] = {}\n    for rec in records:\n        key = str(get_field(rec, group_by, ''))\n        if key not in groups_dict:\n            groups_dict[key] = {group_by: get_field(rec, group_by), '_count': 0, '_records': []}\n        groups_dict[key]['_count'] += 1\n        groups_dict[key]['_records'].append(rec)\n    result = []\n    for group in groups_dict.values():\n        group_result = {group_by: group[group_by], '_count': group['_count']}\n        for agg in aggs:\n            if not isinstance(agg, dict) or 'field' not in agg or 'op' not in agg:\n                raise CardError('invalid_input', \"Each aggregate needs 'field' and 'op'.\")\n            field_name = agg['field']\n            op = agg['op']\n            name = agg.get('name', f'{op}_{field_name}')\n            values = [to_number(get_field(r, field_name), field_name) for r in group['_records'] if get_field(r, field_name) is not None]\n            if op == 'sum':\n                group_result[name] = sum(values) if values else 0\n            elif op == 'avg':\n                group_result[name] = sum(values) / len(values) if values else 0\n            elif op == 'min':\n                group_result[name] = min(values) if values else None\n            elif op == 'max':\n                group_result[name] = max(values) if values else None\n            elif op == 'count':\n                group_result[name] = len(values)\n            else:\n                raise CardError('invalid_input', f'Unknown aggregate operation: {op}.')\n        result.append(group_result)\n    return {'groups': result, 'count': len(result)}",
  "settings": [
   {
    "name": "table",
    "default": "records"
   },
   {
    "name": "group_by",
    "default": "status"
   },
   {
    "name": "aggregates",
    "default": null
   },
   {
    "name": "where",
    "default": null
   },
   {
    "name": "include_archived",
    "default": false
   }
  ],
  "inputs": [],
  "outputs": [
   "groups",
   "count"
  ],
  "runtime": [
   "CardError",
   "get_field",
   "to_number"
  ],
  "imports": []
 },
 "Group Records By Value": {
  "function": "group_records_by_value",
  "source": "def group_records_by_value(ctx, *, records, field: str) -> dict:\n    if not isinstance(records, list):\n        raise CardError('invalid_input', 'Records must be a list.')\n    if not field:\n        raise CardError('missing_field', 'A field name is required for grouping.')\n    records_list = bounded(records, what='records')\n    groups_dict: dict = {}\n    for rec in records_list:\n        if not isinstance(rec, dict):\n            continue\n        value = get_field(rec, field)\n        key = str(value) if value is not None else ''\n        if key not in groups_dict:\n            groups_dict[key] = []\n        groups_dict[key].append(rec)\n    groups = [{'key': key, 'records': recs} for key, recs in groups_dict.items()]\n    return {'groups': groups}",
  "settings": [
   {
    "name": "field",
    "required": true
   }
  ],
  "inputs": [
   "records"
  ],
  "outputs": [
   "groups"
  ],
  "runtime": [
   "CardError",
   "bounded",
   "get_field"
  ],
  "imports": []
 },
 "Grouped Totals View": {
  "function": "grouped_totals_view",
  "source": "def grouped_totals_view(ctx, *, data, group_field: str='category', value_field: str='value', title: str='Grouped Totals', sort_by: str='group') -> dict:\n    if not isinstance(data, list):\n        raise CardError('invalid_input', 'Grouped data must be a list of records.')\n    if not data:\n        raise CardError('invalid_input', 'Grouped view needs at least one record.')\n    groups = bounded(data, limit=1000, what='groups')\n    node = view('display.grouped', title=title, data=groups, group_field=group_field, value_field=value_field, sort_by=sort_by)\n    return {'view': node}",
  "settings": [
   {
    "name": "group_field",
    "default": "category"
   },
   {
    "name": "value_field",
    "default": "value"
   },
   {
    "name": "title",
    "default": "Grouped Totals"
   },
   {
    "name": "sort_by",
    "default": "group"
   }
  ],
  "inputs": [
   "data"
  ],
  "outputs": [
   "view"
  ],
  "runtime": [
   "CardError",
   "bounded",
   "view"
  ],
  "imports": []
 },
 "Handle Error Without Stopping": {
  "function": "handle_error_without_stopping",
  "source": "def handle_error_without_stopping(ctx, *, value, step=None, check_field: str='', required: bool=False) -> dict:\n    if value is None:\n        raise CardError('invalid_input', 'Handle Error Without Stopping needs a value.')\n    if step is not None:\n        if not callable(step):\n            raise CardError('invalid_input', 'Step must be callable.')\n        try:\n            with ctx.store.transaction():\n                value_out = step(value)\n        except CardError as err:\n            return {'ok': False, 'value': value, 'error': err.to_dict()}\n        return {'ok': True, 'value': value_out, 'error': None}\n    if check_field and (not isinstance(check_field, str)):\n        raise CardError('invalid_input', 'Check field must be a field name.')\n    if check_field and required:\n        field_value = get_field(value, check_field) if isinstance(value, dict) else None\n        if is_blank(field_value):\n            return {'ok': False, 'value': value, 'error': {'code': 'required', 'message': f'{check_field} is required.'}}\n    return {'ok': True, 'value': value, 'error': None}",
  "settings": [
   {
    "name": "step",
    "default": null
   },
   {
    "name": "check_field",
    "default": ""
   },
   {
    "name": "required",
    "default": false
   }
  ],
  "inputs": [
   "value"
  ],
  "outputs": [
   "ok",
   "value",
   "error"
  ],
  "runtime": [
   "CardError",
   "get_field",
   "is_blank"
  ],
  "imports": []
 },
 "Import Records": {
  "function": "import_records",
  "source": "def import_records(ctx, *, content: str, table: str, format: str='csv', has_header: bool=True, delimiter: str=',') -> dict:\n    if format not in ('csv', 'json'):\n        raise CardError('invalid_input', f'Unknown format: {format}. Use csv or json.')\n    if not isinstance(content, str):\n        raise CardError('invalid_input', 'Content must be text.')\n    if len(content.encode('utf-8')) > MAX_IMPORT_BYTES:\n        raise CardError('file_too_large', f'File is too large (limit {MAX_IMPORT_BYTES} bytes).')\n    if format == 'json':\n        try:\n            data = json.loads(content)\n        except json.JSONDecodeError as e:\n            raise CardError('invalid_input', f'Invalid JSON: {e}') from None\n        if isinstance(data, dict):\n            records = [data]\n        elif isinstance(data, list):\n            records = data\n        else:\n            raise CardError('invalid_input', 'JSON must be a record or array of records.')\n        if len(records) > MAX_IMPORT_ROWS:\n            raise CardError('too_many_rows', f'Too many rows: {len(records)} (limit {MAX_IMPORT_ROWS}).')\n    else:\n        schema = ctx.store.schema(table)['fields']\n        field_specs = {f['name']: f for f in schema}\n        content = content.lstrip('\\ufeff')\n        if not isinstance(delimiter, str) or len(delimiter) != 1:\n            raise CardError('invalid_input', 'Delimiter must be one character.')\n        reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)\n        if not has_header:\n            field_names = [f['name'] for f in schema]\n            reader = csv.DictReader(io.StringIO(content), fieldnames=field_names, delimiter=delimiter)\n        elif not any((name in field_specs for name in reader.fieldnames or [])):\n            raise CardError('no_matching_columns', 'No column in the file matches a field of the table.', {'columns': list(reader.fieldnames or [])})\n        rows = list(reader)\n        if len(rows) > MAX_IMPORT_ROWS:\n            raise CardError('too_many_rows', f'Too many rows: {len(rows)} (limit {MAX_IMPORT_ROWS}).')\n        records = [{k: v for k, v in row.items() if k in field_specs} for row in rows]\n    stored = ctx.store.insert_many(table, records, MAX_IMPORT_ROWS)\n    return {'count': len(stored), 'records': stored}",
  "settings": [
   {
    "name": "table",
    "required": true
   },
   {
    "name": "format",
    "default": "csv"
   },
   {
    "name": "has_header",
    "default": true
   },
   {
    "name": "delimiter",
    "default": ","
   }
  ],
  "inputs": [
   "content"
  ],
  "outputs": [
   "count",
   "records"
  ],
  "runtime": [
   "CardError",
   "MAX_IMPORT_BYTES",
   "MAX_IMPORT_ROWS",
   "json"
  ],
  "imports": [
   "import csv",
   "import io"
  ]
 },
 "Import Result File": {
  "function": "import_result_file",
  "source": "def import_result_file(ctx, *, item, filename=None, content=None, accepted_types: list=None, label: str='Upload result file') -> dict:\n    if not isinstance(item, dict):\n        raise CardError('invalid_input', 'Item must be a record.')\n    if 'key' not in item:\n        raise CardError('missing_field', \"Item must have a 'key' field.\", {'fields': ['key']})\n    types = accepted_types or ['csv', 'json', 'txt']\n    if not isinstance(types, (list, tuple)):\n        raise CardError('invalid_input', 'Accepted types must be a list.')\n    props = {'label': label, 'accepted_types': list(types), 'item_key': str(item['key'])}\n    if filename is not None:\n        props['filename'] = str(filename)\n    node = view('input.file', props=props)\n    return {'view': node, 'content': content, 'filename': filename}",
  "settings": [
   {
    "name": "filename",
    "default": null
   },
   {
    "name": "content",
    "default": null
   },
   {
    "name": "accepted_types",
    "default": null
   },
   {
    "name": "label",
    "default": "Upload result file"
   }
  ],
  "inputs": [
   "item"
  ],
  "outputs": [
   "view",
   "content",
   "filename"
  ],
  "runtime": [
   "CardError",
   "view"
  ],
  "imports": []
 },
 "Join Records Into List": {
  "function": "join_records_into_list",
  "source": "def join_records_into_list(ctx, *, record_1, record_2, additional: list | None=None) -> dict:\n    if not isinstance(record_1, dict):\n        raise CardError('invalid_input', 'First record must be a record.')\n    if not isinstance(record_2, dict):\n        raise CardError('invalid_input', 'Second record must be a record.')\n    records = [record_1, record_2]\n    if additional:\n        if not isinstance(additional, list):\n            raise CardError('invalid_input', 'Additional records must be a list.')\n        records.extend(additional)\n    return {'records': records}",
  "settings": [
   {
    "name": "additional",
    "default": null
   }
  ],
  "inputs": [
   "record_1",
   "record_2"
  ],
  "outputs": [
   "records"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Join Related Tables": {
  "function": "join_related_tables",
  "source": "def join_related_tables(ctx, *, left_records, right_table: str, left_key: str='id', right_key: str='id', nested_name: str | None=None, limit: int=MAX_LOOP_ITEMS) -> dict:\n    if not isinstance(left_records, (list, tuple)):\n        raise CardError('invalid_input', 'Left records must be a list.')\n    ctx.store.schema(right_table)\n    items = bounded(left_records, limit, 'records')\n    nested = nested_name or right_table.rstrip('s')\n    result = []\n    for rec in items:\n        joined = dict(rec)\n        key_value = get_field(rec, left_key)\n        if key_value is not None:\n            matches = ctx.store.find(right_table, where={'field': right_key, 'op': 'eq', 'value': key_value}, limit=1)\n            joined[nested] = matches[0] if matches else None\n        else:\n            joined[nested] = None\n        result.append(joined)\n    return {'records': result, 'count': len(result)}",
  "settings": [
   {
    "name": "right_table",
    "required": true
   },
   {
    "name": "left_key",
    "default": "id"
   },
   {
    "name": "right_key",
    "default": "id"
   },
   {
    "name": "nested_name",
    "default": null
   },
   {
    "name": "limit",
    "default": 10000
   }
  ],
  "inputs": [
   "left_records"
  ],
  "outputs": [
   "records",
   "count"
  ],
  "runtime": [
   "CardError",
   "MAX_LOOP_ITEMS",
   "bounded",
   "get_field"
  ],
  "imports": []
 },
 "Keep Only Selected Fields": {
  "function": "keep_only_selected_fields",
  "source": "def keep_only_selected_fields(ctx, *, record, fields: list[str]) -> dict:\n    if not isinstance(record, dict):\n        raise CardError('invalid_input', 'Input must be a record.')\n    if not isinstance(fields, list):\n        raise CardError('invalid_input', 'Fields must be a list.')\n    selected = {}\n    for field in fields:\n        if field in record:\n            selected[field] = record[field]\n    return {'record': selected}",
  "settings": [
   {
    "name": "fields",
    "required": true
   }
  ],
  "inputs": [
   "record"
  ],
  "outputs": [
   "record"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Label Text By Keywords": {
  "function": "label_text_by_keywords",
  "source": "def label_text_by_keywords(ctx, *, record, field: str='text', keywords: dict, label_field: str='label', default: str='') -> dict:\n    if not keywords:\n        raise CardError('invalid_input', 'At least one keyword is required.')\n    rec = dict(record)\n    text = str(get_field(rec, field, '')).lower()\n    label = default\n    for keyword, tag in keywords.items():\n        if keyword.lower() in text:\n            label = tag\n            break\n    rec[label_field] = label\n    return {'record': rec}",
  "settings": [
   {
    "name": "field",
    "default": "text"
   },
   {
    "name": "keywords",
    "required": true
   },
   {
    "name": "label_field",
    "default": "label"
   },
   {
    "name": "default",
    "default": ""
   }
  ],
  "inputs": [
   "record"
  ],
  "outputs": [
   "record"
  ],
  "runtime": [
   "CardError",
   "get_field"
  ],
  "imports": []
 },
 "Link Tables By Relationship": {
  "function": "link_tables_by_relationship",
  "source": "def link_tables_by_relationship(ctx, *, from_table: str, field: str, to_table: str, required: bool=False, protect_delete: bool=False) -> dict:\n    check_identifier(field, 'field name')\n    if from_table not in ctx.store.tables():\n        raise CardError('no_such_table', f\"Table '{from_table}' does not exist.\")\n    if to_table not in ctx.store.tables():\n        raise CardError('no_such_table', f\"Table '{to_table}' does not exist.\")\n    spec = {'name': field, 'type': 'integer', 'required': required, 'references': to_table, 'protect_delete': protect_delete}\n    ctx.store.add_field(from_table, spec)\n    return {'field_name': field}",
  "settings": [
   {
    "name": "from_table",
    "required": true
   },
   {
    "name": "field",
    "required": true
   },
   {
    "name": "to_table",
    "required": true
   },
   {
    "name": "required",
    "default": false
   },
   {
    "name": "protect_delete",
    "default": false
   }
  ],
  "inputs": [],
  "outputs": [
   "field_name"
  ],
  "runtime": [
   "CardError",
   "check_identifier"
  ],
  "imports": []
 },
 "List Records": {
  "function": "list_records",
  "source": "def list_records(ctx, *, records=None, title_field: str='', subtitle_field: str='', icon_field: str='') -> dict:\n    if not isinstance(records, list):\n        raise CardError('invalid_input', 'Records must be a list.')\n    if not title_field or not isinstance(title_field, str):\n        raise CardError('required', 'Title field is required.')\n    items = bounded(records, what='records')\n    node = view('display.list', records=items, title_field=title_field, subtitle_field=subtitle_field, icon_field=icon_field)\n    return {'view': node}",
  "settings": [
   {
    "name": "title_field",
    "default": ""
   },
   {
    "name": "subtitle_field",
    "default": ""
   },
   {
    "name": "icon_field",
    "default": ""
   }
  ],
  "inputs": [
   "records"
  ],
  "outputs": [
   "view"
  ],
  "runtime": [
   "CardError",
   "bounded",
   "view"
  ],
  "imports": []
 },
 "Load Sample Data Set": {
  "function": "load_sample_data_set",
  "source": "def load_sample_data_set(ctx, *, table: str, sample_data: list | None=None) -> dict:\n    ctx.store.schema(table)\n    if sample_data is not None:\n        if not isinstance(sample_data, list):\n            raise CardError('invalid_input', 'sample_data must be a list of records.')\n        records = sample_data\n    else:\n        schema = ctx.store.schema(table)['fields']\n        records = []\n        for i in range(3):\n            record = {}\n            for field in schema:\n                fname = field['name']\n                ftype = field['type']\n                if ftype == 'text':\n                    record[fname] = f'Sample {i + 1}'\n                elif ftype in ('number', 'currency'):\n                    record[fname] = (i + 1) * 10.0\n                elif ftype == 'integer':\n                    record[fname] = (i + 1) * 10\n                elif ftype == 'bool':\n                    record[fname] = i % 2 == 0\n                elif ftype == 'date':\n                    record[fname] = f'2026-01-{i + 1:02d}'\n                elif ftype == 'email':\n                    record[fname] = f'user{i + 1}@example.com'\n                elif ftype == 'phone':\n                    record[fname] = '555-0100'\n                elif ftype == 'time':\n                    record[fname] = f'{9 + i:02d}:00'\n                elif ftype == 'datetime':\n                    record[fname] = f'2026-01-{i + 1:02d}T09:00:00'\n                elif ftype in ('choice', 'multichoice') and field.get('choices'):\n                    first = field['choices'][0]\n                    record[fname] = [first] if ftype == 'multichoice' else first\n            records.append(record)\n    stored = ctx.store.insert_many(table, records, MAX_IMPORT_ROWS)\n    return {'count': len(stored), 'records': stored}",
  "settings": [
   {
    "name": "table",
    "required": true
   }
  ],
  "inputs": [
   "sample_data"
  ],
  "outputs": [
   "count",
   "records"
  ],
  "runtime": [
   "CardError",
   "MAX_IMPORT_ROWS"
  ],
  "imports": []
 },
 "Log Error Details": {
  "function": "log_error_details",
  "source": "def log_error_details(ctx, *, error, kind: str='error') -> dict:\n    if error is None:\n        raise CardError('invalid_input', 'Error information is required.')\n    if not kind or not isinstance(kind, str):\n        raise CardError('invalid_input', 'Error kind is required.')\n    if isinstance(error, dict):\n        message = error.get('message', str(error))\n        details = error\n    else:\n        message = str(error)\n        details = {'error': message}\n    ctx.store.log_event(kind, message, details)\n    return {'logged': True, 'event_kind': kind}",
  "settings": [
   {
    "name": "kind",
    "default": "error"
   }
  ],
  "inputs": [
   "error"
  ],
  "outputs": [
   "logged",
   "event_kind"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Log Outside Action": {
  "function": "log_outside_action",
  "source": "def log_outside_action(ctx, *, item, result, action: str='completed', details: dict=None) -> dict:\n    if not isinstance(item, dict):\n        raise CardError('invalid_input', 'Item must be a record.')\n    if 'key' not in item:\n        raise CardError('missing_field', \"Item must have a 'key' field.\", {'fields': ['key']})\n    if not isinstance(result, dict):\n        raise CardError('invalid_input', 'Result must be a record.')\n    import json\n    kind = item.get('kind', 'outside_action')\n    message = f\"{action.capitalize()} outside action for {item['key']}\"\n    log_details = details or {}\n    log_details.update({'item_key': item['key'], 'kind': kind, 'result': result})\n    ctx.store.log_event(kind, message, log_details)\n    return {'logged': True}",
  "settings": [
   {
    "name": "action",
    "default": "completed"
   },
   {
    "name": "details",
    "default": null
   }
  ],
  "inputs": [
   "item",
   "result"
  ],
  "outputs": [
   "logged"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Mark Item Outcome": {
  "function": "mark_item_outcome",
  "source": "def mark_item_outcome(ctx, *, item, result, outcome: str='done', table: str='_vp_outbox', result_field: str='result') -> dict:\n    if not isinstance(item, dict):\n        raise CardError('invalid_input', 'Item must be a record.')\n    if 'key' not in item:\n        raise CardError('missing_field', \"Item must have a 'key' field.\", {'fields': ['key']})\n    if outcome not in ('done', 'failed'):\n        raise CardError('not_allowed', \"Outcome must be 'done' or 'failed'.\", {'allowed': ['done', 'failed']})\n    key = str(item['key'])\n    if table == '_vp_outbox':\n        ctx.store.outbox_set(key, outcome, result)\n        return {'item': ctx.store.outbox_get(key)}\n    records = ctx.store.find(table, where={'field': 'key', 'op': 'eq', 'value': key}, limit=1)\n    if not records:\n        raise CardError('not_found', f\"No item found with key '{key}'.\", {'key': key})\n    changes = {'status': outcome}\n    if result_field in ctx.store.field_names(table):\n        changes[result_field] = result if isinstance(result, str) else json.dumps(result)\n    updated = ctx.store.update(table, records[0]['id'], changes)\n    return {'item': updated}",
  "settings": [
   {
    "name": "outcome",
    "default": "done"
   },
   {
    "name": "table",
    "default": "_vp_outbox"
   },
   {
    "name": "result_field",
    "default": "result"
   }
  ],
  "inputs": [
   "item",
   "result"
  ],
  "outputs": [
   "item"
  ],
  "runtime": [
   "CardError",
   "json"
  ],
  "imports": []
 },
 "Match Format Pattern": {
  "function": "match_format_pattern",
  "source": "def match_format_pattern(ctx, *, value, field: str='value', format_type: str='email', pattern: str='') -> dict:\n    if format_type == 'email':\n        spec = {'type': 'email', 'required': True}\n    elif format_type == 'phone':\n        spec = {'type': 'phone', 'required': True}\n    elif format_type == 'custom':\n        spec = {'type': 'text', 'required': True, 'pattern': pattern}\n    else:\n        raise CardError('invalid_input', f'Unknown format type: {format_type}.')\n    clean = coerce_value(spec, value, field)\n    return {'value': clean}",
  "settings": [
   {
    "name": "field",
    "default": "value"
   },
   {
    "name": "format_type",
    "default": "email"
   },
   {
    "name": "pattern",
    "default": ""
   }
  ],
  "inputs": [
   "value"
  ],
  "outputs": [
   "value"
  ],
  "runtime": [
   "CardError",
   "coerce_value"
  ],
  "imports": []
 },
 "Match Result To Item": {
  "function": "match_result_to_item",
  "source": "def match_result_to_item(ctx, *, result, items, key_field: str='item_key') -> dict:\n    if not isinstance(result, dict):\n        raise CardError('invalid_input', 'Result must be a record.')\n    if key_field not in result:\n        raise CardError('missing_field', f\"Result must have a '{key_field}' field.\", {'fields': [key_field]})\n    if not isinstance(items, (list, tuple)):\n        raise CardError('invalid_input', 'Items must be a list.')\n    target_key = str(result[key_field])\n    matched = None\n    for item in items:\n        if isinstance(item, dict) and str(item.get('key')) == target_key:\n            matched = item\n            break\n    if matched is None:\n        raise CardError('not_found', f\"No item found with key '{target_key}'.\", {'key': target_key})\n    return {'matched_item': matched, 'result': result}",
  "settings": [
   {
    "name": "key_field",
    "default": "item_key"
   }
  ],
  "inputs": [
   "result",
   "items"
  ],
  "outputs": [
   "matched_item",
   "result"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Merge Two Lists": {
  "function": "merge_two_lists",
  "source": "def merge_two_lists(ctx, *, list_a, list_b, remove_duplicates: bool=False, unique_fields: list[str] | None=None) -> dict:\n    if not isinstance(list_a, list):\n        raise CardError('invalid_input', 'First list must be a list.')\n    if not isinstance(list_b, list):\n        raise CardError('invalid_input', 'Second list must be a list.')\n    combined = bounded(list_a + list_b, what='records')\n    if not remove_duplicates:\n        return {'records': combined}\n    if not unique_fields:\n        unique_fields = []\n    seen = set()\n    unique = []\n    for rec in combined:\n        if not isinstance(rec, dict):\n            unique.append(rec)\n            continue\n        if unique_fields:\n            key = tuple((get_field(rec, field) for field in unique_fields))\n        else:\n            key = tuple(sorted(rec.items()))\n        if key not in seen:\n            seen.add(key)\n            unique.append(rec)\n    return {'records': unique}",
  "settings": [
   {
    "name": "remove_duplicates",
    "default": false
   },
   {
    "name": "unique_fields",
    "default": null
   }
  ],
  "inputs": [
   "list_a",
   "list_b"
  ],
  "outputs": [
   "records"
  ],
  "runtime": [
   "CardError",
   "bounded",
   "get_field"
  ],
  "imports": []
 },
 "Merge Two Records": {
  "function": "merge_two_records",
  "source": "def merge_two_records(ctx, *, record_a, record_b, strategy: str='overwrite') -> dict:\n    if not isinstance(record_a, dict):\n        raise CardError('invalid_input', 'First input must be a record.')\n    if not isinstance(record_b, dict):\n        raise CardError('invalid_input', 'Second input must be a record.')\n    merged = record_a.copy()\n    if strategy == 'overwrite':\n        merged.update(record_b)\n    elif strategy == 'keep_first':\n        for key, value in record_b.items():\n            if key not in merged:\n                merged[key] = value\n    else:\n        merged.update(record_b)\n    return {'record': merged}",
  "settings": [
   {
    "name": "strategy",
    "default": "overwrite"
   }
  ],
  "inputs": [
   "record_a",
   "record_b"
  ],
  "outputs": [
   "record"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Open Detail Screen": {
  "function": "open_detail_screen",
  "source": "def open_detail_screen(ctx, *, record=None, screen: str='detail', title: str='') -> dict:\n    if record is None:\n        raise CardError('required', 'Detail screen needs a record.')\n    if not isinstance(record, dict):\n        raise CardError('invalid_input', 'Record must be a record.')\n    node = view('nav.detail', screen=screen, record=record, title=title)\n    return {'view': node}",
  "settings": [
   {
    "name": "screen",
    "default": "detail"
   },
   {
    "name": "title",
    "default": ""
   }
  ],
  "inputs": [
   "record"
  ],
  "outputs": [
   "view"
  ],
  "runtime": [
   "CardError",
   "view"
  ],
  "imports": []
 },
 "Open Pop-Up Panel": {
  "function": "open_pop_up_panel",
  "source": "def open_pop_up_panel(ctx, *, content=None, title: str='', size: str='medium', dismissible: bool=True) -> dict:\n    if content is None:\n        raise CardError('required', 'Pop-up panel needs content.')\n    if not isinstance(content, dict) or 'kind' not in content:\n        raise CardError('invalid_input', 'Content must be a view node.')\n    node = view('dialog.panel', title=title, size=size, dismissible=dismissible, children=[content])\n    return {'view': node}",
  "settings": [
   {
    "name": "title",
    "default": ""
   },
   {
    "name": "size",
    "default": "medium"
   },
   {
    "name": "dismissible",
    "default": true
   }
  ],
  "inputs": [
   "content"
  ],
  "outputs": [
   "view"
  ],
  "runtime": [
   "CardError",
   "view"
  ],
  "imports": []
 },
 "Organize In Tabs": {
  "function": "organize_in_tabs",
  "source": "def organize_in_tabs(ctx, *, tabs=None) -> dict:\n    if not isinstance(tabs, list) or not tabs:\n        raise CardError('invalid_input', 'Tabs must be a list with at least one tab.')\n    for i, tab in enumerate(tabs):\n        if not isinstance(tab, dict):\n            raise CardError('invalid_input', f'Tab {i + 1} must be a record.')\n        if 'label' not in tab or not isinstance(tab['label'], str):\n            raise CardError('invalid_input', f'Tab {i + 1} needs a label.')\n        if 'children' not in tab or not isinstance(tab['children'], list):\n            raise CardError('invalid_input', f'Tab {i + 1} needs a children list.')\n    node = view('layout.tabs', tabs=tabs)\n    return {'view': node}",
  "settings": [],
  "inputs": [
   "tabs"
  ],
  "outputs": [
   "view"
  ],
  "runtime": [
   "CardError",
   "view"
  ],
  "imports": []
 },
 "Paginate Record List": {
  "function": "paginate_record_list",
  "source": "def paginate_record_list(ctx, *, records, page: int=1, page_size: int=10) -> dict:\n    if not isinstance(records, list):\n        raise CardError('invalid_input', 'Records must be a list.')\n    page = as_int(page, 'page')\n    page_size = as_int(page_size, 'page_size')\n    if page < 1:\n        raise CardError('invalid_input', 'Page number must be at least 1.')\n    if page_size < 1:\n        raise CardError('invalid_input', 'Page size must be at least 1.')\n    records_list = bounded(records, what='records')\n    total = len(records_list)\n    total_pages = (total + page_size - 1) // page_size if total > 0 else 1\n    start = (page - 1) * page_size\n    end = start + page_size\n    page_records = records_list[start:end]\n    return {'records': page_records, 'total': total, 'page': page, 'page_size': page_size, 'total_pages': total_pages}",
  "settings": [
   {
    "name": "page",
    "default": 1
   },
   {
    "name": "page_size",
    "default": 10
   }
  ],
  "inputs": [
   "records"
  ],
  "outputs": [
   "records",
   "total",
   "page",
   "page_size",
   "total_pages"
  ],
  "runtime": [
   "CardError",
   "as_int",
   "bounded"
  ],
  "imports": []
 },
 "Pick Date": {
  "function": "pick_date",
  "source": "def pick_date(ctx, *, value=None, name: str='date', label: str='Date', required: bool=False, min_date=None, max_date=None, help_text: str='') -> dict:\n    spec = {'type': 'date', 'required': required, 'min': min_date, 'max': max_date}\n    clean = coerce_value(spec, value, label)\n    node = view('input.date', id=name, label=label, value=clean, required=required, min=min_date, max=max_date, help=help_text)\n    return {'view': node, 'value': clean}",
  "settings": [
   {
    "name": "name",
    "default": "date"
   },
   {
    "name": "label",
    "default": "Date"
   },
   {
    "name": "required",
    "default": false
   },
   {
    "name": "min_date",
    "default": null
   },
   {
    "name": "max_date",
    "default": null
   },
   {
    "name": "help_text",
    "default": ""
   }
  ],
  "inputs": [
   "value"
  ],
  "outputs": [
   "view",
   "value"
  ],
  "runtime": [
   "coerce_value",
   "view"
  ],
  "imports": []
 },
 "Pick Date Range": {
  "function": "pick_date_range",
  "source": "def pick_date_range(ctx, *, start_date=None, end_date=None, name: str='daterange', label: str='Date Range', required: bool=False, help_text: str='') -> dict:\n    spec_start = {'type': 'date', 'required': required}\n    spec_end = {'type': 'date', 'required': required}\n    start_clean = coerce_value(spec_start, start_date, 'Start date')\n    end_clean = coerce_value(spec_end, end_date, 'End date')\n    if start_clean and end_clean and (start_clean > end_clean):\n        raise CardError('invalid_input', 'Start date must be before or equal to end date.')\n    node = view('input.daterange', id=name, label=label, startDate=start_clean, endDate=end_clean, required=required, help=help_text)\n    return {'view': node, 'start_date': start_clean, 'end_date': end_clean}",
  "settings": [
   {
    "name": "name",
    "default": "daterange"
   },
   {
    "name": "label",
    "default": "Date Range"
   },
   {
    "name": "required",
    "default": false
   },
   {
    "name": "help_text",
    "default": ""
   }
  ],
  "inputs": [
   "start_date",
   "end_date"
  ],
  "outputs": [
   "view",
   "start_date",
   "end_date"
  ],
  "runtime": [
   "CardError",
   "coerce_value",
   "view"
  ],
  "imports": []
 },
 "Pick Field From Records": {
  "function": "pick_field_from_records",
  "source": "def pick_field_from_records(ctx, *, records, field: str, skip_blank: bool=True, unique: bool=False) -> dict:\n    if not isinstance(records, list):\n        raise CardError('invalid_input', 'Records must be a list.')\n    if not isinstance(field, str) or not field.strip():\n        raise CardError('invalid_input', 'Say which field to take.')\n    out = []\n    for rec in bounded(records, what='records'):\n        value = get_field(rec, field) if isinstance(rec, dict) else None\n        if skip_blank and is_blank(value):\n            continue\n        if unique and value in out:\n            continue\n        out.append(value)\n    return {'values': out}",
  "settings": [
   {
    "name": "field",
    "required": true
   },
   {
    "name": "skip_blank",
    "default": true
   },
   {
    "name": "unique",
    "default": false
   }
  ],
  "inputs": [
   "records"
  ],
  "outputs": [
   "values"
  ],
  "runtime": [
   "CardError",
   "bounded",
   "get_field",
   "is_blank"
  ],
  "imports": []
 },
 "Pick From Searchable List": {
  "function": "pick_from_searchable_list",
  "source": "def pick_from_searchable_list(ctx, *, value=None, name: str='autocomplete', label: str='Search and Pick', choices: list=None, required: bool=False, placeholder: str='', help_text: str='') -> dict:\n    if not choices:\n        choices = []\n    spec = {'type': 'choice', 'required': required, 'choices': choices}\n    clean = coerce_value(spec, value, label)\n    node = view('input.autocomplete', id=name, label=label, value=clean, choices=choices, required=required, placeholder=placeholder, help=help_text)\n    return {'view': node, 'value': clean}",
  "settings": [
   {
    "name": "name",
    "default": "autocomplete"
   },
   {
    "name": "label",
    "default": "Search and Pick"
   },
   {
    "name": "choices",
    "default": null
   },
   {
    "name": "required",
    "default": false
   },
   {
    "name": "placeholder",
    "default": ""
   },
   {
    "name": "help_text",
    "default": ""
   }
  ],
  "inputs": [
   "value"
  ],
  "outputs": [
   "view",
   "value"
  ],
  "runtime": [
   "coerce_value",
   "view"
  ],
  "imports": []
 },
 "Pick Time": {
  "function": "pick_time",
  "source": "def pick_time(ctx, *, value=None, name: str='time', label: str='Time', required: bool=False, help_text: str='') -> dict:\n    spec = {'type': 'time', 'required': required}\n    clean = coerce_value(spec, value, label)\n    node = view('input.time', id=name, label=label, value=clean, required=required, help=help_text)\n    return {'view': node, 'value': clean}",
  "settings": [
   {
    "name": "name",
    "default": "time"
   },
   {
    "name": "label",
    "default": "Time"
   },
   {
    "name": "required",
    "default": false
   },
   {
    "name": "help_text",
    "default": ""
   }
  ],
  "inputs": [
   "value"
  ],
  "outputs": [
   "view",
   "value"
  ],
  "runtime": [
   "coerce_value",
   "view"
  ],
  "imports": []
 },
 "Prepare AI Prompt": {
  "function": "prepare_ai_prompt",
  "source": "def prepare_ai_prompt(ctx, *, record, template: str, fields: list, max_length: int=5000) -> dict:\n    if not isinstance(record, dict):\n        raise CardError('invalid_input', 'Record must be a dict.')\n    if not isinstance(fields, list) or not fields:\n        raise CardError('invalid_input', 'Fields list must not be empty.')\n    if not template or not isinstance(template, str):\n        raise CardError('invalid_input', 'Template must be a non-empty string.')\n    context = {}\n    values = {}\n    for field in fields:\n        value = get_field(record, field)\n        if value is None or (isinstance(value, str) and (not value.strip())):\n            raise CardError('missing_field', f'Field {field} is required for the prompt.', {'field': field})\n        context[field] = value\n        key = field.replace('.', '_')\n        values[key] = value\n    for field in fields:\n        template = template.replace('{' + field + '}', '{' + field.replace('.', '_') + '}')\n    try:\n        prompt = template.format(**{field.replace('.', '_'): get_field(record, field) for field in fields})\n    except KeyError as e:\n        raise CardError('missing_field', f'Template refers to a field that was not listed: {e}.', {'field': str(e)}) from None\n    except (IndexError, ValueError, AttributeError):\n        raise CardError('invalid_input', 'Template has a { or } that does not fit.') from None\n    prompt = prompt.strip()\n    if len(prompt) > max_length:\n        raise CardError('too_long', f'Prompt must be at most {max_length} characters (got {len(prompt)}).')\n    return {'prompt': prompt, 'context': context}",
  "settings": [
   {
    "name": "template",
    "required": true
   },
   {
    "name": "fields",
    "required": true
   },
   {
    "name": "max_length",
    "default": 5000
   }
  ],
  "inputs": [
   "record"
  ],
  "outputs": [
   "prompt",
   "context"
  ],
  "runtime": [
   "CardError",
   "get_field"
  ],
  "imports": []
 },
 "Prevent Accidental Delete": {
  "function": "prevent_accidental_delete",
  "source": "def prevent_accidental_delete(ctx, *, table: str, record_id: int) -> dict:\n    record = ctx.store.get(table, record_id)\n    if record is None:\n        raise CardError('not_found', f'Record {record_id} not found in {table}.')\n    for other_table in ctx.store.tables():\n        if other_table == table:\n            continue\n        schema = ctx.store.schema(other_table)['fields']\n        for field_spec in schema:\n            if field_spec.get('references') == table and field_spec.get('protect_delete'):\n                referencing = ctx.store.find(other_table, where={'field': field_spec['name'], 'op': 'eq', 'value': record_id}, limit=1)\n                if referencing:\n                    return {'can_delete': False}\n    return {'can_delete': True}",
  "settings": [
   {
    "name": "table",
    "required": true
   }
  ],
  "inputs": [
   "record_id"
  ],
  "outputs": [
   "can_delete"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Prevent Duplicate Order": {
  "function": "prevent_duplicate_order",
  "source": "def prevent_duplicate_order(ctx, *, record, table: str='orders', key_fields: list=None) -> dict:\n    if not isinstance(record, dict):\n        raise CardError('invalid_input', 'Prevent Duplicate Order needs a record.')\n    keys = key_fields or ['customer', 'item', 'date']\n    for field in keys:\n        if field not in record:\n            raise CardError('missing_field', f'Key field {field} is required.', {'field': field})\n    conditions = [{'field': field, 'op': 'eq', 'value': record[field]} for field in keys]\n    where = {'all': conditions}\n    existing = ctx.store.find(table, where=where, limit=1)\n    if existing:\n        raise CardError('duplicate_order', f\"An order with the same {', '.join(keys)} already exists.\")\n    return {'record': record}",
  "settings": [
   {
    "name": "table",
    "default": "orders"
   },
   {
    "name": "key_fields",
    "default": null
   }
  ],
  "inputs": [
   "record"
  ],
  "outputs": [
   "record"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Prevent Negative Stock": {
  "function": "prevent_negative_stock",
  "source": "def prevent_negative_stock(ctx, *, record, quantity_field: str='quantity', change_field: str='change') -> dict:\n    if not isinstance(record, dict):\n        raise CardError('invalid_input', 'Prevent Negative Stock needs a record.')\n    qty = to_number(get_field(record, quantity_field, 0), quantity_field)\n    change = to_number(get_field(record, change_field, 0), change_field)\n    new_qty = qty + change\n    if new_qty < 0:\n        raise CardError('stock_below_zero', f'Stock cannot fall below zero (would be {new_qty}).')\n    return {'record': record}",
  "settings": [
   {
    "name": "quantity_field",
    "default": "quantity"
   },
   {
    "name": "change_field",
    "default": "change"
   }
  ],
  "inputs": [
   "record"
  ],
  "outputs": [
   "record"
  ],
  "runtime": [
   "CardError",
   "get_field",
   "to_number"
  ],
  "imports": []
 },
 "Print-Friendly Page": {
  "function": "print_friendly_page",
  "source": "def print_friendly_page(ctx, *, content=None, title: str='Document', show_header: bool=False, show_footer: bool=False, page_size: str='A4', orientation: str='portrait') -> dict:\n    if content is None:\n        raise CardError('required', 'Print page needs content.')\n    if not isinstance(content, dict) or 'kind' not in content:\n        raise CardError('invalid_input', 'Content must be a view node.')\n    if orientation not in ('portrait', 'landscape'):\n        orientation = 'portrait'\n    node = view('print.page', title=title, show_header=show_header, show_footer=show_footer, page_size=page_size, orientation=orientation, children=[content])\n    return {'view': node}",
  "settings": [
   {
    "name": "title",
    "default": "Document"
   },
   {
    "name": "show_header",
    "default": false
   },
   {
    "name": "show_footer",
    "default": false
   },
   {
    "name": "page_size",
    "default": "A4"
   },
   {
    "name": "orientation",
    "default": "portrait"
   }
  ],
  "inputs": [
   "content"
  ],
  "outputs": [
   "view"
  ],
  "runtime": [
   "CardError",
   "view"
  ],
  "imports": []
 },
 "Propose Field Mappings": {
  "function": "propose_field_mappings",
  "source": "def propose_field_mappings(ctx, *, proposal) -> dict:\n    if not isinstance(proposal, dict) or 'mappings' not in proposal:\n        raise CardError('invalid_input', \"Proposal must have a 'mappings' list.\")\n    if not isinstance(proposal['mappings'], list):\n        raise CardError('invalid_input', 'Mappings must be a list.')\n    valid_confidence = {'high', 'medium', 'low'}\n    cleaned = []\n    for mapping in proposal['mappings']:\n        if not isinstance(mapping, dict):\n            raise CardError('invalid_input', 'Each mapping must be a record.')\n        if 'import_column' not in mapping or 'record_field' not in mapping:\n            raise CardError('invalid_input', \"Each mapping needs 'import_column' and 'record_field'.\")\n        confidence = mapping.get('confidence', 'medium')\n        if confidence not in valid_confidence:\n            raise CardError('invalid_input', f'Confidence must be high, medium, or low (got {confidence}).')\n        cleaned.append({'import_column': str(mapping['import_column']), 'record_field': str(mapping['record_field']), 'confidence': confidence})\n    return {'mappings': cleaned}",
  "settings": [],
  "inputs": [
   "proposal"
  ],
  "outputs": [
   "mappings"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Query Saved Records By Criteria": {
  "function": "query_saved_records_by_criteria",
  "source": "def query_saved_records_by_criteria(ctx, *, where, table: str='records', order_by: str | None=None, limit: int=MAX_LOOP_ITEMS, offset: int=0, include_archived: bool=False) -> dict:\n    if not isinstance(where, dict):\n        raise CardError('invalid_input', 'Where clause must be a condition record.')\n    records = ctx.store.find(table, where=where, order_by=order_by, limit=limit, offset=offset, include_archived=include_archived)\n    return {'records': records, 'count': len(records)}",
  "settings": [
   {
    "name": "table",
    "default": "records"
   },
   {
    "name": "order_by",
    "default": null
   },
   {
    "name": "limit",
    "default": 10000
   },
   {
    "name": "offset",
    "default": 0
   },
   {
    "name": "include_archived",
    "default": false
   }
  ],
  "inputs": [
   "where"
  ],
  "outputs": [
   "records",
   "count"
  ],
  "runtime": [
   "CardError",
   "MAX_LOOP_ITEMS"
  ],
  "imports": []
 },
 "Rate With Stars": {
  "function": "rate_with_stars",
  "source": "def rate_with_stars(ctx, *, value=None, name: str='rating', label: str='Rating', required: bool=False, max_stars: int=5, help_text: str='') -> dict:\n    spec = {'type': 'integer', 'required': required, 'min': 1, 'max': max_stars}\n    clean = coerce_value(spec, value, label)\n    node = view('input.rating', id=name, label=label, value=clean, maxStars=max_stars, required=required, help=help_text)\n    return {'view': node, 'value': clean}",
  "settings": [
   {
    "name": "name",
    "default": "rating"
   },
   {
    "name": "label",
    "default": "Rating"
   },
   {
    "name": "required",
    "default": false
   },
   {
    "name": "max_stars",
    "default": 5
   },
   {
    "name": "help_text",
    "default": ""
   }
  ],
  "inputs": [
   "value"
  ],
  "outputs": [
   "view",
   "value"
  ],
  "runtime": [
   "coerce_value",
   "view"
  ],
  "imports": []
 },
 "Read Chosen File": {
  "function": "read_chosen_file",
  "source": "def read_chosen_file(ctx, *, filename, content, allowed_types: list | None=None) -> dict:\n    if filename is None or content is None:\n        raise CardError('no_file', 'No file has been chosen yet.')\n    if not isinstance(filename, str) or not isinstance(content, str):\n        raise CardError('invalid_input', 'The file name and the file text must be text.')\n    name = _plain_filename(filename)\n    types = [t.lower() for t in (allowed_types if allowed_types is not None else _FILE_TYPES)]\n    if not any((name.lower().endswith(t) for t in types)):\n        raise CardError('file_type_not_allowed', f\"Only these file types are allowed: {', '.join(types)}.\", {'allowed': types})\n    size = len(content.encode('utf-8'))\n    if size > MAX_IMPORT_BYTES:\n        raise CardError('file_too_large', f'File is too large (limit {MAX_IMPORT_BYTES} bytes).')\n    return {'content': content, 'filename': name, 'size': size}",
  "settings": [
   {
    "name": "allowed_types",
    "default": null
   }
  ],
  "inputs": [
   "filename",
   "content"
  ],
  "outputs": [
   "content",
   "filename",
   "size"
  ],
  "runtime": [
   "CardError",
   "MAX_IMPORT_BYTES"
  ],
  "imports": [],
  "helpers": [
   {
    "name": "_FILE_TYPES",
    "source": "_FILE_TYPES = ('.csv', '.json', '.txt')"
   },
   {
    "name": "_plain_filename",
    "source": "def _plain_filename(filename: str) -> str:\n    name = filename.strip()\n    if not name or any((ch in name for ch in '/\\\\:\\x00')) or name in ('.', '..'):\n        raise CardError('bad_filename', 'The file name must be a plain name, with no folder.')\n    return name"
   }
  ]
 },
 "Read Record By ID": {
  "function": "read_record_by_id",
  "source": "def read_record_by_id(ctx, *, id, table: str='records', include_archived: bool=False) -> dict:\n    try:\n        rec_id = int(id)\n    except (TypeError, ValueError):\n        raise CardError('invalid_input', 'ID must be a number.') from None\n    record = ctx.store.get(table, rec_id)\n    if record is None:\n        raise CardError('not_found', f'Record {rec_id} not found in {table}.')\n    if record.get('_archived') and (not include_archived):\n        raise CardError('not_found', f'Record {rec_id} not found in {table}.')\n    return {'record': record}",
  "settings": [
   {
    "name": "table",
    "default": "records"
   },
   {
    "name": "include_archived",
    "default": false
   }
  ],
  "inputs": [
   "id"
  ],
  "outputs": [
   "record"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Reconcile Stale Result": {
  "function": "reconcile_stale_result",
  "source": "def reconcile_stale_result(ctx, *, result, old_item, current_item, action=None) -> dict:\n    if not isinstance(result, dict):\n        raise CardError('invalid_input', 'Result must be a record.')\n    if not isinstance(old_item, dict) or not isinstance(current_item, dict):\n        raise CardError('invalid_input', 'Both items must be records.')\n    if 'key' not in old_item or 'key' not in current_item:\n        raise CardError('missing_field', \"Both items must have a 'key' field.\", {'fields': ['key']})\n    changed_fields = []\n    all_fields = set(old_item.keys()) | set(current_item.keys())\n    for field in all_fields:\n        if field.startswith('_'):\n            continue\n        if old_item.get(field) != current_item.get(field):\n            changed_fields.append({'field': field, 'old': old_item.get(field), 'new': current_item.get(field)})\n    has_changes = len(changed_fields) > 0\n    props = {'has_changes': has_changes, 'change_count': len(changed_fields), 'old_version': old_item.get('_version', 1), 'current_version': current_item.get('_version', 1)}\n    node = view('display.reconciliation', props=props)\n    return {'view': node, 'action': action}",
  "settings": [
   {
    "name": "action",
    "default": null
   }
  ],
  "inputs": [
   "result",
   "old_item",
   "current_item"
  ],
  "outputs": [
   "view",
   "action"
  ],
  "runtime": [
   "CardError",
   "view"
  ],
  "imports": []
 },
 "Reference Linked Record": {
  "function": "reference_linked_record",
  "source": "def reference_linked_record(ctx, *, record: dict, field: str, table: str='records', referenced_table: str | None=None) -> dict:\n    if not isinstance(record, dict):\n        raise CardError('invalid_input', 'Record must be a dict.')\n    value = record.get(field)\n    if referenced_table is None:\n        schema = ctx.store.schema(table)['fields']\n        spec = next((f for f in schema if f['name'] == field), None)\n        if spec and 'references' in spec:\n            referenced_table = spec['references']\n        else:\n            raise CardError('invalid_input', f\"Field '{field}' is not a reference field.\", {'field': field})\n    schema = ctx.store.schema(table)['fields']\n    spec = next((f for f in schema if f['name'] == field), None)\n    is_required = spec.get('required', False) if spec else False\n    if value is None:\n        if is_required:\n            raise CardError('required', f'{field} is required.', {'field': field})\n        return {'record': record}\n    referenced = ctx.store.get(referenced_table, value)\n    if referenced is None:\n        raise CardError('missing_reference', f'Referenced record not found in {referenced_table}.', {'field': field})\n    return {'record': record}",
  "settings": [
   {
    "name": "field",
    "required": true
   },
   {
    "name": "table",
    "default": "records"
   },
   {
    "name": "referenced_table",
    "default": null
   }
  ],
  "inputs": [
   "record"
  ],
  "outputs": [
   "record"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Reject Future Date": {
  "function": "reject_future_date",
  "source": "def reject_future_date(ctx, *, value, field: str='date') -> dict:\n    date_value = to_date(value, field)\n    today = ctx.today()\n    if date_value > today:\n        raise CardError('too_large', f'{field} cannot be in the future.', {'field': field})\n    return {'value': date_value.isoformat()}",
  "settings": [
   {
    "name": "field",
    "default": "date"
   }
  ],
  "inputs": [
   "value"
  ],
  "outputs": [
   "value"
  ],
  "runtime": [
   "CardError",
   "to_date"
  ],
  "imports": []
 },
 "Reject Invalid Result": {
  "function": "reject_invalid_result",
  "source": "def reject_invalid_result(ctx, *, result, item, max_age_hours: int=24) -> dict:\n    if not isinstance(result, dict):\n        raise CardError('invalid_input', 'Result must be a record.')\n    if not isinstance(item, dict):\n        raise CardError('invalid_input', 'Item must be a record.')\n    if 'item_key' not in result:\n        raise CardError('missing_field', \"Result must have 'item_key'.\", {'fields': ['item_key']})\n    if 'key' not in item:\n        raise CardError('missing_field', \"Item must have 'key'.\", {'fields': ['key']})\n    if str(result['item_key']) != str(item['key']):\n        return {'valid': False, 'reason': 'key_mismatch'}\n    built_on = result.get('item_version')\n    if built_on is not None and item.get('_version') != built_on:\n        return {'valid': False, 'reason': 'stale'}\n    if 'entered_at' in result and max_age_hours > 0:\n        from ..runtime import to_datetime\n        import datetime as dt\n        entered = to_datetime(result['entered_at'])\n        age = (ctx.now() - entered).total_seconds() / 3600\n        if age > max_age_hours:\n            return {'valid': False, 'reason': 'too_old'}\n    return {'valid': True, 'reason': ''}",
  "settings": [
   {
    "name": "max_age_hours",
    "default": 24
   }
  ],
  "inputs": [
   "result",
   "item"
  ],
  "outputs": [
   "valid",
   "reason"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Remove Duplicate Records": {
  "function": "remove_duplicate_records",
  "source": "def remove_duplicate_records(ctx, *, records, fields: list[str]) -> dict:\n    if not isinstance(records, list):\n        raise CardError('invalid_input', 'Records must be a list.')\n    if not fields:\n        raise CardError('missing_field', 'At least one field is required to detect duplicates.')\n    records_list = bounded(records, what='records')\n    seen = set()\n    unique = []\n    for rec in records_list:\n        if not isinstance(rec, dict):\n            continue\n        key = tuple((get_field(rec, field) for field in fields))\n        if key not in seen:\n            seen.add(key)\n            unique.append(rec)\n    return {'records': unique}",
  "settings": [
   {
    "name": "fields",
    "required": true
   }
  ],
  "inputs": [
   "records"
  ],
  "outputs": [
   "records"
  ],
  "runtime": [
   "CardError",
   "bounded",
   "get_field"
  ],
  "imports": []
 },
 "Remove Special Characters": {
  "function": "remove_special_characters",
  "source": "def remove_special_characters(ctx, *, text) -> dict:\n    s = as_text(text, 'text')\n    return {'text': re.sub('[^a-zA-Z0-9\\\\s]', '', s)}",
  "settings": [],
  "inputs": [
   "text"
  ],
  "outputs": [
   "text"
  ],
  "runtime": [
   "as_text",
   "re"
  ],
  "imports": []
 },
 "Rename Record Fields": {
  "function": "rename_record_fields",
  "source": "def rename_record_fields(ctx, *, record, mapping: dict) -> dict:\n    if not isinstance(record, dict):\n        raise CardError('invalid_input', 'Input must be a record.')\n    if not isinstance(mapping, dict):\n        raise CardError('invalid_input', 'Mapping must be a record.')\n    renamed = {}\n    for old_name, value in record.items():\n        new_name = mapping.get(old_name, old_name)\n        renamed[new_name] = value\n    return {'record': renamed}",
  "settings": [
   {
    "name": "mapping",
    "required": true
   }
  ],
  "inputs": [
   "record"
  ],
  "outputs": [
   "record"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Repeat For Each List Item": {
  "function": "repeat_for_each_list_item",
  "source": "def repeat_for_each_list_item(ctx, *, items: list, step: Callable[[dict], dict], limit: int=MAX_LOOP_ITEMS) -> dict:\n    if not isinstance(items, list):\n        raise CardError('invalid_input', 'Items must be a list.')\n    if limit < 1 or limit > MAX_LOOP_ITEMS:\n        raise CardError('invalid_input', f'Limit must be between 1 and {MAX_LOOP_ITEMS}.')\n    bounded(items, limit, 'items')\n    if not callable(step):\n        raise CardError('invalid_input', 'Step must be callable.')\n    results = []\n    for item in items:\n        result = step(item)\n        results.append(result)\n    return {'results': results, 'count': len(results)}",
  "settings": [
   {
    "name": "limit",
    "default": 10000
   }
  ],
  "inputs": [
   "items",
   "step"
  ],
  "outputs": [
   "results",
   "count"
  ],
  "runtime": [
   "Callable",
   "CardError",
   "MAX_LOOP_ITEMS",
   "bounded"
  ],
  "imports": []
 },
 "Replace Text In Field": {
  "function": "replace_text_in_field",
  "source": "def replace_text_in_field(ctx, *, text, find: str, replace: str='') -> dict:\n    s = as_text(text, 'text')\n    if not isinstance(find, str) or find == '':\n        raise CardError('invalid_input', 'Say which text to find.')\n    return {'text': s.replace(find, replace)}",
  "settings": [
   {
    "name": "find",
    "required": true
   },
   {
    "name": "replace",
    "default": ""
   }
  ],
  "inputs": [
   "text"
  ],
  "outputs": [
   "text"
  ],
  "runtime": [
   "CardError",
   "as_text"
  ],
  "imports": []
 },
 "Require Approval Above Amount": {
  "function": "require_approval_above_amount",
  "source": "def require_approval_above_amount(ctx, *, record, amount_field: str='amount', threshold: float=1000) -> dict:\n    if not isinstance(record, dict):\n        raise CardError('invalid_input', 'Require Approval Above Amount needs a record.')\n    amount = to_number(get_field(record, amount_field, 0), amount_field)\n    requires_approval = amount > threshold\n    reason = f'Amount {amount} exceeds approval threshold {threshold}' if requires_approval else ''\n    return {'record': record, 'requires_approval': requires_approval, 'reason': reason}",
  "settings": [
   {
    "name": "amount_field",
    "default": "amount"
   },
   {
    "name": "threshold",
    "default": 1000
   }
  ],
  "inputs": [
   "record"
  ],
  "outputs": [
   "record",
   "requires_approval",
   "reason"
  ],
  "runtime": [
   "CardError",
   "get_field",
   "to_number"
  ],
  "imports": []
 },
 "Require Dependent Field": {
  "function": "require_dependent_field",
  "source": "def require_dependent_field(ctx, *, value, trigger_field: str='trigger', trigger_value: str='yes', dependent_field: str='dependent') -> dict:\n    trigger = get_field(value, trigger_field)\n    dependent = get_field(value, dependent_field)\n    field_required = str(trigger).strip().casefold() == str(trigger_value).strip().casefold()\n    if field_required and is_blank(dependent):\n        raise CardError('required', f'{dependent_field} is required when {trigger_field} is {trigger_value}.', {'field': dependent_field})\n    return {'value': value, 'field_required': field_required}",
  "settings": [
   {
    "name": "trigger_field",
    "default": "trigger"
   },
   {
    "name": "trigger_value",
    "default": "yes"
   },
   {
    "name": "dependent_field",
    "default": "dependent"
   }
  ],
  "inputs": [
   "value"
  ],
  "outputs": [
   "value",
   "field_required"
  ],
  "runtime": [
   "CardError",
   "get_field",
   "is_blank"
  ],
  "imports": []
 },
 "Require Either Or Field": {
  "function": "require_either_or_field",
  "source": "def require_either_or_field(ctx, *, value, field_a: str='field_a', field_b: str='field_b') -> dict:\n    val_a = get_field(value, field_a)\n    val_b = get_field(value, field_b)\n    if is_blank(val_a) and is_blank(val_b):\n        raise CardError('required', f'At least one of {field_a} or {field_b} is required.', {'field_a': field_a, 'field_b': field_b})\n    return {'value': value}",
  "settings": [
   {
    "name": "field_a",
    "default": "field_a"
   },
   {
    "name": "field_b",
    "default": "field_b"
   }
  ],
  "inputs": [
   "value"
  ],
  "outputs": [
   "value"
  ],
  "runtime": [
   "CardError",
   "get_field",
   "is_blank"
  ],
  "imports": []
 },
 "Restore Previous Record Version": {
  "function": "restore_previous_record_version",
  "source": "def restore_previous_record_version(ctx, *, id, table: str='records', version: int | None=None) -> dict:\n    try:\n        rec_id = int(id)\n    except (TypeError, ValueError):\n        raise CardError('invalid_input', 'ID must be a number.') from None\n    history = ctx.store.history(table, rec_id)\n    if not history:\n        raise CardError('not_found', f'No history found for record {rec_id} in {table}.')\n    if version is None:\n        old_data = history[-1].get('before')\n        if old_data is None:\n            raise CardError('not_found', 'There is no earlier version to go back to.')\n    else:\n        matches = [h for h in history if h['version'] == version]\n        if not matches or matches[0].get('after') is None:\n            raise CardError('not_found', f'Version {version} not found for record {rec_id}.')\n        old_data = matches[0]['after']\n    restore_values = {k: v for k, v in old_data.items() if k not in ('id', '_version', '_created_at', '_updated_at', '_archived')}\n    record = ctx.store.update(table, rec_id, restore_values)\n    return {'record': record}",
  "settings": [
   {
    "name": "table",
    "default": "records"
   },
   {
    "name": "version",
    "default": null
   }
  ],
  "inputs": [
   "id"
  ],
  "outputs": [
   "record"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Resume After Result": {
  "function": "resume_after_result",
  "source": "def resume_after_result(ctx, *, result, item, merge_payload: bool=True) -> dict:\n    if not isinstance(result, dict):\n        raise CardError('invalid_input', 'Result must be a record.')\n    if not isinstance(item, dict):\n        raise CardError('invalid_input', 'Item must be a record.')\n    if 'key' not in item:\n        raise CardError('missing_field', \"Item must have a 'key' field.\", {'fields': ['key']})\n    data = {'result': result}\n    if merge_payload and 'payload' in item:\n        data['payload'] = item['payload']\n    return {'resumed': True, 'data': data}",
  "settings": [
   {
    "name": "merge_payload",
    "default": true
   }
  ],
  "inputs": [
   "result",
   "item"
  ],
  "outputs": [
   "resumed",
   "data"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Retry Failed Step": {
  "function": "retry_failed_step",
  "source": "def retry_failed_step(ctx, *, step, max_attempts: int=3) -> dict:\n    if not callable(step):\n        raise CardError('invalid_input', 'Step must be callable.')\n    if max_attempts < 1:\n        raise CardError('invalid_input', 'Max attempts must be at least 1.')\n    last_error = None\n    for attempt in range(1, max_attempts + 1):\n        try:\n            with ctx.store.transaction():\n                result = step()\n            return {'success': True, 'result': result, 'attempts': attempt, 'error': None}\n        except Exception as err:\n            last_error = str(err)\n    return {'success': False, 'result': None, 'attempts': max_attempts, 'error': {'code': 'max_retries', 'message': f'Step failed after {max_attempts} attempts.', 'last_error': last_error}}",
  "settings": [
   {
    "name": "max_attempts",
    "default": 3
   }
  ],
  "inputs": [
   "step"
  ],
  "outputs": [
   "success",
   "result",
   "attempts",
   "error"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Round Numeric Value": {
  "function": "round_numeric_value",
  "source": "def round_numeric_value(ctx, *, value, places: int=2) -> dict:\n    num = to_number(value, 'value')\n    return {'value': round_half_up(num, places)}",
  "settings": [
   {
    "name": "places",
    "default": 2
   }
  ],
  "inputs": [
   "value"
  ],
  "outputs": [
   "value"
  ],
  "runtime": [
   "round_half_up",
   "to_number"
  ],
  "imports": []
 },
 "Route By Category": {
  "function": "route_by_category",
  "source": "def route_by_category(ctx, *, record, field: str='category', categories: dict | None=None) -> dict:\n    if not isinstance(record, dict):\n        raise CardError('invalid_input', 'Route By Category needs a record.')\n    if categories is None:\n        categories = {}\n    if not isinstance(categories, dict):\n        raise CardError('invalid_input', 'Categories must be a mapping of values to port names.')\n    value = get_field(record, field)\n    value_str = str(value).strip().casefold() if value is not None else ''\n    for cat_val, port in categories.items():\n        if str(cat_val).strip().casefold() == value_str:\n            return {'route': port, 'value': record}\n    return {'route': 'no_match', 'value': record}",
  "settings": [
   {
    "name": "field",
    "default": "category"
   },
   {
    "name": "categories",
    "default": null
   }
  ],
  "inputs": [
   "record"
  ],
  "outputs": [
   "hardware",
   "tools",
   "supplies",
   "no_match"
  ],
  "runtime": [
   "CardError",
   "get_field"
  ],
  "imports": []
 },
 "Route By Date Comparison": {
  "function": "route_by_date_comparison",
  "source": "def route_by_date_comparison(ctx, *, record, field: str='date') -> dict:\n    if not isinstance(record, dict):\n        raise CardError('invalid_input', 'Route By Date Comparison needs a record.')\n    value = get_field(record, field)\n    record_date = to_date(value, field)\n    today = ctx.today()\n    if record_date < today:\n        return {'route': 'past', 'value': record}\n    elif record_date > today:\n        return {'route': 'future', 'value': record}\n    else:\n        return {'route': 'today', 'value': record}",
  "settings": [
   {
    "name": "field",
    "default": "date"
   }
  ],
  "inputs": [
   "record"
  ],
  "outputs": [
   "past",
   "today",
   "future"
  ],
  "runtime": [
   "CardError",
   "get_field",
   "to_date"
  ],
  "imports": []
 },
 "Route By Field Presence": {
  "function": "route_by_field_presence",
  "source": "def route_by_field_presence(ctx, *, record, field: str='value') -> dict:\n    if not isinstance(record, dict):\n        raise CardError('invalid_input', 'Route By Field Presence needs a record.')\n    if not field:\n        raise CardError('invalid_input', 'Field name is required.')\n    value = get_field(record, field)\n    if is_blank(value):\n        return {'route': 'is_empty', 'value': record}\n    return {'route': 'has_value', 'value': record}",
  "settings": [
   {
    "name": "field",
    "default": "value"
   }
  ],
  "inputs": [
   "record"
  ],
  "outputs": [
   "has_value",
   "is_empty"
  ],
  "runtime": [
   "CardError",
   "get_field",
   "is_blank"
  ],
  "imports": []
 },
 "Route By List Membership": {
  "function": "route_by_list_membership",
  "source": "def route_by_list_membership(ctx, *, record, field: str='value', reference_list: list | None=None) -> dict:\n    if not isinstance(record, dict):\n        raise CardError('invalid_input', 'Route By List Membership needs a record.')\n    if reference_list is None:\n        reference_list = []\n    if not isinstance(reference_list, list):\n        raise CardError('invalid_input', 'Reference list must be a list.')\n    value = get_field(record, field)\n    value_str = str(value).strip().casefold() if value is not None else ''\n    for item in reference_list:\n        if str(item).strip().casefold() == value_str:\n            return {'route': 'in_list', 'value': record}\n    return {'route': 'not_in_list', 'value': record}",
  "settings": [
   {
    "name": "field",
    "default": "value"
   },
   {
    "name": "reference_list",
    "default": null
   }
  ],
  "inputs": [
   "record"
  ],
  "outputs": [
   "in_list",
   "not_in_list"
  ],
  "runtime": [
   "CardError",
   "get_field"
  ],
  "imports": []
 },
 "Route By Numeric Range": {
  "function": "route_by_numeric_range",
  "source": "def route_by_numeric_range(ctx, *, record, field: str='value', ranges: list | None=None) -> dict:\n    if not isinstance(record, dict):\n        raise CardError('invalid_input', 'Route By Numeric Range needs a record.')\n    if ranges is None:\n        ranges = []\n    if not isinstance(ranges, list):\n        raise CardError('invalid_input', 'Ranges must be a list of range definitions.')\n    value = get_field(record, field)\n    num = try_number(value)\n    if num is not None:\n        for rng in ranges:\n            if not isinstance(rng, dict):\n                continue\n            min_val = rng.get('min')\n            max_val = rng.get('max')\n            port = rng.get('port', 'no_match')\n            if min_val is not None:\n                min_num = try_number(min_val)\n                if min_num is not None and num < min_num:\n                    continue\n            if max_val is not None:\n                max_num = try_number(max_val)\n                if max_num is not None and num > max_num:\n                    continue\n            return {'route': port, 'value': record}\n    return {'route': 'no_match', 'value': record}",
  "settings": [
   {
    "name": "field",
    "default": "value"
   },
   {
    "name": "ranges",
    "default": null
   }
  ],
  "inputs": [
   "record"
  ],
  "outputs": [
   "low",
   "medium",
   "high",
   "no_match"
  ],
  "runtime": [
   "CardError",
   "get_field",
   "try_number"
  ],
  "imports": []
 },
 "Route By Status Value": {
  "function": "route_by_status_value",
  "source": "def route_by_status_value(ctx, *, record, field: str='status', routes: dict | None=None) -> dict:\n    if not isinstance(record, dict):\n        raise CardError('invalid_input', 'Route By Status Value needs a record.')\n    if routes is None:\n        routes = {}\n    if not isinstance(routes, dict):\n        raise CardError('invalid_input', 'Routes must be a mapping of values to port names.')\n    value = get_field(record, field)\n    value_str = str(value).strip() if value is not None else ''\n    for status_val, port in routes.items():\n        if str(status_val).strip().casefold() == value_str.casefold():\n            return {'route': port, 'value': record}\n    return {'route': 'no_match', 'value': record}",
  "settings": [
   {
    "name": "field",
    "default": "status"
   },
   {
    "name": "routes",
    "default": null
   }
  ],
  "inputs": [
   "record"
  ],
  "outputs": [
   "pending",
   "shipped",
   "delivered",
   "no_match"
  ],
  "runtime": [
   "CardError",
   "get_field"
  ],
  "imports": []
 },
 "Route By Text Match": {
  "function": "route_by_text_match",
  "source": "def route_by_text_match(ctx, *, record, field: str='value', match_value: str='', match_port: str='match') -> dict:\n    if not isinstance(record, dict):\n        raise CardError('invalid_input', 'Route By Text Match needs a record.')\n    if not match_port or not isinstance(match_port, str):\n        raise CardError('invalid_input', 'Match port name is required.')\n    value = get_field(record, field)\n    value_str = str(value).strip().casefold() if value is not None else ''\n    match_str = str(match_value).strip().casefold()\n    if value_str == match_str:\n        return {'route': match_port, 'value': record}\n    return {'route': 'no_match', 'value': record}",
  "settings": [
   {
    "name": "field",
    "default": "value"
   },
   {
    "name": "match_value",
    "default": ""
   },
   {
    "name": "match_port",
    "default": "match"
   }
  ],
  "inputs": [
   "record"
  ],
  "outputs": [
   "match",
   "no_match"
  ],
  "runtime": [
   "CardError",
   "get_field"
  ],
  "imports": []
 },
 "Run At App Start": {
  "function": "run_at_app_start",
  "source": "def run_at_app_start(ctx, *, started, description: str='Initialize app') -> dict:\n    ctx.require_preview()\n    fire = bool(started)\n    event = {'kind': 'app_start', 'at': iso(ctx.now()), 'description': description} if fire else {}\n    return {'fire': fire, 'event': event}",
  "settings": [
   {
    "name": "description",
    "default": "Initialize app"
   }
  ],
  "inputs": [
   "started"
  ],
  "outputs": [
   "fire",
   "event"
  ],
  "runtime": [
   "iso"
  ],
  "imports": []
 },
 "Run On A Timer": {
  "function": "run_on_a_timer",
  "source": "def run_on_a_timer(ctx, *, interval_seconds: int=60, repeat: bool=True, label: str='Timer', last_fired: str | None=None) -> dict:\n    ctx.require_preview()\n    if not isinstance(interval_seconds, (int, float)) or isinstance(interval_seconds, bool) or interval_seconds <= 0:\n        raise CardError('invalid_input', 'Timer interval must be positive.')\n    from datetime import timedelta\n    if last_fired is not None:\n        if not repeat:\n            return {'fire': False, 'event': {}, 'next_due': None}\n        due_at = to_datetime(last_fired, 'last_fired') + timedelta(seconds=interval_seconds)\n        if ctx.now() < due_at:\n            return {'fire': False, 'event': {}, 'next_due': iso(due_at)}\n    fire = True\n    event = {'kind': 'timer_tick', 'interval': interval_seconds, 'repeat': repeat, 'label': label, 'at': iso(ctx.now())}\n    next_due = iso(ctx.now() + timedelta(seconds=interval_seconds)) if repeat else None\n    return {'fire': fire, 'event': event, 'next_due': next_due}",
  "settings": [
   {
    "name": "interval_seconds",
    "default": 60
   },
   {
    "name": "repeat",
    "default": true
   },
   {
    "name": "label",
    "default": "Timer"
   },
   {
    "name": "last_fired",
    "default": null
   }
  ],
  "inputs": [],
  "outputs": [
   "fire",
   "event",
   "next_due"
  ],
  "runtime": [
   "CardError",
   "iso",
   "to_datetime"
  ],
  "imports": []
 },
 "Run Steps In Sequence": {
  "function": "run_steps_in_sequence",
  "source": "def run_steps_in_sequence(ctx, *, steps: list[Callable[[], dict]]) -> dict:\n    if not isinstance(steps, list):\n        raise CardError('invalid_input', 'Steps must be a list.')\n    bounded(steps, MAX_LOOP_ITEMS, 'steps')\n    results = []\n    for step in steps:\n        if not callable(step):\n            raise CardError('invalid_input', 'Each step must be callable.')\n        result = step()\n        results.append(result)\n    return {'results': results}",
  "settings": [],
  "inputs": [
   "steps"
  ],
  "outputs": [
   "results"
  ],
  "runtime": [
   "Callable",
   "CardError",
   "MAX_LOOP_ITEMS",
   "bounded"
  ],
  "imports": []
 },
 "Run When Button Pressed": {
  "function": "run_when_button_pressed",
  "source": "def run_when_button_pressed(ctx, *, pressed, button_id: str='button', label: str='Run') -> dict:\n    ctx.require_preview()\n    fire = bool(pressed)\n    event = {'kind': 'button_pressed', 'button_id': button_id, 'label': label} if fire else {}\n    return {'fire': fire, 'event': event}",
  "settings": [
   {
    "name": "button_id",
    "default": "button"
   },
   {
    "name": "label",
    "default": "Run"
   }
  ],
  "inputs": [
   "pressed"
  ],
  "outputs": [
   "fire",
   "event"
  ],
  "runtime": [],
  "imports": []
 },
 "Run When Form Submitted": {
  "function": "run_when_form_submitted",
  "source": "def run_when_form_submitted(ctx, *, submitted, values, form_id: str='form') -> dict:\n    ctx.require_preview()\n    if not isinstance(values, dict):\n        raise CardError('invalid_input', 'Form values must be a record.')\n    fire = bool(submitted)\n    event = {'kind': 'form_submitted', 'form_id': form_id, 'values': values} if fire else {}\n    return {'fire': fire, 'event': event}",
  "settings": [
   {
    "name": "form_id",
    "default": "form"
   }
  ],
  "inputs": [
   "submitted",
   "values"
  ],
  "outputs": [
   "fire",
   "event"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Run When Page Opened": {
  "function": "run_when_page_opened",
  "source": "def run_when_page_opened(ctx, *, opened, page_id: str='page', title: str='Page') -> dict:\n    ctx.require_preview()\n    fire = bool(opened)\n    event = {'kind': 'page_opened', 'page_id': page_id, 'title': title} if fire else {}\n    return {'fire': fire, 'event': event}",
  "settings": [
   {
    "name": "page_id",
    "default": "page"
   },
   {
    "name": "title",
    "default": "Page"
   }
  ],
  "inputs": [
   "opened"
  ],
  "outputs": [
   "fire",
   "event"
  ],
  "runtime": [],
  "imports": []
 },
 "Run When Record Changed": {
  "function": "run_when_record_changed",
  "source": "def run_when_record_changed(ctx, *, table: str, record_id: int, last_version: int | None=None, watch_fields: list[str] | None=None) -> dict:\n    ctx.require_preview()\n    if not ctx.store.schema(table):\n        raise CardError('no_such_table', f'Table {table} does not exist.')\n    record = ctx.store.get(table, record_id)\n    if not record:\n        return {'fire': False, 'event': None, 'record': None, 'before': None, 'after': None}\n    current_version = record['_version']\n    if last_version is not None and current_version <= last_version:\n        return {'fire': False, 'event': None, 'record': None, 'before': None, 'after': None}\n    history = ctx.store.history(table, record_id)\n    before = history[-1]['before'] if history and history[-1].get('before') else {}\n    after = record\n    if watch_fields and (not ctx.store.schema(table).get('history')):\n        raise CardError('history_required', 'Watching fields needs change history to be enabled for the table.')\n    if watch_fields:\n        changed = any((before.get(f) != after.get(f) for f in watch_fields))\n        if not changed:\n            return {'fire': False, 'event': None, 'record': None, 'before': None, 'after': None}\n    return {'fire': True, 'event': {'kind': 'record_changed', 'table': table, 'id': record_id, 'version': current_version}, 'record': record, 'before': before, 'after': after}",
  "settings": [
   {
    "name": "record_id",
    "required": true
   },
   {
    "name": "last_version",
    "default": null
   },
   {
    "name": "watch_fields",
    "default": null
   }
  ],
  "inputs": [
   "table"
  ],
  "outputs": [
   "fire",
   "event",
   "record",
   "before",
   "after"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Run When Record Created": {
  "function": "run_when_record_created",
  "source": "def run_when_record_created(ctx, *, table: str, last_checked_id: int | None=None) -> dict:\n    ctx.require_preview()\n    ctx.store.schema(table)\n    where = None if last_checked_id is None else {'field': 'id', 'op': 'gt', 'value': last_checked_id}\n    found = ctx.store.find(table, where=where, order_by='id', limit=1, include_archived=True)\n    if not found:\n        return {'fire': False, 'event': None, 'record': None, 'last_seen_id': last_checked_id}\n    record = found[0]\n    return {'fire': True, 'event': {'kind': 'record_created', 'table': table, 'id': record['id']}, 'record': record, 'last_seen_id': record['id']}",
  "settings": [
   {
    "name": "last_checked_id",
    "default": null
   }
  ],
  "inputs": [
   "table"
  ],
  "outputs": [
   "fire",
   "event",
   "record",
   "last_seen_id"
  ],
  "runtime": [],
  "imports": []
 },
 "Run When Record Deleted": {
  "function": "run_when_record_deleted",
  "source": "def run_when_record_deleted(ctx, *, table: str, tracked_ids: list[int]) -> dict:\n    ctx.require_preview()\n    if not ctx.store.schema(table):\n        raise CardError('no_such_table', f'Table {table} does not exist.')\n    for rid in bounded(tracked_ids, what='tracked ids'):\n        record = ctx.store.get(table, rid)\n        if not record or record.get('_archived'):\n            history = ctx.store.history(table, rid)\n            last_state = history[-1]['before'] if history and history[-1].get('before') else {'id': rid}\n            return {'fire': True, 'event': {'kind': 'record_deleted', 'table': table, 'id': rid}, 'record': last_state}\n    return {'fire': False, 'event': None, 'record': None}",
  "settings": [
   {
    "name": "tracked_ids",
    "required": true
   }
  ],
  "inputs": [
   "table"
  ],
  "outputs": [
   "fire",
   "event",
   "record"
  ],
  "runtime": [
   "CardError",
   "bounded"
  ],
  "imports": []
 },
 "Run When Record Selected": {
  "function": "run_when_record_selected",
  "source": "def run_when_record_selected(ctx, *, selected, record, table: str='records') -> dict:\n    ctx.require_preview()\n    fire = bool(selected) and record is not None\n    event = {'kind': 'record_selected', 'table': table, 'record': record} if fire else {}\n    return {'fire': fire, 'event': event}",
  "settings": [
   {
    "name": "table",
    "default": "records"
   }
  ],
  "inputs": [
   "selected",
   "record"
  ],
  "outputs": [
   "fire",
   "event"
  ],
  "runtime": [],
  "imports": []
 },
 "Run When Value Crosses Threshold": {
  "function": "run_when_value_crosses_threshold",
  "source": "def run_when_value_crosses_threshold(ctx, *, table: str, record_id: int, field: str, threshold: float, direction: str='below', last_value: float | None=None) -> dict:\n    ctx.require_preview()\n    if not ctx.store.schema(table):\n        raise CardError('no_such_table', f'Table {table} does not exist.')\n    if direction not in ('above', 'below'):\n        raise CardError('invalid_input', \"Direction must be 'above' or 'below'.\")\n    record = ctx.store.get(table, record_id)\n    if not record:\n        return {'fire': False, 'event': None, 'value': None, 'crossed': None}\n    from ..runtime import get_field, try_number\n    current = try_number(get_field(record, field))\n    if current is None:\n        return {'fire': False, 'event': None, 'value': None, 'crossed': None}\n    crossed = False\n    if direction == 'below':\n        if current < threshold:\n            if last_value is None or last_value >= threshold:\n                crossed = True\n    elif current > threshold:\n        if last_value is None or last_value <= threshold:\n            crossed = True\n    if crossed:\n        return {'fire': True, 'event': {'kind': 'threshold_crossed', 'table': table, 'id': record_id, 'field': field, 'threshold': threshold, 'direction': direction}, 'value': current, 'crossed': direction}\n    return {'fire': False, 'event': None, 'value': current, 'crossed': None}",
  "settings": [
   {
    "name": "field",
    "required": true
   },
   {
    "name": "threshold",
    "required": true
   },
   {
    "name": "direction",
    "default": "below"
   },
   {
    "name": "last_value",
    "default": null
   }
  ],
  "inputs": [
   "table",
   "record_id"
  ],
  "outputs": [
   "fire",
   "event",
   "value",
   "crossed"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Search Saved Records By Text": {
  "function": "search_saved_records_by_text",
  "source": "def search_saved_records_by_text(ctx, *, query, table: str='records', fields: list[str] | None=None, limit: int=1000, include_archived: bool=False) -> dict:\n    if not isinstance(query, str):\n        raise CardError('invalid_input', 'Query must be text.')\n    search_text = query.strip()\n    if not search_text:\n        records = ctx.store.find(table, limit=limit, include_archived=include_archived)\n        return {'records': records, 'count': len(records)}\n    schema = ctx.store.schema(table)['fields']\n    search_fields = fields if fields else [f['name'] for f in schema if f.get('type') in ('text', 'email', 'phone', 'choice')]\n    if not search_fields:\n        raise CardError('invalid_input', f'No text fields to search in table {table}.')\n    condition = {'any': [{'field': f, 'op': 'contains', 'value': search_text} for f in search_fields]}\n    records = ctx.store.find(table, where=condition, limit=limit, include_archived=include_archived)\n    return {'records': records, 'count': len(records)}",
  "settings": [
   {
    "name": "table",
    "default": "records"
   },
   {
    "name": "fields",
    "default": null
   },
   {
    "name": "limit",
    "default": 1000
   },
   {
    "name": "include_archived",
    "default": false
   }
  ],
  "inputs": [
   "query"
  ],
  "outputs": [
   "records",
   "count"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Search Text For Pattern": {
  "function": "search_text_for_pattern",
  "source": "def search_text_for_pattern(ctx, *, text, pattern: str, case_sensitive: bool=False) -> dict:\n    s = as_text(text, 'text')\n    _check_safe_pattern(pattern, len(s))\n    flags = 0 if case_sensitive else re.IGNORECASE\n    try:\n        match = re.search(pattern, s, flags)\n    except re.error:\n        raise CardError('bad_expression', 'Pattern is not valid.') from None\n    if match:\n        return {'found': True, 'match': match.group()}\n    return {'found': False, 'match': None}",
  "settings": [
   {
    "name": "pattern",
    "required": true
   },
   {
    "name": "case_sensitive",
    "default": false
   }
  ],
  "inputs": [
   "text"
  ],
  "outputs": [
   "found",
   "match"
  ],
  "runtime": [
   "CardError",
   "MAX_TEXT_LENGTH",
   "as_text",
   "re"
  ],
  "imports": [],
  "helpers": [
   {
    "name": "_QUANTIFIER",
    "source": "_QUANTIFIER = re.compile('\\\\{\\\\d*(,\\\\d*)?\\\\}')"
   },
   {
    "name": "_check_safe_pattern",
    "source": "def _check_safe_pattern(pattern, text_length: int) -> None:\n    if not isinstance(pattern, str) or not pattern or len(pattern) > 200:\n        raise CardError('invalid_input', 'Pattern must be 1 to 200 characters.')\n    groups = []\n    last_group = None\n    open_ended = 0\n    i, n = (0, len(pattern))\n    while i < n:\n        ch = pattern[i]\n        group_closed, last_group = (last_group, None)\n        if ch == '\\\\':\n            i += 2\n            continue\n        if ch == '[':\n            i += 2 if pattern[i + 1:i + 2] == '^' else 1\n            i += 1\n            while i < n and pattern[i] != ']':\n                i += 2 if pattern[i] == '\\\\' else 1\n            i += 1\n            continue\n        if ch == '(':\n            groups.append([False, False])\n            if pattern[i + 1:i + 2] == '?':\n                i += 2\n                while i < n and pattern[i] not in ':)=!>':\n                    i += 1\n                i += 0 if pattern[i:i + 1] == ')' else 1\n                continue\n        elif ch == ')':\n            if groups:\n                last_group = groups.pop()\n                if groups:\n                    groups[-1][0] = groups[-1][0] or last_group[0]\n                    groups[-1][1] = groups[-1][1] or last_group[1]\n        elif ch == '|':\n            if groups:\n                groups[-1][1] = True\n        else:\n            size = 1\n            repeat = ch in '*+?'\n            unbounded = ch in '*+'\n            if ch == '{':\n                m = _QUANTIFIER.match(pattern, i)\n                if m:\n                    size, repeat, unbounded = (m.end() - i, True, m.group(1) == ',' or m.group().endswith(',}'))\n            if repeat:\n                if ch != '?' and group_closed and (group_closed[0] or group_closed[1]):\n                    raise CardError('bad_expression', 'Pattern repeats a group that already repeats or has choices; that can hang.')\n                open_ended += unbounded\n                if groups:\n                    groups[-1][0] = True\n                i += size\n                if pattern[i:i + 1] in ('?', '+'):\n                    i += 1\n                continue\n        i += 1\n    if open_ended > 2:\n        raise CardError('bad_expression', 'Pattern has more than 2 open-ended repeats (* + {n,}); that can hang.')\n    limit = (MAX_TEXT_LENGTH, 10000, 1000)[open_ended]\n    if text_length > limit:\n        raise CardError('limit_exceeded', f'Text is too long for this pattern (limit {limit} characters).')"
   }
  ]
 },
 "Select Multiple Options": {
  "function": "select_multiple_options",
  "source": "def select_multiple_options(ctx, *, value=None, name: str='multiselect', label: str='Select Multiple', choices: list=None, required: bool=False, min_selections: int=None, max_selections: int=None, help_text: str='') -> dict:\n    if not choices:\n        choices = []\n    spec = {'type': 'multichoice', 'required': required, 'choices': choices, 'min_length': min_selections, 'max_length': max_selections}\n    clean = coerce_value(spec, value, label)\n    node = view('input.multiselect', id=name, label=label, value=clean or [], choices=choices, required=required, minSelections=min_selections, maxSelections=max_selections, help=help_text)\n    return {'view': node, 'value': clean}",
  "settings": [
   {
    "name": "name",
    "default": "multiselect"
   },
   {
    "name": "label",
    "default": "Select Multiple"
   },
   {
    "name": "choices",
    "default": null
   },
   {
    "name": "required",
    "default": false
   },
   {
    "name": "min_selections",
    "default": null
   },
   {
    "name": "max_selections",
    "default": null
   },
   {
    "name": "help_text",
    "default": ""
   }
  ],
  "inputs": [
   "value"
  ],
  "outputs": [
   "view",
   "value"
  ],
  "runtime": [
   "coerce_value",
   "view"
  ],
  "imports": []
 },
 "Set App Title": {
  "function": "set_app_title",
  "source": "def set_app_title(ctx, *, title: str='', subtitle: str='') -> dict:\n    if not isinstance(title, str):\n        raise CardError('invalid_input', 'App title must be text.')\n    if not title.strip():\n        raise CardError('required', 'App title is required.')\n    if not isinstance(subtitle, str):\n        raise CardError('invalid_input', 'Subtitle must be text.')\n    node = view('layout.app_title', title=title.strip(), subtitle=subtitle.strip())\n    return {'view': node}",
  "settings": [
   {
    "name": "title",
    "default": ""
   },
   {
    "name": "subtitle",
    "default": ""
   }
  ],
  "inputs": [],
  "outputs": [
   "view"
  ],
  "runtime": [
   "CardError",
   "view"
  ],
  "imports": []
 },
 "Set Default Value On Error": {
  "function": "set_default_value_on_error",
  "source": "def set_default_value_on_error(ctx, *, value, default=None) -> dict:\n    if default is None:\n        raise CardError('invalid_input', 'A default value is required.')\n    if is_blank(value):\n        return {'value': default}\n    return {'value': value}",
  "settings": [
   {
    "name": "default",
    "default": null
   }
  ],
  "inputs": [
   "value"
  ],
  "outputs": [
   "value"
  ],
  "runtime": [
   "CardError",
   "is_blank"
  ],
  "imports": []
 },
 "Set Field Default Value": {
  "function": "set_field_default_value",
  "source": "def set_field_default_value(ctx, *, table: str, field: str, default_value) -> dict:\n    schema = ctx.store.schema(table)['fields']\n    spec = next((f for f in schema if f['name'] == field), None)\n    if spec is None:\n        raise CardError('unknown_field', f\"Field '{field}' not found in table '{table}'.\", {'field': field})\n    ctx.store.update_field(table, field, {'default': default_value})\n    return {'field_name': field}",
  "settings": [
   {
    "name": "table",
    "required": true
   },
   {
    "name": "field",
    "required": true
   }
  ],
  "inputs": [
   "default_value"
  ],
  "outputs": [
   "field_name"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Set Field Of Record": {
  "function": "set_field_of_record",
  "source": "def set_field_of_record(ctx, *, value, field: str, record=None) -> dict:\n    if not isinstance(field, str) or not field.strip():\n        raise CardError('invalid_input', 'Say which field to set.')\n    if record is not None and (not isinstance(record, dict)):\n        raise CardError('invalid_input', 'Record must be a record.')\n    out = dict(record or {})\n    out[field.strip()] = value\n    return {'record': out}",
  "settings": [
   {
    "name": "field",
    "required": true
   }
  ],
  "inputs": [
   "value",
   "record"
  ],
  "outputs": [
   "record"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Set Primary Key Field": {
  "function": "set_primary_key_field",
  "source": "def set_primary_key_field(ctx, *, table: str, field: str='id') -> dict:\n    schema = ctx.store.schema(table)['fields']\n    if field != 'id':\n        spec = next((f for f in schema if f['name'] == field), None)\n        if spec is None:\n            raise CardError('unknown_field', f\"Field '{field}' not found in table '{table}'.\", {'field': field})\n        if not spec.get('unique'):\n            raise CardError('invalid_input', f\"Field '{field}' must be unique to be a primary key.\", {'field': field})\n    return {'field_name': field}",
  "settings": [
   {
    "name": "table",
    "required": true
   },
   {
    "name": "field",
    "default": "id"
   }
  ],
  "inputs": [],
  "outputs": [
   "field_name"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Shift Date By Time": {
  "function": "shift_date_by_time",
  "source": "def shift_date_by_time(ctx, *, date, amount, unit: str='days', direction: str='forward') -> dict:\n    if direction not in ('forward', 'backward'):\n        raise CardError('invalid_input', f'Unknown direction: {direction}. Use forward or backward.')\n    d = to_datetime(date, 'date')\n    amt = to_number(amount, 'amount')\n    if unit not in ('days', 'hours', 'minutes', 'seconds'):\n        raise CardError('invalid_input', f'Unknown unit: {unit}. Use days, hours, minutes or seconds.')\n    delta = dt.timedelta(**{unit: amt})\n    result = d + delta if direction == 'forward' else d - delta\n    return {'result': _same_shape(date, result)}",
  "settings": [
   {
    "name": "amount",
    "required": true
   },
   {
    "name": "unit",
    "default": "days"
   },
   {
    "name": "direction",
    "default": "forward"
   }
  ],
  "inputs": [
   "date"
  ],
  "outputs": [
   "result"
  ],
  "runtime": [
   "CardError",
   "dt",
   "iso",
   "to_datetime",
   "to_number"
  ],
  "imports": [],
  "helpers": [
   {
    "name": "_same_shape",
    "source": "def _same_shape(original, result: dt.datetime) -> str:\n    date_only = isinstance(original, dt.date) and (not isinstance(original, dt.datetime)) or (isinstance(original, str) and len(original.strip()) <= 10)\n    if date_only and result.time() == dt.time(0, 0):\n        return result.date().isoformat()\n    return iso(result)"
   }
  ]
 },
 "Show Action Checklist": {
  "function": "show_action_checklist",
  "source": "def show_action_checklist(ctx, *, items, title: str='Actions to complete', icon: str='checkbox') -> dict:\n    if not isinstance(items, (list, tuple)):\n        raise CardError('invalid_input', 'Items must be a list.')\n    if not items:\n        raise CardError('required', 'At least one item is required.')\n    item_nodes = []\n    for i, item in enumerate(items, start=1):\n        text = str(item).strip()\n        if not text:\n            raise CardError('invalid_input', f'Item {i} is empty.')\n        item_nodes.append(view('display.text', props={'text': text}))\n    node = view('display.checklist', props={'title': title, 'icon': icon, 'item_count': len(item_nodes)}, children=item_nodes)\n    return {'view': node}",
  "settings": [
   {
    "name": "title",
    "default": "Actions to complete"
   },
   {
    "name": "icon",
    "default": "checkbox"
   }
  ],
  "inputs": [
   "items"
  ],
  "outputs": [
   "view"
  ],
  "runtime": [
   "CardError",
   "view"
  ],
  "imports": []
 },
 "Show Copyable Text": {
  "function": "show_copyable_text",
  "source": "def show_copyable_text(ctx, *, text, label: str='Copy this text', monospace: bool=False) -> dict:\n    if text is None or (isinstance(text, str) and (not text.strip())):\n        raise CardError('required', 'Text is required.')\n    content = str(text)\n    node = view('display.copyable', props={'label': label, 'text': content, 'monospace': monospace, 'char_count': len(content)})\n    return {'view': node}",
  "settings": [
   {
    "name": "label",
    "default": "Copy this text"
   },
   {
    "name": "monospace",
    "default": false
   }
  ],
  "inputs": [
   "text"
  ],
  "outputs": [
   "view"
  ],
  "runtime": [
   "CardError",
   "view"
  ],
  "imports": []
 },
 "Show Detail View": {
  "function": "show_detail_view",
  "source": "def show_detail_view(ctx, *, record=None, sections=None) -> dict:\n    if not isinstance(record, dict):\n        raise CardError('invalid_input', 'Record must be a dict.')\n    secs = sections if isinstance(sections, list) else []\n    for i, sec in enumerate(secs):\n        if not isinstance(sec, dict):\n            raise CardError('invalid_input', f'Section {i + 1} must be a record.')\n        if 'title' not in sec or not isinstance(sec['title'], str):\n            raise CardError('invalid_input', f'Section {i + 1} needs a title.')\n        if 'fields' not in sec or not isinstance(sec['fields'], list):\n            raise CardError('invalid_input', f'Section {i + 1} needs a fields list.')\n    node = view('display.detail', record=record, sections=secs)\n    return {'view': node}",
  "settings": [
   {
    "name": "sections",
    "default": null
   }
  ],
  "inputs": [
   "record"
  ],
  "outputs": [
   "view"
  ],
  "runtime": [
   "CardError",
   "view"
  ],
  "imports": []
 },
 "Show Manual Steps": {
  "function": "show_manual_steps",
  "source": "def show_manual_steps(ctx, *, steps, title: str='Follow these steps', icon: str='info') -> dict:\n    if not isinstance(steps, (list, tuple)):\n        raise CardError('invalid_input', 'Steps must be a list.')\n    if not steps:\n        raise CardError('required', 'At least one step is required.')\n    step_nodes = []\n    for i, step in enumerate(steps, start=1):\n        text = str(step).strip()\n        if not text:\n            raise CardError('invalid_input', f'Step {i} is empty.')\n        step_nodes.append(view('display.text', props={'text': f'{i}. {text}'}))\n    node = view('display.instructions', props={'title': title, 'icon': icon, 'step_count': len(step_nodes)}, children=step_nodes)\n    return {'view': node}",
  "settings": [
   {
    "name": "title",
    "default": "Follow these steps"
   },
   {
    "name": "icon",
    "default": "info"
   }
  ],
  "inputs": [
   "steps"
  ],
  "outputs": [
   "view"
  ],
  "runtime": [
   "CardError",
   "view"
  ],
  "imports": []
 },
 "Show Message Banner": {
  "function": "show_message_banner",
  "source": "def show_message_banner(ctx, *, message, variant: str='info', dismissible: bool=True, icon: str='') -> dict:\n    if not isinstance(message, str):\n        message = str(message)\n    if not message.strip():\n        raise CardError('required', 'Banner needs a message.')\n    if variant not in ('success', 'info', 'warning', 'error'):\n        variant = 'info'\n    node = view('display.banner', message=message, variant=variant, dismissible=dismissible, icon=icon)\n    return {'view': node}",
  "settings": [
   {
    "name": "variant",
    "default": "info"
   },
   {
    "name": "dismissible",
    "default": true
   },
   {
    "name": "icon",
    "default": ""
   }
  ],
  "inputs": [
   "message"
  ],
  "outputs": [
   "view"
  ],
  "runtime": [
   "CardError",
   "view"
  ],
  "imports": []
 },
 "Show Or Hide Field": {
  "function": "show_or_hide_field",
  "source": "def show_or_hide_field(ctx, *, record, depends_on_field: str, depends_on_value: str=None, show_when: str='equals') -> dict:\n    if not isinstance(record, dict):\n        raise CardError('invalid_input', 'Show Or Hide Field needs a record.')\n    value = get_field(record, depends_on_field)\n    if show_when == 'equals':\n        visible = str(value).strip().lower() == str(depends_on_value).strip().lower() if depends_on_value else False\n    elif show_when == 'not_empty':\n        visible = not is_blank(value)\n    elif show_when == 'empty':\n        visible = is_blank(value)\n    else:\n        raise CardError('invalid_input', f\"Unknown show_when value: {show_when}. Use 'equals', 'not_empty', or 'empty'.\")\n    return {'record': record, 'visible': visible}",
  "settings": [
   {
    "name": "depends_on_field",
    "required": true
   },
   {
    "name": "depends_on_value",
    "default": null
   },
   {
    "name": "show_when",
    "default": "equals"
   }
  ],
  "inputs": [
   "record"
  ],
  "outputs": [
   "record",
   "visible"
  ],
  "runtime": [
   "CardError",
   "get_field",
   "is_blank"
  ],
  "imports": []
 },
 "Show Pending Reminder": {
  "function": "show_pending_reminder",
  "source": "def show_pending_reminder(ctx, *, items, message: str='Actions pending', urgency: str='normal') -> dict:\n    if not isinstance(items, (list, tuple)):\n        raise CardError('invalid_input', 'Items must be a list.')\n    if not items:\n        raise CardError('required', 'At least one pending item is required.')\n    for i, item in enumerate(items):\n        if not isinstance(item, dict) or 'key' not in item:\n            raise CardError('invalid_input', f\"Item {i + 1} must be a record with a 'key' field.\")\n    node = view('display.reminder', props={'message': message, 'urgency': urgency, 'pending_count': len(items)})\n    return {'view': node}",
  "settings": [
   {
    "name": "message",
    "default": "Actions pending"
   },
   {
    "name": "urgency",
    "default": "normal"
   }
  ],
  "inputs": [
   "items"
  ],
  "outputs": [
   "view"
  ],
  "runtime": [
   "CardError",
   "view"
  ],
  "imports": []
 },
 "Show Progress While Running": {
  "function": "show_progress_while_running",
  "source": "def show_progress_while_running(ctx, *, current=None, total=None, label: str='Loading...', show_percentage: bool=True) -> dict:\n    if current is not None and total is not None:\n        current = int(current)\n        total = int(total)\n        if current > total:\n            raise CardError('invalid_input', 'Progress current cannot exceed total.')\n    node = view('display.progress', label=label, current=current, total=total, show_percentage=show_percentage)\n    return {'view': node}",
  "settings": [
   {
    "name": "label",
    "default": "Loading..."
   },
   {
    "name": "show_percentage",
    "default": true
   }
  ],
  "inputs": [
   "current",
   "total"
  ],
  "outputs": [
   "view"
  ],
  "runtime": [
   "CardError",
   "view"
  ],
  "imports": []
 },
 "Show Records Table": {
  "function": "show_records_table",
  "source": "def show_records_table(ctx, *, records=None, columns=None, sortable: bool=False, page_size: int=100) -> dict:\n    if not isinstance(records, list):\n        raise CardError('invalid_input', 'Records must be a list.')\n    cols = columns if isinstance(columns, list) else []\n    for i, col in enumerate(cols):\n        if not isinstance(col, dict):\n            raise CardError('invalid_input', f'Column {i + 1} must be a record.')\n        if 'field' not in col or not isinstance(col['field'], str):\n            raise CardError('invalid_input', f'Column {i + 1} needs a field name.')\n        if 'label' not in col:\n            col['label'] = col['field']\n    if page_size < 1:\n        raise CardError('invalid_input', 'Page size must be at least 1.')\n    items = bounded(records, what='records')\n    node = view('display.table', records=items, columns=cols, sortable=sortable, page_size=page_size)\n    return {'view': node}",
  "settings": [
   {
    "name": "columns",
    "default": null
   },
   {
    "name": "sortable",
    "default": false
   },
   {
    "name": "page_size",
    "default": 100
   }
  ],
  "inputs": [
   "records"
  ],
  "outputs": [
   "view"
  ],
  "runtime": [
   "CardError",
   "bounded",
   "view"
  ],
  "imports": []
 },
 "Show Status Badge": {
  "function": "show_status_badge",
  "source": "def show_status_badge(ctx, *, value='', color: str='gray') -> dict:\n    if not value or (isinstance(value, str) and (not value.strip())):\n        raise CardError('required', 'Badge value is required.')\n    allowed = ('gray', 'blue', 'green', 'yellow', 'red', 'orange')\n    if color not in allowed:\n        raise CardError('invalid_input', f\"Color must be one of: {', '.join(allowed)}.\")\n    text = str(value).strip() if isinstance(value, str) else str(value)\n    node = view('display.badge', value=text, color=color)\n    return {'view': node}",
  "settings": [
   {
    "name": "color",
    "default": "gray"
   }
  ],
  "inputs": [
   "value"
  ],
  "outputs": [
   "view"
  ],
  "runtime": [
   "CardError",
   "view"
  ],
  "imports": []
 },
 "Show Still Pending": {
  "function": "show_still_pending",
  "source": "def show_still_pending(ctx, *, items, status_field: str='status', pending_value: str='pending', require_status: bool=False) -> dict:\n    if not isinstance(items, (list, tuple)):\n        raise CardError('invalid_input', 'Items must be a list.')\n    pending = []\n    for i, item in enumerate(items):\n        if not isinstance(item, dict):\n            raise CardError('invalid_input', f'Item {i + 1} must be a record.')\n        if require_status and status_field not in item:\n            raise CardError('missing_field', f\"Item {i + 1} must have '{status_field}' field.\", {'fields': [status_field]})\n        status = str(item.get(status_field, '')).strip().lower()\n        if status == pending_value.lower():\n            pending.append(item)\n    return {'pending_items': pending, 'count': len(pending)}",
  "settings": [
   {
    "name": "status_field",
    "default": "status"
   },
   {
    "name": "pending_value",
    "default": "pending"
   },
   {
    "name": "require_status",
    "default": false
   }
  ],
  "inputs": [
   "items"
  ],
  "outputs": [
   "pending_items",
   "count"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Show Waiting Item": {
  "function": "show_waiting_item",
  "source": "def show_waiting_item(ctx, *, item, show_instructions: bool=True) -> dict:\n    if not isinstance(item, dict):\n        raise CardError('invalid_input', 'Item must be a record.')\n    if 'key' not in item or 'kind' not in item:\n        raise CardError('missing_field', \"Item must have 'key' and 'kind' fields.\", {'fields': ['key', 'kind']})\n    props = {'key': str(item['key']), 'kind': str(item['kind']), 'created_at': item.get('created_at'), 'show_instructions': show_instructions}\n    if show_instructions and 'instructions' in item:\n        props['instructions'] = str(item['instructions'])\n    node = view('display.waiting_item', props=props)\n    return {'view': node}",
  "settings": [
   {
    "name": "show_instructions",
    "default": true
   }
  ],
  "inputs": [
   "item"
  ],
  "outputs": [
   "view"
  ],
  "runtime": [
   "CardError",
   "view"
  ],
  "imports": []
 },
 "Skip Invalid Record": {
  "function": "skip_invalid_record",
  "source": "def skip_invalid_record(ctx, *, record, condition: dict | None=None) -> dict:\n    if not isinstance(record, dict):\n        raise CardError('invalid_input', 'Skip Invalid Record needs a record.')\n    if condition is None:\n        return {'record': record, 'skipped': False}\n    if not isinstance(condition, dict):\n        raise CardError('invalid_input', 'Condition must be a condition object.')\n    from ..runtime import matches\n    if matches(record, condition):\n        return {'record': record, 'skipped': False}\n    return {'record': None, 'skipped': True}",
  "settings": [
   {
    "name": "condition",
    "default": null
   }
  ],
  "inputs": [
   "record"
  ],
  "outputs": [
   "record",
   "skipped"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Sort Records By Field": {
  "function": "sort_records_by_field",
  "source": "def sort_records_by_field(ctx, *, records, fields: list[str], descending: bool=False) -> dict:\n    if not isinstance(records, list):\n        raise CardError('invalid_input', 'Records must be a list.')\n    if not fields:\n        raise CardError('missing_field', 'At least one field is required for sorting.')\n    records_list = bounded(records, what='records')\n\n    def sort_key(rec: dict) -> tuple:\n        values = []\n        for field in fields:\n            val = get_field(rec, field)\n            blank = val is None or (isinstance(val, str) and (not val.strip()))\n            flag = (0 if blank else 1) if descending else 1 if blank else 0\n            if blank:\n                values.append((flag, 0, 0))\n                continue\n            num = try_number(val) if not isinstance(val, bool) else None\n            if num is not None:\n                values.append((flag, 0, num))\n            else:\n                values.append((flag, 1, str(val).strip().casefold()))\n        return tuple(values)\n    sorted_records = sorted(records_list, key=sort_key, reverse=descending)\n    return {'records': sorted_records}",
  "settings": [
   {
    "name": "fields",
    "required": true
   },
   {
    "name": "descending",
    "default": false
   }
  ],
  "inputs": [
   "records"
  ],
  "outputs": [
   "records"
  ],
  "runtime": [
   "CardError",
   "bounded",
   "get_field",
   "try_number"
  ],
  "imports": []
 },
 "Split Into Columns": {
  "function": "split_into_columns",
  "source": "def split_into_columns(ctx, *, children=None, widths=None, gap: int=16) -> dict:\n    kids = children if isinstance(children, list) else []\n    if not kids:\n        raise CardError('invalid_input', 'Columns need at least one child.')\n    ws = widths if isinstance(widths, list) else [1] * len(kids)\n    if len(ws) != len(kids):\n        raise CardError('invalid_input', f'Number of widths ({len(ws)}) must match number of children ({len(kids)}).')\n    if any((w <= 0 for w in ws)):\n        raise CardError('invalid_input', 'Column widths must be positive.')\n    if gap < 0:\n        raise CardError('invalid_input', 'Gap cannot be negative.')\n    node = view('layout.columns', children=kids, widths=ws, gap=gap)\n    return {'view': node}",
  "settings": [
   {
    "name": "widths",
    "default": null
   },
   {
    "name": "gap",
    "default": 16
   }
  ],
  "inputs": [
   "children"
  ],
  "outputs": [
   "view"
  ],
  "runtime": [
   "CardError",
   "view"
  ],
  "imports": []
 },
 "Split Text By Separator": {
  "function": "split_text_by_separator",
  "source": "def split_text_by_separator(ctx, *, text, separator: str=',', trim: bool=True) -> dict:\n    s = as_text(text, 'text')\n    if not isinstance(separator, str) or separator == '':\n        raise CardError('invalid_input', 'Separator must be at least one character.')\n    parts = s.split(separator)\n    if trim:\n        parts = [p.strip() for p in parts]\n    return {'values': parts}",
  "settings": [
   {
    "name": "separator",
    "default": ","
   },
   {
    "name": "trim",
    "default": true
   }
  ],
  "inputs": [
   "text"
  ],
  "outputs": [
   "values"
  ],
  "runtime": [
   "CardError",
   "as_text"
  ],
  "imports": []
 },
 "Split Text Into Lines": {
  "function": "split_text_into_lines",
  "source": "def split_text_into_lines(ctx, *, text, skip_blank: bool=True) -> dict:\n    s = as_text(text, 'text')\n    lines = s.splitlines()\n    if skip_blank:\n        lines = [ln for ln in lines if ln.strip()]\n    return {'lines': lines}",
  "settings": [
   {
    "name": "skip_blank",
    "default": true
   }
  ],
  "inputs": [
   "text"
  ],
  "outputs": [
   "lines"
  ],
  "runtime": [
   "as_text"
  ],
  "imports": []
 },
 "Stack In Panel": {
  "function": "stack_in_panel",
  "source": "def stack_in_panel(ctx, *, children=None, title: str='', border: bool=False) -> dict:\n    if not isinstance(children, list):\n        raise CardError('invalid_input', 'Children must be a list of view nodes.')\n    if not isinstance(title, str):\n        raise CardError('invalid_input', 'Title must be text.')\n    node = view('layout.panel', children=children, title=title, border=border)\n    return {'view': node}",
  "settings": [
   {
    "name": "title",
    "default": ""
   },
   {
    "name": "border",
    "default": false
   }
  ],
  "inputs": [
   "children"
  ],
  "outputs": [
   "view"
  ],
  "runtime": [
   "CardError",
   "view"
  ],
  "imports": []
 },
 "Stop On Error Threshold": {
  "function": "stop_on_error_threshold",
  "source": "def stop_on_error_threshold(ctx, *, errors, threshold: int=10, total_processed: int=0, threshold_percent: float=None) -> dict:\n    if not isinstance(errors, list):\n        raise CardError('invalid_input', 'Errors must be a list.')\n    error_count = len(errors)\n    if error_count > threshold:\n        raise CardError('error_threshold_exceeded', f'Too many errors: {error_count} exceeds limit of {threshold}.')\n    if threshold_percent is not None and total_processed > 0:\n        error_rate = error_count / total_processed * 100\n        if error_rate > threshold_percent:\n            raise CardError('error_threshold_exceeded', f'Error rate {error_rate:.1f}% exceeds limit of {threshold_percent}%.')\n    return {'proceed': True, 'stopped': False}",
  "settings": [
   {
    "name": "threshold",
    "default": 10
   },
   {
    "name": "total_processed",
    "default": 0
   },
   {
    "name": "threshold_percent",
    "default": null
   }
  ],
  "inputs": [
   "errors"
  ],
  "outputs": [
   "proceed",
   "stopped"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Suggest Record Layout": {
  "function": "suggest_record_layout",
  "source": "def suggest_record_layout(ctx, *, proposal) -> dict:\n    if not isinstance(proposal, dict) or 'fields' not in proposal:\n        raise CardError('invalid_input', \"Proposal must have a 'fields' list.\")\n    if not isinstance(proposal['fields'], list) or not proposal['fields']:\n        raise CardError('invalid_input', 'Proposal must have at least one field.')\n    valid_types = {'text', 'number', 'integer', 'bool', 'date', 'datetime', 'time', 'choice', 'multichoice', 'email', 'phone', 'currency'}\n    schema = []\n    for field in proposal['fields']:\n        if not isinstance(field, dict) or 'name' not in field or 'type' not in field:\n            raise CardError('invalid_input', \"Each field needs 'name' and 'type'.\")\n        if field['type'] not in valid_types:\n            raise CardError('bad_type', f\"Unknown type: {field['type']}.\")\n        clean = {'name': field['name'], 'type': field['type']}\n        if field.get('required'):\n            clean['required'] = True\n        if field['type'] in ('choice', 'multichoice') and 'choices' in field:\n            if not isinstance(field['choices'], list) or not field['choices']:\n                raise CardError('invalid_input', f\"Field {field['name']} needs a non-empty choices list.\")\n            clean['choices'] = field['choices']\n        if 'min' in field:\n            clean['min'] = field['min']\n        if 'max' in field:\n            clean['max'] = field['max']\n        if 'min_length' in field:\n            clean['min_length'] = field['min_length']\n        if 'max_length' in field:\n            clean['max_length'] = field['max_length']\n        if 'default' in field:\n            clean['default'] = field['default']\n        schema.append(clean)\n    return {'schema': schema}",
  "settings": [],
  "inputs": [
   "proposal"
  ],
  "outputs": [
   "schema"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Summary Table": {
  "function": "summary_table",
  "source": "def summary_table(ctx, *, data, title: str='Summary', show_borders: bool=True) -> dict:\n    if not isinstance(data, list):\n        raise CardError('invalid_input', 'Summary data must be a list of records.')\n    if not data:\n        raise CardError('invalid_input', 'Summary needs at least one row.')\n    rows = bounded(data, limit=1000, what='summary rows')\n    node = view('display.summary', title=title, rows=rows, show_borders=show_borders)\n    return {'view': node}",
  "settings": [
   {
    "name": "title",
    "default": "Summary"
   },
   {
    "name": "show_borders",
    "default": true
   }
  ],
  "inputs": [
   "data"
  ],
  "outputs": [
   "view"
  ],
  "runtime": [
   "CardError",
   "bounded",
   "view"
  ],
  "imports": []
 },
 "Switch Toggle": {
  "function": "switch_toggle",
  "source": "def switch_toggle(ctx, *, value=None, label: str='Toggle', name: str='toggle', disabled: bool=False) -> dict:\n    spec = {'type': 'bool'}\n    clean = coerce_value(spec, value, label)\n    node = view('input.toggle', id=name, label=label, value=clean, disabled=disabled)\n    return {'view': node, 'value': clean}",
  "settings": [
   {
    "name": "label",
    "default": "Toggle"
   },
   {
    "name": "name",
    "default": "toggle"
   },
   {
    "name": "disabled",
    "default": false
   }
  ],
  "inputs": [
   "value"
  ],
  "outputs": [
   "view",
   "value"
  ],
  "runtime": [
   "coerce_value",
   "view"
  ],
  "imports": []
 },
 "Take Record Range": {
  "function": "take_record_range",
  "source": "def take_record_range(ctx, *, records, start: int=0, end: int=10) -> dict:\n    if not isinstance(records, list):\n        raise CardError('invalid_input', 'Records must be a list.')\n    start = as_int(start, 'start')\n    end = as_int(end, 'end')\n    if start < 0:\n        raise CardError('invalid_input', 'Start position must be at least 0.')\n    if end < start:\n        raise CardError('invalid_input', 'End position must be at least the start position.')\n    records_list = bounded(records, what='records')\n    return {'records': records_list[start:end]}",
  "settings": [
   {
    "name": "start",
    "default": 0
   },
   {
    "name": "end",
    "default": 10
   }
  ],
  "inputs": [
   "records"
  ],
  "outputs": [
   "records"
  ],
  "runtime": [
   "CardError",
   "as_int",
   "bounded"
  ],
  "imports": []
 },
 "Toggle Checkbox": {
  "function": "toggle_checkbox",
  "source": "def toggle_checkbox(ctx, *, value=None, name: str='checkbox', label: str='Option', help_text: str='') -> dict:\n    spec = {'type': 'bool'}\n    clean = coerce_value(spec, value, label)\n    if clean is None:\n        clean = False\n    node = view('input.checkbox', id=name, label=label, checked=clean, help=help_text)\n    return {'view': node, 'value': clean}",
  "settings": [
   {
    "name": "name",
    "default": "checkbox"
   },
   {
    "name": "label",
    "default": "Option"
   },
   {
    "name": "help_text",
    "default": ""
   }
  ],
  "inputs": [
   "value"
  ],
  "outputs": [
   "view",
   "value"
  ],
  "runtime": [
   "coerce_value",
   "view"
  ],
  "imports": []
 },
 "Trim Whitespace": {
  "function": "trim_whitespace",
  "source": "def trim_whitespace(ctx, *, text) -> dict:\n    s = as_text(text, 'text')\n    return {'text': s.strip()}",
  "settings": [],
  "inputs": [
   "text"
  ],
  "outputs": [
   "text"
  ],
  "runtime": [
   "as_text"
  ],
  "imports": []
 },
 "Update Existing Record": {
  "function": "update_existing_record",
  "source": "def update_existing_record(ctx, *, id, changes, table: str='records', expected_version: int | None=None) -> dict:\n    if not isinstance(changes, dict):\n        raise CardError('invalid_input', 'Changes must be a record.')\n    try:\n        rec_id = int(id)\n    except (TypeError, ValueError):\n        raise CardError('invalid_input', 'ID must be a number.') from None\n    record = ctx.store.update(table, rec_id, changes, expected_version=expected_version)\n    return {'record': record}",
  "settings": [
   {
    "name": "table",
    "default": "records"
   },
   {
    "name": "expected_version",
    "default": null
   }
  ],
  "inputs": [
   "id",
   "changes"
  ],
  "outputs": [
   "record"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 },
 "Update Field Across Records": {
  "function": "update_field_across_records",
  "source": "def update_field_across_records(ctx, *, ids, field, value, table: str='records', limit: int=MAX_LOOP_ITEMS) -> dict:\n    if not isinstance(ids, (list, tuple)):\n        raise CardError('invalid_input', 'IDs must be a list.')\n    if not isinstance(field, str) or not field.strip():\n        raise CardError('invalid_input', 'Field must be a non-empty text.')\n    id_list = bounded(ids, limit, 'records')\n    count = 0\n    with ctx.store.transaction():\n        for rec_id in id_list:\n            try:\n                rid = int(rec_id)\n            except (TypeError, ValueError):\n                raise CardError('invalid_input', f'{rec_id!r} is not a record id.') from None\n            ctx.store.update(table, rid, {field: value})\n            count += 1\n    return {'count': count}",
  "settings": [
   {
    "name": "table",
    "default": "records"
   },
   {
    "name": "limit",
    "default": 10000
   }
  ],
  "inputs": [
   "ids",
   "field",
   "value"
  ],
  "outputs": [
   "count"
  ],
  "runtime": [
   "CardError",
   "MAX_LOOP_ITEMS",
   "bounded"
  ],
  "imports": []
 },
 "Validate Against Allowed List": {
  "function": "validate_against_allowed_list",
  "source": "def validate_against_allowed_list(ctx, *, value, field: str='value', allowed: list=None) -> dict:\n    if allowed is None:\n        allowed = []\n    spec = {'type': 'choice', 'required': True, 'choices': allowed}\n    clean = coerce_value(spec, value, field)\n    return {'value': clean}",
  "settings": [
   {
    "name": "field",
    "default": "value"
   },
   {
    "name": "allowed",
    "default": null
   }
  ],
  "inputs": [
   "value"
  ],
  "outputs": [
   "value"
  ],
  "runtime": [
   "coerce_value"
  ],
  "imports": []
 },
 "Validate Date Order": {
  "function": "validate_date_order",
  "source": "def validate_date_order(ctx, *, value, start_field: str='start_date', end_field: str='end_date', allow_equal: bool=True) -> dict:\n    start = to_date(get_field(value, start_field), start_field)\n    end = to_date(get_field(value, end_field), end_field)\n    if allow_equal:\n        if start > end:\n            raise CardError('date_order_invalid', f'{start_field} must be on or before {end_field}.', {'start_field': start_field, 'end_field': end_field})\n    elif start >= end:\n        raise CardError('date_order_invalid', f'{start_field} must be before {end_field}.', {'start_field': start_field, 'end_field': end_field})\n    return {'value': value}",
  "settings": [
   {
    "name": "start_field",
    "default": "start_date"
   },
   {
    "name": "end_field",
    "default": "end_date"
   },
   {
    "name": "allow_equal",
    "default": true
   }
  ],
  "inputs": [
   "value"
  ],
  "outputs": [
   "value"
  ],
  "runtime": [
   "CardError",
   "get_field",
   "to_date"
  ],
  "imports": []
 },
 "Validate Field Type": {
  "function": "validate_field_type",
  "source": "def validate_field_type(ctx, *, value, field: str='value', field_type: str='text') -> dict:\n    spec = {'type': field_type, 'required': False}\n    clean = coerce_value(spec, value, field)\n    return {'value': clean}",
  "settings": [
   {
    "name": "field",
    "default": "value"
   },
   {
    "name": "field_type",
    "default": "text"
   }
  ],
  "inputs": [
   "value"
  ],
  "outputs": [
   "value"
  ],
  "runtime": [
   "coerce_value"
  ],
  "imports": []
 },
 "Validate Number Range": {
  "function": "validate_number_range",
  "source": "def validate_number_range(ctx, *, value, field: str='value', min: float | None=None, max: float | None=None) -> dict:\n    spec = {'type': 'number', 'required': True, 'min': min, 'max': max}\n    clean = coerce_value(spec, value, field)\n    return {'value': clean}",
  "settings": [
   {
    "name": "field",
    "default": "value"
   },
   {
    "name": "min",
    "default": null
   },
   {
    "name": "max",
    "default": null
   }
  ],
  "inputs": [
   "value"
  ],
  "outputs": [
   "value"
  ],
  "runtime": [
   "coerce_value"
  ],
  "imports": []
 },
 "Verify Sum Equals Total": {
  "function": "verify_sum_equals_total",
  "source": "def verify_sum_equals_total(ctx, *, value, items_field: str='items', amount_field: str='amount', total_field: str='total') -> dict:\n    items = get_field(value, items_field) or []\n    total = to_number(get_field(value, total_field), total_field)\n    computed_sum = sum((to_number(get_field(item, amount_field), amount_field) for item in items))\n    if abs(computed_sum - total) > 1e-09:\n        raise CardError('sum_mismatch', f'Sum of {items_field}.{amount_field} ({computed_sum}) does not match {total_field} ({total}).')\n    return {'value': value}",
  "settings": [
   {
    "name": "items_field",
    "default": "items"
   },
   {
    "name": "amount_field",
    "default": "amount"
   },
   {
    "name": "total_field",
    "default": "total"
   }
  ],
  "inputs": [
   "value"
  ],
  "outputs": [
   "value"
  ],
  "runtime": [
   "CardError",
   "get_field",
   "to_number"
  ],
  "imports": []
 },
 "Wait For All Steps To Complete": {
  "function": "wait_for_all_steps_to_complete",
  "source": "def wait_for_all_steps_to_complete(ctx, *, branches: list[dict]) -> dict:\n    if not isinstance(branches, list):\n        raise CardError('invalid_input', 'Branches must be a list.')\n    bounded(branches, MAX_LOOP_ITEMS, 'branches')\n    results = []\n    all_done = True\n    for branch in branches:\n        if not isinstance(branch, dict):\n            raise CardError('invalid_input', 'Each branch must be a record.')\n        if not branch.get('done', False):\n            all_done = False\n            break\n        results.append(branch.get('result', {}))\n    return {'all_done': all_done, 'results': results if all_done else []}",
  "settings": [],
  "inputs": [
   "branches"
  ],
  "outputs": [
   "results",
   "all_done"
  ],
  "runtime": [
   "CardError",
   "MAX_LOOP_ITEMS",
   "bounded"
  ],
  "imports": []
 },
 "Wait For Condition With Timeout": {
  "function": "wait_for_condition_with_timeout",
  "source": "def wait_for_condition_with_timeout(ctx, *, condition: bool, timeout_seconds: int=60, elapsed: int=0) -> dict:\n    if timeout_seconds < 0:\n        raise CardError('invalid_input', 'Timeout must be a positive number of seconds.')\n    if elapsed < 0:\n        raise CardError('invalid_input', 'Elapsed time cannot be negative.')\n    if condition:\n        return {'ready': True, 'timeout': False, 'wait_more': False}\n    if elapsed >= timeout_seconds:\n        return {'ready': False, 'timeout': True, 'wait_more': False}\n    return {'ready': False, 'timeout': False, 'wait_more': True}",
  "settings": [
   {
    "name": "timeout_seconds",
    "default": 60
   }
  ],
  "inputs": [
   "condition",
   "elapsed"
  ],
  "outputs": [
   "ready",
   "timeout",
   "wait_more"
  ],
  "runtime": [
   "CardError"
  ],
  "imports": []
 }
};
