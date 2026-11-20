"""Timer Triggers (Triggers / Orchestration). Cards that run on a schedule during preview."""
from __future__ import annotations

from ..runtime import CardError, card, iso, to_datetime

CATEGORY = "Triggers / Orchestration"
GROUP = "Timer Triggers"


@card(
    "Run On A Timer",
    category=CATEGORY, group=GROUP,
    inputs=[], outputs=["fire", "event", "next_due"],
    phase="runtime", effects=[], idempotent=True, role="trigger",
    examples=[
        {"label": "recurring timer fires and schedules next",
         "args": {"interval_seconds": 60, "repeat": True},
         "expect": {"fire": True, "event": {"kind": "timer_tick", "interval": 60, "repeat": True}, 
                   "next_due": "2026-01-15T09:31:00"},
         "preview": True, "now": "2026-01-15T09:30:00"},
        {"label": "one-shot timer fires with no next",
         "args": {"interval_seconds": 30, "repeat": False},
         "expect": {"fire": True, "event": {"kind": "timer_tick", "interval": 30, "repeat": False}, 
                   "next_due": None},
         "preview": True},
        {"label": "not due yet: does not fire",
         "args": {"interval_seconds": 60, "last_fired": "2026-01-15T09:29:30"},
         "expect": {"fire": False, "next_due": "2026-01-15T09:30:30"}, "now": "2026-01-15T09:30:00"},
        {"label": "late tick fires once and the missed ones are skipped",
         "args": {"interval_seconds": 60, "last_fired": "2026-01-15T08:00:00"},
         "expect": {"fire": True, "next_due": "2026-01-15T09:31:00"}, "now": "2026-01-15T09:30:00"},
        {"label": "a one-shot timer that already fired stays quiet",
         "args": {"interval_seconds": 60, "repeat": False, "last_fired": "2026-01-15T09:00:00"},
         "expect": {"fire": False, "next_due": None}},
    ],
    invalid=[
        {"label": "last_fired is not a date",
         "args": {"interval_seconds": 60, "last_fired": "soon"}, "code": "not_a_date"},
        {"label": "cannot run outside preview",
         "args": {"interval_seconds": 60},
         "preview": False, "code": "preview_only"},
        {"label": "negative interval not allowed",
         "args": {"interval_seconds": -10},
         "code": "invalid_input",
         "preview": True},
    ],
)
def run_on_a_timer(ctx, *, interval_seconds: int = 60, repeat: bool = True, label: str = "Timer",
                   last_fired: str | None = None) -> dict:
    """Runs a flow once after a delay, or again and again at a fixed interval, only while the app preview is running."""
    ctx.require_preview()

    if not isinstance(interval_seconds, (int, float)) or isinstance(interval_seconds, bool) or interval_seconds <= 0:
        raise CardError("invalid_input", "Timer interval must be positive.")

    from datetime import timedelta

    # The engine passes back ``last_fired`` (the ``at`` of the previous tick). A tick that is not
    # due yet does not fire; a late one fires once and the missed ones are skipped, not replayed.
    if last_fired is not None:
        if not repeat:
            return {"fire": False, "event": {}, "next_due": None}
        due_at = to_datetime(last_fired, "last_fired") + timedelta(seconds=interval_seconds)
        if ctx.now() < due_at:
            return {"fire": False, "event": {}, "next_due": iso(due_at)}

    fire = True
    event = {"kind": "timer_tick", "interval": interval_seconds, "repeat": repeat, "label": label, "at": iso(ctx.now())}
    next_due = iso(ctx.now() + timedelta(seconds=interval_seconds)) if repeat else None
    
    return {"fire": fire, "event": event, "next_due": next_due}


@card(
    "Run At App Start",
    category=CATEGORY, group=GROUP,
    inputs=["started"], outputs=["fire", "event"],
    phase="runtime", effects=[], idempotent=True, role="trigger",
    examples=[
        {"label": "app started fires event",
         "args": {"started": True},
         "expect": {"fire": True, "event": {"kind": "app_start", "at": "2026-01-15T09:30:00"}},
         "preview": True, "now": "2026-01-15T09:30:00"},
        {"label": "app not started does not fire",
         "args": {"started": False},
         "expect": {"fire": False, "event": {}},
         "preview": True},
    ],
    invalid=[
        {"label": "cannot run outside preview",
         "args": {"started": True},
         "preview": False, "code": "preview_only"},
    ],
)
def run_at_app_start(ctx, *, started, description: str = "Initialize app") -> dict:
    """Runs a flow automatically when the app preview begins running."""
    ctx.require_preview()
    
    fire = bool(started)
    event = {"kind": "app_start", "at": iso(ctx.now()), "description": description} if fire else {}
    
    return {"fire": fire, "event": event}
