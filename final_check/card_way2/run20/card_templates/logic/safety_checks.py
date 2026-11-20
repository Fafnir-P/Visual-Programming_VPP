"""Safety Checks (Logic / Validation). Cards that prevent destructive actions."""
from __future__ import annotations

from ..runtime import CardError, bounded, card

CATEGORY = "Logic / Validation"
GROUP = "Safety Checks"


@card(
    "Confirm Destructive Action",
    category=CATEGORY, group=GROUP,
    inputs=["confirmed"], outputs=["proceed"],
    phase="runtime", effects=[], idempotent=True, role="data",
    examples=[
        {"label": "confirmed allows action",
         "args": {"confirmed": True, "action": "delete", "count": 5},
         "expect": {"proceed": True}},
        {"label": "single item does not need confirmation",
         "args": {"confirmed": False, "action": "delete", "count": 1, "require_for_single": False},
         "expect": {"proceed": True}},
    ],
    invalid=[
        {"label": "not confirmed blocks action",
         "args": {"confirmed": False, "action": "delete", "count": 10},
         "code": "confirmation_required"},
        {"label": "single item requires confirmation when flag set",
         "args": {"confirmed": False, "action": "delete", "count": 1, "require_for_single": True},
         "code": "confirmation_required"},
    ],
)
def confirm_destructive_action(ctx, *, confirmed, action: str = "delete", count: int = 1, 
                               require_for_single: bool = False) -> dict:
    """Asks the user to confirm before a high-impact step, such as deleting several records."""
    if count == 1 and not require_for_single:
        return {"proceed": True}
    
    if not confirmed:
        items = "record" if count == 1 else f"{count} records"
        raise CardError("confirmation_required", 
                       f"Confirm to {action} {items}.")
    
    return {"proceed": True}


@card(
    "Stop On Error Threshold",
    category=CATEGORY, group=GROUP,
    inputs=["errors"], outputs=["proceed", "stopped"],
    phase="runtime", effects=[], idempotent=True, role="data",
    examples=[
        {"label": "below threshold continues",
         "args": {"errors": [{"msg": "bad row"}], "threshold": 5, "total_processed": 100},
         "expect": {"proceed": True, "stopped": False}},
        {"label": "at threshold continues",
         "args": {"errors": [{"msg": "e1"}, {"msg": "e2"}], "threshold": 2, "total_processed": 10},
         "expect": {"proceed": True, "stopped": False}},
        {"label": "zero errors always continues",
         "args": {"errors": [], "threshold": 1, "total_processed": 100},
         "expect": {"proceed": True, "stopped": False}},
    ],
    invalid=[
        {"label": "exceeds threshold stops",
         "args": {"errors": [{"msg": "e1"}, {"msg": "e2"}, {"msg": "e3"}], "threshold": 2},
         "code": "error_threshold_exceeded"},
        {"label": "exceeds percentage threshold stops",
         "args": {"errors": [{"msg": "e1"}] * 6, "threshold": 5, "total_processed": 10, "threshold_percent": 50},
         "code": "error_threshold_exceeded"},
    ],
)
def stop_on_error_threshold(ctx, *, errors, threshold: int = 10, total_processed: int = 0, 
                           threshold_percent: float = None) -> dict:
    """Halts processing when the count of validation or import errors exceeds a set limit."""
    if not isinstance(errors, list):
        raise CardError("invalid_input", "Errors must be a list.")
    
    error_count = len(errors)
    
    # Check absolute threshold
    if error_count > threshold:
        raise CardError("error_threshold_exceeded", 
                       f"Too many errors: {error_count} exceeds limit of {threshold}.")
    
    # Check percentage threshold if provided
    if threshold_percent is not None and total_processed > 0:
        error_rate = (error_count / total_processed) * 100
        if error_rate > threshold_percent:
            raise CardError("error_threshold_exceeded", 
                           f"Error rate {error_rate:.1f}% exceeds limit of {threshold_percent}%.")
    
    return {"proceed": True, "stopped": False}
