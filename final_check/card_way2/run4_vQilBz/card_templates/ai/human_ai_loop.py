"""Human-AI Loop (AI Capabilities). Cards that build prompts for a person to copy to an AI tool and accept the result."""
from __future__ import annotations

import json

from ..runtime import CardError, card, get_field, MAX_TEXT_LENGTH

CATEGORY = "AI Capabilities"
GROUP = "Human-AI Loop"


@card(
    "Prepare AI Prompt", category=CATEGORY, group=GROUP,
    inputs=["record"], outputs=["prompt", "context"],
    phase="human", effects=[], idempotent=True, role="data",
    examples=[
        {"label": "basic prompt with fields",
         "args": {"record": {"item": "Bolt", "description": "Metal fastener"},
                  "template": "Suggest a category for: {item} - {description}",
                  "fields": ["item", "description"]},
         "expect": {"prompt": "Suggest a category for: Bolt - Metal fastener",
                   "context": {"item": "Bolt", "description": "Metal fastener"}}},
        {"label": "prompt with nested field",
         "args": {"record": {"product": {"name": "Wrench", "size": "10mm"}},
                  "template": "Classify {product.name} ({product.size})",
                  "fields": ["product.name", "product.size"]},
         "expect": {"prompt": "Classify Wrench (10mm)",
                   "context": {"product.name": "Wrench", "product.size": "10mm"}}},
    ],
    invalid=[
        {"label": "prompt exceeds max length",
         "args": {"record": {"text": "x" * 10000},
                  "template": "{text}",
                  "fields": ["text"],
                  "max_length": 500},
         "code": "too_long"},
        {"label": "missing required field",
         "args": {"record": {},
                  "template": "Describe {item}",
                  "fields": ["item"]},
         "code": "missing_field"},
    ],
)
def prepare_ai_prompt(ctx, *, record, template: str, fields: list, max_length: int = 5000) -> dict:
    """Formats record fields into a prompt for a person to copy to an outside AI tool."""
    if not isinstance(record, dict):
        raise CardError("invalid_input", "Record must be a dict.")
    if not isinstance(fields, list) or not fields:
        raise CardError("invalid_input", "Fields list must not be empty.")
    if not template or not isinstance(template, str):
        raise CardError("invalid_input", "Template must be a non-empty string.")
    
    # Extract field values
    context = {}
    values = {}
    for field in fields:
        value = get_field(record, field)
        if value is None or (isinstance(value, str) and not value.strip()):
            raise CardError("missing_field", f"Field {field} is required for the prompt.", {"field": field})
        context[field] = value
        # For template substitution, use flat key (replace dots with underscores if needed)
        key = field.replace(".", "_")
        values[key] = value
    
    # Build the prompt. {a.b} in the template means the field a.b
    for field in fields:
        template = template.replace("{" + field + "}", "{" + field.replace(".", "_") + "}")
    try:
        prompt = template.format(**{field.replace(".", "_"): get_field(record, field) for field in fields})
    except KeyError as e:
        raise CardError("missing_field", f"Template refers to a field that was not listed: {e}.", {"field": str(e)}) from None
    except (IndexError, ValueError, AttributeError):
        raise CardError("invalid_input", "Template has a { or } that does not fit.") from None
    
    prompt = prompt.strip()
    if len(prompt) > max_length:
        raise CardError("too_long", f"Prompt must be at most {max_length} characters (got {len(prompt)}).")
    
    return {"prompt": prompt, "context": context}


@card(
    "Accept AI Answer", category=CATEGORY, group=GROUP,
    inputs=["text"], outputs=["answer", "format"],
    phase="human", effects=[], idempotent=True, role="data",
    examples=[
        {"label": "plain text answer",
         "args": {"text": "The item should be in the hardware category."},
         "expect": {"answer": "The item should be in the hardware category.", "format": "text"}},
        {"label": "JSON answer",
         "args": {"text": '{"category": "hardware", "confidence": "high"}', "format": "json"},
         "expect": {"answer": {"category": "hardware", "confidence": "high"}, "format": "json"}},
        {"label": "list answer",
         "args": {"text": "Bolt\nNut\nWasher", "format": "lines"},
         "expect": {"answer": ["Bolt", "Nut", "Washer"], "format": "lines"}},
    ],
    invalid=[
        {"label": "empty answer", "args": {"text": "  "}, "code": "required"},
        {"label": "invalid JSON format",
         "args": {"text": "{not valid json}", "format": "json"},
         "code": "bad_format"},
    ],
)
def accept_ai_answer(ctx, *, text, format: str = "text") -> dict:
    """Receives text from an outside AI tool and parses it into the specified format."""
    if not isinstance(text, str) or not text.strip():
        raise CardError("required", "AI answer cannot be empty.")
    
    text = text.strip()
    if len(text) > MAX_TEXT_LENGTH:
        raise CardError("too_long", f"AI answer is too long (max {MAX_TEXT_LENGTH} characters).")
    
    valid_formats = {"text", "json", "lines"}
    if format not in valid_formats:
        raise CardError("invalid_input", f"Format must be text, json, or lines (got {format}).")
    
    if format == "text":
        return {"answer": text, "format": "text"}
    
    if format == "json":
        try:
            parsed = json.loads(text)
        except (json.JSONDecodeError, RecursionError):   # RecursionError: nested far too deeply
            raise CardError("bad_format", "AI answer is not valid JSON.") from None
        return {"answer": parsed, "format": "json"}
    
    if format == "lines":
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return {"answer": lines, "format": "lines"}
    
    raise CardError("invalid_input", f"Unknown format: {format}.")


@card(
    "Check Answer Shape", category=CATEGORY, group=GROUP,
    inputs=["answer"], outputs=["value", "valid"],
    phase="human", effects=[], idempotent=True, role="data",
    examples=[
        {"label": "valid dict with required keys",
         "args": {"answer": {"category": "hardware", "confidence": "high"},
                  "expected_type": "dict",
                  "required_keys": ["category", "confidence"]},
         "expect": {"value": {"category": "hardware", "confidence": "high"}, "valid": True}},
        {"label": "valid list with min length",
         "args": {"answer": ["option1", "option2", "option3"],
                  "expected_type": "list",
                  "min_length": 2},
         "expect": {"value": ["option1", "option2", "option3"], "valid": True}},
        {"label": "invalid missing key",
         "args": {"answer": {"category": "hardware"},
                  "expected_type": "dict",
                  "required_keys": ["category", "confidence"]},
         "expect": {"value": {"category": "hardware"}, "valid": False}},
        {"label": "invalid list too short",
         "args": {"answer": ["option1"],
                  "expected_type": "list",
                  "min_length": 2},
         "expect": {"value": ["option1"], "valid": False}},
    ],
    invalid=[
        {"label": "wrong type expected dict got list",
         "args": {"answer": ["a", "b"], "expected_type": "dict"},
         "code": "invalid_input"},
        {"label": "wrong type expected list got dict",
         "args": {"answer": {"a": 1}, "expected_type": "list"},
         "code": "invalid_input"},
    ],
)
def check_answer_shape(ctx, *, answer, expected_type: str = "dict", required_keys: list | None = None,
                       min_length: int | None = None, max_length: int | None = None) -> dict:
    """Checks that an AI answer has the expected structure before use."""
    valid_types = {"dict", "list", "text"}
    if expected_type not in valid_types:
        raise CardError("invalid_input", f"Expected type must be dict, list, or text (got {expected_type}).")
    
    # Type check
    if expected_type == "dict" and not isinstance(answer, dict):
        raise CardError("invalid_input", f"Answer must be a dict (got {type(answer).__name__}).")
    if expected_type == "list" and not isinstance(answer, list):
        raise CardError("invalid_input", f"Answer must be a list (got {type(answer).__name__}).")
    if expected_type == "text" and not isinstance(answer, str):
        raise CardError("invalid_input", f"Answer must be text (got {type(answer).__name__}).")
    
    valid = True
    
    # Check required keys for dict
    if expected_type == "dict" and required_keys:
        missing = [k for k in required_keys if k not in answer]
        if missing:
            valid = False
    
    # Check length for list or text
    if expected_type in ("list", "text"):
        length = len(answer)
        if min_length is not None and length < min_length:
            valid = False
        if max_length is not None and length > max_length:
            valid = False
    
    return {"value": answer, "valid": valid}
