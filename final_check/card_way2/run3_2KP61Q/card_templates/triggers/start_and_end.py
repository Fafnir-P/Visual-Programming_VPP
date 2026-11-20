"""Start and End (Triggers / Orchestration). The two special cards: where the app begins and where it finishes."""
from __future__ import annotations

from ..runtime import CardError, card, iso

CATEGORY = "Triggers / Orchestration"
GROUP = "Start and End"


@card(
    "App Start",
    category=CATEGORY, group=GROUP,
    inputs=[], outputs=["event", "started_at"],
    phase="runtime", effects=[], idempotent=True, role="start",
    examples=[
        {"label": "the app begins: the event goes out with the start time",
         "args": {},
         "expect": {"event": {"kind": "app_start", "at": "2026-01-15T09:30:00"}, "started_at": "2026-01-15T09:30:00"},
         "preview": True, "now": "2026-01-15T09:30:00"},
        {"label": "a note can say what starts",
         "args": {"description": "Load stock"},
         "expect": {"event": {"kind": "app_start", "description": "Load stock"}},
         "preview": True},
    ],
    invalid=[
        {"label": "cannot run outside preview", "args": {}, "preview": False, "code": "preview_only"},
        {"label": "the note must be text", "args": {"description": 5}, "code": "invalid_input"},
    ],
)
def app_start(ctx, *, description: str = "App starts") -> dict:
    """The one place every flow of the app begins: its event output starts the first cards when the app starts."""
    ctx.require_preview()
    if not isinstance(description, str):
        raise CardError("invalid_input", "The note must be text.")
    now = iso(ctx.now())
    return {"event": {"kind": "app_start", "at": now, "description": description}, "started_at": now}


@card(
    "App End",
    category=CATEGORY, group=GROUP,
    inputs=["finish"], outputs=[],
    phase="runtime", effects=["writes_store"], idempotent=False, role="end",
    examples=[
        {"label": "the app finishes and the finish is written to the event log",
         "args": {"finish": True},
         "expect": {}},
        {"label": "a note can say what finished",
         "args": {"finish": {"orders": 3}, "message": "Orders sent"},
         "expect": {}},
    ],
    invalid=[
        {"label": "nothing reached the end", "args": {"finish": None}, "code": "invalid_input"},
        {"label": "the message must be text", "args": {"finish": True, "message": 7}, "code": "invalid_input"},
    ],
)
def app_end(ctx, *, finish, message: str = "The app has finished") -> dict:
    """Marks a place where the app finishes: when a flow reaches it, the finish is written to the event log."""
    if finish is None:
        raise CardError("invalid_input", "Nothing has reached the end.")
    if not isinstance(message, str):
        raise CardError("invalid_input", "The message must be text.")
    ctx.store.log_event("app_end", message, {"at": iso(ctx.now())})
    return {}
