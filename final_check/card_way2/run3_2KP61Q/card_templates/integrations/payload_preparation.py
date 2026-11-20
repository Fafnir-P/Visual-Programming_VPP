"""Payload Preparation (Integrations / Connectors). Formats data for human submission."""
from __future__ import annotations

import json

from ..runtime import CardError, bounded, card, csv_safe_cell, get_field, iso

CATEGORY = "Integrations / Connectors"
GROUP = "Payload Preparation"


@card(
    "Build Order Request", category=CATEGORY, group=GROUP,
    inputs=["order"], outputs=["payload", "instructions"],
    phase="human", effects=["outbox"],
    examples=[
        {"label": "simple order",
         "args": {"order": {"supplier": "ACME", "items": [{"sku": "A1", "qty": 10}]}, "format": "json"},
         "expect": {"payload": {"supplier": "ACME", "items": [{"sku": "A1", "qty": 10}]}}},
        {"label": "text format",
         "args": {"order": {"supplier": "SupplyCo", "ref": "ORD-001", "total": 250.00}, "format": "text"},
         "expect": {"instructions": "Submit this order request to the supplier."}},
    ],
    invalid=[
        {"label": "not a record",
         "args": {"order": "text"}, "code": "invalid_input"},
        {"label": "unknown format",
         "args": {"order": {"supplier": "X"}, "format": "xml"}, "code": "invalid_input"},
    ],
)
def build_order_request(ctx, *, order: dict, format: str = "json",
                       instructions: str = "Submit this order request to the supplier.") -> dict:
    """Formats order data into a structured request ready for a person to submit to a supplier."""
    if not isinstance(order, dict):
        raise CardError("invalid_input", "Order must be a record.")
    if format not in ("json", "text"):
        raise CardError("invalid_input", "Format must be 'json' or 'text'.")
    
    if format == "json":
        payload = dict(order)
    else:
        lines = []
        for key, value in order.items():
            lines.append(f"{key}: {value}")
        payload = {"text": "\n".join(lines)}
    
    return {"payload": payload, "instructions": instructions}


@card(
    "Build Shipment Notice", category=CATEGORY, group=GROUP,
    inputs=["shipment"], outputs=["payload", "instructions"],
    phase="human", effects=["outbox"],
    examples=[
        {"label": "shipment with tracking",
         "args": {"shipment": {"carrier": "FedEx", "tracking": "1Z999", "items": 5}},
         "expect": {"payload": {"carrier": "FedEx", "tracking": "1Z999", "items": 5}}},
        {"label": "minimal shipment",
         "args": {"shipment": {"destination": "Warehouse A"}},
         "expect": {"instructions": "Send this shipment notice to the recipient."}},
    ],
    invalid=[
        {"label": "not a record",
         "args": {"shipment": [1, 2]}, "code": "invalid_input"},
        {"label": "empty shipment",
         "args": {"shipment": {}}, "code": "invalid_input"},
    ],
)
def build_shipment_notice(ctx, *, shipment: dict,
                         instructions: str = "Send this shipment notice to the recipient.") -> dict:
    """Formats shipment details into a notice ready for a person to send to a recipient."""
    if not isinstance(shipment, dict):
        raise CardError("invalid_input", "Shipment must be a record.")
    if not shipment:
        raise CardError("invalid_input", "Shipment cannot be empty.")
    
    payload = dict(shipment)
    return {"payload": payload, "instructions": instructions}


@card(
    "Build Supplier Message", category=CATEGORY, group=GROUP,
    inputs=["message"], outputs=["payload", "instructions"],
    phase="human", effects=["outbox"],
    examples=[
        {"label": "inquiry message",
         "args": {"message": {"to": "supplier@example.com", "subject": "Stock inquiry", "body": "Please advise."}},
         "expect": {"payload": {"to": "supplier@example.com", "subject": "Stock inquiry", "body": "Please advise."}}},
        {"label": "short message",
         "args": {"message": {"subject": "Urgent"}},
         "expect": {"instructions": "Send this message to the supplier."}},
    ],
    invalid=[
        {"label": "not a record",
         "args": {"message": "text"}, "code": "invalid_input"},
        {"label": "empty message",
         "args": {"message": {}}, "code": "invalid_input"},
    ],
)
def build_supplier_message(ctx, *, message: dict,
                          instructions: str = "Send this message to the supplier.") -> dict:
    """Formats supplier communication data into a message ready for a person to send."""
    if not isinstance(message, dict):
        raise CardError("invalid_input", "Message must be a record.")
    if not message:
        raise CardError("invalid_input", "Message cannot be empty.")
    
    payload = dict(message)
    return {"payload": payload, "instructions": instructions}


@card(
    "Build Spreadsheet Export", category=CATEGORY, group=GROUP,
    inputs=["records"], outputs=["payload", "instructions"],
    phase="human", effects=["outbox"],
    examples=[
        {"label": "two records",
         "args": {"records": [{"name": "Bolt", "qty": 10}, {"name": "Nut", "qty": 20}], "headers": ["name", "qty"]},
         "expect": {"payload": {"headers": ["name", "qty"], "rows": [["Bolt", 10], ["Nut", 20]]}}},
        {"label": "empty list",
         "args": {"records": [], "headers": ["id"]},
         "expect": {"payload": {"headers": ["id"], "rows": []}}},
    ],
    invalid=[
        {"label": "not a list",
         "args": {"records": "text"}, "code": "invalid_input"},
        {"label": "headers not list",
         "args": {"records": [], "headers": "wrong"}, "code": "invalid_input"},
    ],
)
def build_spreadsheet_export(ctx, *, records: list[dict], headers: list[str] | None = None) -> dict:
    """Formats records into a table ready for a person to paste into a spreadsheet."""
    if not isinstance(records, list):
        raise CardError("invalid_input", "Records must be a list.")
    
    bounded(records, 10000, "records")
    
    if headers is not None and not isinstance(headers, list):
        raise CardError("invalid_input", "Headers must be a list of field names.")
    
    # Infer headers from first record if not provided
    if headers is None:
        if records:
            headers = [k for k in records[0].keys() if not k.startswith("_")]
        else:
            headers = []
    
    rows = []
    for rec in records:
        if not isinstance(rec, dict):
            raise CardError("invalid_input", "Each record must be a dict.")
        row = [csv_safe_cell(get_field(rec, h, "")) for h in headers]   # a cell like =1+1 must not run as a formula
        rows.append(row)
    
    payload = {"headers": headers, "rows": rows}
    return {"payload": payload, "instructions": "Paste this table into a spreadsheet."}


@card(
    "Build Email Text", category=CATEGORY, group=GROUP,
    inputs=["data"], outputs=["payload", "instructions"],
    phase="human", effects=["outbox"],
    examples=[
        {"label": "template filled",
         "args": {"data": {"name": "Alice", "amount": 500}, "template": "Hello {name}, your total is {amount}."},
         "expect": {"payload": {"text": "Hello Alice, your total is 500."}}},
        {"label": "plain data",
         "args": {"data": {"subject": "Reminder", "body": "Please confirm."}},
         "expect": {"payload": {"subject": "Reminder", "body": "Please confirm."}}},
    ],
    invalid=[
        {"label": "not a record",
         "args": {"data": [1, 2]}, "code": "invalid_input"},
        {"label": "template missing key",
         "args": {"data": {"x": 1}, "template": "Value is {y}."}, "code": "missing_field"},
    ],
)
def build_email_text(ctx, *, data: dict, template: str | None = None) -> dict:
    """Formats data into email-ready text ready for a person to copy and send."""
    if not isinstance(data, dict):
        raise CardError("invalid_input", "Data must be a record.")
    
    if template:
        # Simple placeholder replacement
        text = template
        import re
        placeholders = re.findall(r"\{(\w+)\}", template)
        for ph in placeholders:
            if ph not in data:
                raise CardError("missing_field", f"Template uses field '{ph}' which is not in data.")
            text = text.replace(f"{{{ph}}}", str(data[ph]))
        payload = {"text": text}
    else:
        payload = dict(data)
    
    return {"payload": payload, "instructions": "Copy this text and send it by email."}


@card(
    "Build Data File", category=CATEGORY, group=GROUP,
    inputs=["records"], outputs=["payload", "instructions"],
    phase="human", effects=["outbox"],
    examples=[
        {"label": "json format",
         "args": {"records": [{"id": 1, "name": "Item"}], "format": "json"},
         "expect": {"payload": {"format": "json", "content": '[{"id": 1, "name": "Item"}]'}}},
        {"label": "csv format",
         "args": {"records": [{"a": 1, "b": 2}], "format": "csv"},
         "expect": {"instructions": "Upload this file to the other tool."}},
    ],
    invalid=[
        {"label": "not a list",
         "args": {"records": "text"}, "code": "invalid_input"},
        {"label": "unknown format",
         "args": {"records": [], "format": "xml"}, "code": "invalid_input"},
    ],
)
def build_data_file(ctx, *, records: list[dict], format: str = "json",
                   instructions: str = "Upload this file to the other tool.") -> dict:
    """Formats records into a file ready for a person to upload to another tool."""
    if not isinstance(records, list):
        raise CardError("invalid_input", "Records must be a list.")
    if format not in ("json", "csv"):
        raise CardError("invalid_input", "Format must be 'json' or 'csv'.")
    
    bounded(records, 10000, "records")
    
    if format == "json":
        content = json.dumps(records, default=iso)
    else:  # csv
        if not records:
            content = ""
        else:
            import csv
            import io
            headers = [k for k in records[0].keys() if not k.startswith("_")]
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=headers, extrasaction="ignore")
            writer.writeheader()
            writer.writerows([{k: csv_safe_cell(v) for k, v in r.items()} for r in records])
            content = output.getvalue()
    
    payload = {"format": format, "content": content}
    return {"payload": payload, "instructions": instructions}
