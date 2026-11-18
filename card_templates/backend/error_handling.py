"""Error Handling (Backend Processing). Handles failures gracefully without stopping the entire flow."""
from __future__ import annotations

from ..runtime import CardError, bounded, card, get_field, is_blank

CATEGORY = "Backend Processing"
GROUP = "Error Handling"


@card(
    "Handle Error Without Stopping", category=CATEGORY, group=GROUP,
    inputs=["value"], outputs=["ok", "value", "error"],
    examples=[
        {"label": "successful operation returns on ok output",
         "args": {"value": {"result": 42}, "check_field": "result"},
         "expect": {"ok": True, "value": {"result": 42}, "error": None}},
        {"label": "missing required field returns on error output",
         "args": {"value": {}, "check_field": "result", "required": True},
         "expect": {"ok": False, "value": {}, "error": {"code": "required", "message": "result is required."}}},
        {"label": "a failing step is caught and its error comes out",
         "args": {"value": {"qty": 1}, "step": lambda rec: (_ for _ in ()).throw(CardError("stock_below_zero", "Not enough stock."))},
         "expect": {"ok": False, "value": {"qty": 1}, "error": {"code": "stock_below_zero"}}},
        {"label": "a working step gives its result",
         "args": {"value": {"qty": 1}, "step": lambda rec: {"qty": rec["qty"] + 1}},
         "expect": {"ok": True, "value": {"qty": 2}, "error": None}},
    ],
    invalid=[
        {"label": "value must be provided", "args": {"value": None}, "code": "invalid_input"},
        {"label": "check_field must be a string", "args": {"value": {"x": 1}, "check_field": 123}, "code": "invalid_input"},
    ],
)
def handle_error_without_stopping(ctx, *, value, step=None, check_field: str = "", required: bool = False) -> dict:
    """Catches a failure in a step so the rest of the flow can carry on along an error path."""
    if value is None:
        raise CardError("invalid_input", "Handle Error Without Stopping needs a value.")
    if step is not None:
        if not callable(step):
            raise CardError("invalid_input", "Step must be callable.")
        try:
            with ctx.store.transaction():   # whatever the step saved is undone if it fails
                value_out = step(value)
        except CardError as err:
            return {"ok": False, "value": value, "error": err.to_dict()}
        return {"ok": True, "value": value_out, "error": None}
    if check_field and not isinstance(check_field, str):
        raise CardError("invalid_input", "Check field must be a field name.")
    
    if check_field and required:
        field_value = get_field(value, check_field) if isinstance(value, dict) else None
        if is_blank(field_value):
            return {
                "ok": False,
                "value": value,
                "error": {"code": "required", "message": f"{check_field} is required."}
            }
    
    return {"ok": True, "value": value, "error": None}


@card(
    "Set Default Value On Error", category=CATEGORY, group=GROUP,
    inputs=["value"], outputs=["value"],
    examples=[
        {"label": "valid value passes through",
         "args": {"value": 42, "default": 0},
         "expect": {"value": 42}},
        {"label": "blank value replaced with default",
         "args": {"value": None, "default": 0},
         "expect": {"value": 0}},
        {"label": "empty string replaced with default",
         "args": {"value": "", "default": "N/A"},
         "expect": {"value": "N/A"}},
    ],
    invalid=[
        {"label": "default is required", "args": {"value": None}, "code": "invalid_input"},
        {"label": "default cannot be None", "args": {"value": None, "default": None}, "code": "invalid_input"},
    ],
)
def set_default_value_on_error(ctx, *, value, default=None) -> dict:
    """Provides a fallback value when a field calculation or transformation fails."""
    if default is None:
        raise CardError("invalid_input", "A default value is required.")
    
    if is_blank(value):
        return {"value": default}
    
    return {"value": value}


@card(
    "Retry Failed Step", category=CATEGORY, group=GROUP,
    inputs=["step"], outputs=["success", "result", "attempts", "error"],
    examples=[
        {"label": "successful step returns result",
         "args": {"step": lambda: {"success": True}, "max_attempts": 3},
         "expect": {"success": True, "attempts": 1, "error": None}},
        {"label": "step that always fails exhausts retries",
         "args": {"step": lambda: (_ for _ in ()).throw(ValueError("failed")), "max_attempts": 2},
         "expect": {"success": False, "attempts": 2, "error": {"code": "max_retries", "message": "Step failed after 2 attempts."}}},
    ],
    invalid=[
        {"label": "step must be callable", "args": {"step": "not-callable", "max_attempts": 3}, "code": "invalid_input"},
        {"label": "max_attempts must be positive", "args": {"step": lambda: None, "max_attempts": 0}, "code": "invalid_input"},
    ],
)
def retry_failed_step(ctx, *, step, max_attempts: int = 3) -> dict:
    """Runs a failed local step again a set number of times, only if it is safe to repeat, then follows the error path."""
    if not callable(step):
        raise CardError("invalid_input", "Step must be callable.")
    if max_attempts < 1:
        raise CardError("invalid_input", "Max attempts must be at least 1.")
    
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            with ctx.store.transaction():   # a failed attempt leaves nothing half-written behind
                result = step()
            return {"success": True, "result": result, "attempts": attempt, "error": None}
        except Exception as err:
            last_error = str(err)
    
    return {
        "success": False,
        "result": None,
        "attempts": max_attempts,
        "error": {"code": "max_retries", "message": f"Step failed after {max_attempts} attempts.", "last_error": last_error}
    }


@card(
    "Log Error Details", category=CATEGORY, group=GROUP,
    inputs=["error"], outputs=["logged", "event_kind"],
    effects=["writes_store"], idempotent=False,
    examples=[
        {"label": "error details saved to event log",
         "args": {"error": {"code": "not_found", "message": "Record not found."}, "kind": "record_error"},
         "expect": {"logged": True, "event_kind": "record_error"}},
        {"label": "string error logged",
         "args": {"error": "Something went wrong", "kind": "general_error"},
         "expect": {"logged": True, "event_kind": "general_error"}},
    ],
    invalid=[
        {"label": "error must be provided", "args": {"error": None, "kind": "error"}, "code": "invalid_input"},
        {"label": "kind must be non-empty", "args": {"error": "fail", "kind": ""}, "code": "invalid_input"},
    ],
)
def log_error_details(ctx, *, error, kind: str = "error") -> dict:
    """Records information about a failure for review without stopping the application flow."""
    if error is None:
        raise CardError("invalid_input", "Error information is required.")
    if not kind or not isinstance(kind, str):
        raise CardError("invalid_input", "Error kind is required.")
    
    if isinstance(error, dict):
        message = error.get("message", str(error))
        details = error
    else:
        message = str(error)
        details = {"error": message}
    
    ctx.store.log_event(kind, message, details)
    
    return {"logged": True, "event_kind": kind}


@card(
    "Flag Record With Error", category=CATEGORY, group=GROUP,
    inputs=["record"], outputs=["record"],
    examples=[
        {"label": "record flagged with error code and message",
         "args": {"record": {"id": 1, "name": "Item"}, "error_code": "invalid", "error_message": "Price missing"},
         "expect": {"record": {"id": 1, "name": "Item", "_error": True, "_error_code": "invalid", "_error_message": "Price missing"}}},
        {"label": "record without error passes through unchanged",
         "args": {"record": {"id": 2, "name": "Valid"}, "has_error": False},
         "expect": {"record": {"id": 2, "name": "Valid"}}},
    ],
    invalid=[
        {"label": "record must be a dict", "args": {"record": [], "error_code": "x", "error_message": "y"}, "code": "invalid_input"},
        {"label": "error_code required when has_error is true", "args": {"record": {"id": 1}, "has_error": True, "error_code": ""}, "code": "invalid_input"},
    ],
)
def flag_record_with_error(ctx, *, record, has_error: bool = True, error_code: str = "error", error_message: str = "") -> dict:
    """Marks a record as having encountered a problem and continues processing remaining records."""
    if not isinstance(record, dict):
        raise CardError("invalid_input", "Flag Record With Error needs a record.")
    if has_error and not error_code:
        raise CardError("invalid_input", "Error code is required when flagging an error.")
    
    flagged = dict(record)
    
    if has_error:
        flagged["_error"] = True
        flagged["_error_code"] = error_code
        if error_message:
            flagged["_error_message"] = error_message
    
    return {"record": flagged}


@card(
    "Skip Invalid Record", category=CATEGORY, group=GROUP,
    inputs=["record"], outputs=["record", "skipped"],
    examples=[
        {"label": "valid record passes through",
         "args": {"record": {"id": 1, "qty": 5}, "condition": {"field": "qty", "op": "gt", "value": 0}},
         "expect": {"record": {"id": 1, "qty": 5}, "skipped": False}},
        {"label": "invalid record is skipped",
         "args": {"record": {"id": 2, "qty": 0}, "condition": {"field": "qty", "op": "gt", "value": 0}},
         "expect": {"record": None, "skipped": True}},
    ],
    invalid=[
        {"label": "record must be a dict", "args": {"record": "text", "condition": {"field": "x", "op": "eq", "value": "y"}}, "code": "invalid_input"},
        {"label": "condition must be a dict", "args": {"record": {"id": 1}, "condition": []}, "code": "invalid_input"},
    ],
)
def skip_invalid_record(ctx, *, record, condition: dict | None = None) -> dict:
    """Removes a record from further processing when it fails validation or transformation."""
    if not isinstance(record, dict):
        raise CardError("invalid_input", "Skip Invalid Record needs a record.")
    
    if condition is None:
        return {"record": record, "skipped": False}
    
    if not isinstance(condition, dict):
        raise CardError("invalid_input", "Condition must be a condition object.")
    
    from ..runtime import matches
    
    if matches(record, condition):
        return {"record": record, "skipped": False}
    
    return {"record": None, "skipped": True}


@card(
    "Collect Error Records", category=CATEGORY, group=GROUP,
    inputs=["records"], outputs=["errors", "valid"],
    examples=[
        {"label": "separates error records from valid ones",
         "args": {"records": [{"id": 1, "_error": True}, {"id": 2}, {"id": 3, "_error": True}], "error_flag": "_error"},
         "expect": {"errors": [{"id": 1, "_error": True}, {"id": 3, "_error": True}], "valid": [{"id": 2}]}},
        {"label": "no errors returns empty error list",
         "args": {"records": [{"id": 1}, {"id": 2}], "error_flag": "_error"},
         "expect": {"errors": [], "valid": [{"id": 1}, {"id": 2}]}},
        {"label": "all errors returns empty valid list",
         "args": {"records": [{"id": 1, "_error": True}, {"id": 2, "_error": True}], "error_flag": "_error"},
         "expect": {"errors": [{"id": 1, "_error": True}, {"id": 2, "_error": True}], "valid": []}},
    ],
    invalid=[
        {"label": "records must be a list", "args": {"records": {"id": 1}, "error_flag": "_error"}, "code": "invalid_input"},
        {"label": "error_flag required", "args": {"records": [], "error_flag": ""}, "code": "invalid_input"},
    ],
)
def collect_error_records(ctx, *, records, error_flag: str = "_error") -> dict:
    """Gathers all records that encountered errors into a separate list for review."""
    if not isinstance(records, list):
        raise CardError("invalid_input", "Collect Error Records needs a list of records.")
    if not error_flag:
        raise CardError("invalid_input", "Error flag field name is required.")
    
    items = bounded(records)
    errors = []
    valid = []
    
    for rec in items:
        if isinstance(rec, dict) and rec.get(error_flag):
            errors.append(rec)
        else:
            valid.append(rec)
    
    return {"errors": errors, "valid": valid}
