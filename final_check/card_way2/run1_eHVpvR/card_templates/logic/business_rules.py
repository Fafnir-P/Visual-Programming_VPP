"""Business Rules (Logic / Validation). Cards that enforce domain-specific business logic."""
from __future__ import annotations

from ..runtime import CardError, card, get_field, to_number

CATEGORY = "Logic / Validation"
GROUP = "Business Rules"


@card(
    "Prevent Negative Stock",
    category=CATEGORY, group=GROUP,
    inputs=["record"], outputs=["record"],
    phase="runtime", effects=[], idempotent=True, role="data",
    examples=[
        {"label": "positive quantity passes",
         "args": {"record": {"qty": 10, "change": -3}, "quantity_field": "qty", "change_field": "change"},
         "expect": {"record": {"qty": 10, "change": -3}}},
        {"label": "zero after change passes",
         "args": {"record": {"qty": 5, "change": -5}, "quantity_field": "qty", "change_field": "change"},
         "expect": {"record": {"qty": 5, "change": -5}}},
    ],
    invalid=[
        {"label": "would go negative",
         "args": {"record": {"qty": 5, "change": -10}, "quantity_field": "qty", "change_field": "change"},
         "code": "stock_below_zero"},
        {"label": "already negative",
         "args": {"record": {"qty": -2, "change": 0}, "quantity_field": "qty", "change_field": "change"},
         "code": "stock_below_zero"},
    ],
)
def prevent_negative_stock(ctx, *, record, quantity_field: str = "quantity", change_field: str = "change") -> dict:
    """Blocks inventory updates that would result in stock quantity falling below zero."""
    if not isinstance(record, dict):
        raise CardError("invalid_input", "Prevent Negative Stock needs a record.")
    
    qty = to_number(get_field(record, quantity_field, 0), quantity_field)
    change = to_number(get_field(record, change_field, 0), change_field)
    
    new_qty = qty + change
    if new_qty < 0:
        raise CardError("stock_below_zero", f"Stock cannot fall below zero (would be {new_qty}).")
    
    return {"record": record}


@card(
    "Flag Reorder Level Reached",
    category=CATEGORY, group=GROUP,
    inputs=["record"], outputs=["record", "flag", "reason"],
    phase="runtime", effects=[], idempotent=True, role="data",
    examples=[
        {"label": "below reorder level is flagged",
         "args": {"record": {"qty": 8, "reorder": 10}, "quantity_field": "qty", "reorder_field": "reorder"},
         "expect": {"record": {"qty": 8, "reorder": 10}, "flag": True, "reason": "Quantity 8 is at or below reorder level 10"}},
        {"label": "at reorder level is flagged",
         "args": {"record": {"qty": 10, "reorder": 10}, "quantity_field": "qty", "reorder_field": "reorder"},
         "expect": {"flag": True}},
        {"label": "above reorder level not flagged",
         "args": {"record": {"qty": 15, "reorder": 10}, "quantity_field": "qty", "reorder_field": "reorder"},
         "expect": {"flag": False}},
    ],
    invalid=[
        {"label": "missing quantity field",
         "args": {"record": {"reorder": 10}, "quantity_field": "qty"},
         "code": "not_a_number"},
    ],
)
def flag_reorder_level_reached(ctx, *, record, quantity_field: str = "quantity", reorder_field: str = "reorder_level") -> dict:
    """Signals when inventory quantity drops to or below the reorder threshold."""
    if not isinstance(record, dict):
        raise CardError("invalid_input", "Flag Reorder Level Reached needs a record.")
    
    qty = to_number(get_field(record, quantity_field), quantity_field)
    reorder = to_number(get_field(record, reorder_field), reorder_field)
    
    flag = qty <= reorder
    reason = f"Quantity {qty} is at or below reorder level {reorder}" if flag else ""
    
    return {"record": record, "flag": flag, "reason": reason}


@card(
    "Require Approval Above Amount",
    category=CATEGORY, group=GROUP,
    inputs=["record"], outputs=["record", "requires_approval", "reason"],
    phase="runtime", effects=[], idempotent=True, role="data",
    examples=[
        {"label": "above threshold requires approval",
         "args": {"record": {"total": 1500}, "amount_field": "total", "threshold": 1000},
         "expect": {"record": {"total": 1500}, "requires_approval": True, "reason": "Amount 1500 exceeds approval threshold 1000"}},
        {"label": "exactly at the threshold does not need approval",
         "args": {"record": {"total": 1000}, "amount_field": "total", "threshold": 1000},
         "expect": {"requires_approval": False}},
        {"label": "below threshold does not require approval",
         "args": {"record": {"total": 999}, "amount_field": "total", "threshold": 1000},
         "expect": {"requires_approval": False, "reason": ""}},
    ],
    invalid=[
        {"label": "non-numeric amount",
         "args": {"record": {"total": "many"}, "amount_field": "total", "threshold": 1000},
         "code": "not_a_number"},
    ],
)
def require_approval_above_amount(ctx, *, record, amount_field: str = "amount", threshold: float = 1000) -> dict:
    """Marks an order or transaction for manual approval if value exceeds a set limit."""
    if not isinstance(record, dict):
        raise CardError("invalid_input", "Require Approval Above Amount needs a record.")
    
    amount = to_number(get_field(record, amount_field, 0), amount_field)
    requires_approval = amount > threshold
    reason = f"Amount {amount} exceeds approval threshold {threshold}" if requires_approval else ""
    
    return {"record": record, "requires_approval": requires_approval, "reason": reason}


@card(
    "Prevent Duplicate Order",
    category=CATEGORY, group=GROUP,
    inputs=["record"], outputs=["record"],
    phase="runtime", effects=["reads_store"], idempotent=True, role="data",
    examples=[
        {"label": "no existing order allows creation",
         "tables": {"orders": [{"name": "customer", "type": "text"}, {"name": "item", "type": "text"}, 
                               {"name": "date", "type": "date"}]},
         "args": {"record": {"customer": "Acme", "item": "Bolt", "date": "2026-01-15"}, "table": "orders"},
         "expect": {"record": {"customer": "Acme", "item": "Bolt", "date": "2026-01-15"}}},
        {"label": "different customer allows creation",
         "tables": {"orders": [{"name": "customer", "type": "text"}, {"name": "item", "type": "text"}, 
                               {"name": "date", "type": "date"}]},
         "rows": {"orders": [{"customer": "Acme", "item": "Bolt", "date": "2026-01-15"}]},
         "args": {"record": {"customer": "Beta", "item": "Bolt", "date": "2026-01-15"}, "table": "orders"},
         "expect": {"record": {"customer": "Beta", "item": "Bolt", "date": "2026-01-15"}}},
    ],
    invalid=[
        {"label": "duplicate customer item and date",
         "tables": {"orders": [{"name": "customer", "type": "text"}, {"name": "item", "type": "text"}, 
                               {"name": "date", "type": "date"}]},
         "rows": {"orders": [{"customer": "Acme", "item": "Bolt", "date": "2026-01-15"}]},
         "args": {"record": {"customer": "Acme", "item": "Bolt", "date": "2026-01-15"}, "table": "orders"},
         "code": "duplicate_order"},
        {"label": "missing key field",
         "tables": {"orders": [{"name": "customer", "type": "text"}, {"name": "item", "type": "text"}, 
                               {"name": "date", "type": "date"}]},
         "args": {"record": {"customer": "Acme", "date": "2026-01-15"}, "table": "orders", 
                  "key_fields": ["customer", "item", "date"]},
         "code": "missing_field"},
    ],
)
def prevent_duplicate_order(ctx, *, record, table: str = "orders", key_fields: list = None) -> dict:
    """Prevents creating a new order when one with the same key details already exists."""
    if not isinstance(record, dict):
        raise CardError("invalid_input", "Prevent Duplicate Order needs a record.")
    
    keys = key_fields or ["customer", "item", "date"]
    
    # Check all key fields exist
    for field in keys:
        if field not in record:
            raise CardError("missing_field", f"Key field {field} is required.", {"field": field})
    
    # Build condition to find matching records
    conditions = [{"field": field, "op": "eq", "value": record[field]} for field in keys]
    where = {"all": conditions}
    
    existing = ctx.store.find(table, where=where, limit=1)
    if existing:
        raise CardError("duplicate_order", f"An order with the same {', '.join(keys)} already exists.")
    
    return {"record": record}


@card(
    "Enforce Lead Time Limit",
    category=CATEGORY, group=GROUP,
    inputs=["record"], outputs=["record"],
    phase="runtime", effects=[], idempotent=True, role="data",
    examples=[
        {"label": "sufficient lead time passes",
         "args": {"record": {"order_date": "2026-01-15", "delivery_date": "2026-01-20"}, 
                  "order_field": "order_date", "delivery_field": "delivery_date", "min_days": 3},
         "expect": {"record": {"order_date": "2026-01-15", "delivery_date": "2026-01-20"}}},
        {"label": "exact minimum days passes",
         "args": {"record": {"order_date": "2026-01-15", "delivery_date": "2026-01-18"}, 
                  "order_field": "order_date", "delivery_field": "delivery_date", "min_days": 3},
         "expect": {"record": {"order_date": "2026-01-15", "delivery_date": "2026-01-18"}}},
    ],
    invalid=[
        {"label": "insufficient lead time",
         "args": {"record": {"order_date": "2026-01-15", "delivery_date": "2026-01-17"}, 
                  "order_field": "order_date", "delivery_field": "delivery_date", "min_days": 3},
         "code": "insufficient_lead_time"},
        {"label": "delivery before order",
         "args": {"record": {"order_date": "2026-01-15", "delivery_date": "2026-01-14"}, 
                  "order_field": "order_date", "delivery_field": "delivery_date", "min_days": 1},
         "code": "insufficient_lead_time"},
    ],
)
def enforce_lead_time_limit(ctx, *, record, order_field: str = "order_date", 
                           delivery_field: str = "delivery_date", min_days: int = 3) -> dict:
    """Ensures a delivery or completion date allows enough days from the order date."""
    if not isinstance(record, dict):
        raise CardError("invalid_input", "Enforce Lead Time Limit needs a record.")
    
    from ..runtime import to_date
    
    order_date = to_date(get_field(record, order_field), order_field)
    delivery_date = to_date(get_field(record, delivery_field), delivery_field)
    
    actual_days = (delivery_date - order_date).days
    
    if actual_days < min_days:
        raise CardError("insufficient_lead_time", 
                       f"Delivery date must be at least {min_days} days after order date (only {actual_days} days).")
    
    return {"record": record}


@card(
    "Check Valid Status Transition",
    category=CATEGORY, group=GROUP,
    inputs=["record"], outputs=["record"],
    phase="runtime", effects=[], idempotent=True, role="data",
    examples=[
        {"label": "valid transition passes",
         "args": {"record": {"old_status": "pending", "new_status": "approved"}, 
                  "old_field": "old_status", "new_field": "new_status",
                  "allowed_transitions": {"pending": ["approved", "rejected"], "approved": ["shipped"]}},
         "expect": {"record": {"old_status": "pending", "new_status": "approved"}}},
        {"label": "same status passes",
         "args": {"record": {"old_status": "pending", "new_status": "pending"}, 
                  "old_field": "old_status", "new_field": "new_status"},
         "expect": {"record": {"old_status": "pending", "new_status": "pending"}}},
    ],
    invalid=[
        {"label": "invalid transition",
         "args": {"record": {"old_status": "pending", "new_status": "shipped"}, 
                  "old_field": "old_status", "new_field": "new_status",
                  "allowed_transitions": {"pending": ["approved", "rejected"], "approved": ["shipped"]}},
         "code": "invalid_transition"},
        {"label": "unknown old status",
         "args": {"record": {"old_status": "unknown", "new_status": "approved"}, 
                  "old_field": "old_status", "new_field": "new_status",
                  "allowed_transitions": {"pending": ["approved"]}},
         "code": "invalid_transition"},
    ],
)
def check_valid_status_transition(ctx, *, record, old_field: str = "old_status", 
                                 new_field: str = "new_status",
                                 allowed_transitions: dict = None) -> dict:
    """Confirms a status change follows allowed steps like pending to shipped to delivered."""
    if not isinstance(record, dict):
        raise CardError("invalid_input", "Check Valid Status Transition needs a record.")
    
    transitions = allowed_transitions or {
        "pending": ["approved", "rejected"],
        "approved": ["shipped", "cancelled"],
        "shipped": ["delivered"],
    }
    
    old_status = str(get_field(record, old_field, "")).strip()
    new_status = str(get_field(record, new_field, "")).strip()
    
    # Same status is always allowed
    if old_status == new_status:
        return {"record": record}
    
    # Check if transition is allowed
    if old_status not in transitions:
        raise CardError("invalid_transition", 
                       f"Unknown status: {old_status}.")
    
    if new_status not in transitions[old_status]:
        allowed = ", ".join(transitions[old_status])
        raise CardError("invalid_transition", 
                       f"Cannot change from {old_status} to {new_status}. Allowed: {allowed}.")
    
    return {"record": record}
