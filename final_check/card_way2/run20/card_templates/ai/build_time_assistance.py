"""Build-Time Assistance (AI Capabilities). Cards that propose schema, validation, mappings and docs at build time."""
from __future__ import annotations

from ..runtime import CardError, card, validate_against

CATEGORY = "AI Capabilities"
GROUP = "Build-Time Assistance"

# Prompts sent to the generator at build time (the generator fills these requests)
PROMPT_RECORD_LAYOUT = """Propose field names and types for a table described below. Return JSON:
{"fields": [{"name": "...", "type": "text|number|integer|bool|date|datetime|choice|email|phone|currency", 
"required": true|false, "choices": [...] (if type is choice)}]}

App description: {description}
Table purpose: {purpose}"""

PROMPT_SAMPLE_RECORDS = """Generate {count} example records for testing. Return JSON: {"records": [{...}, {...}]}
Each record must have these fields with appropriate values: {field_names}
Schema: {schema}"""

PROMPT_FIELD_MAPPINGS = """Match imported columns to record fields. Return JSON:
{"mappings": [{"import_column": "...", "record_field": "...", "confidence": "high|medium|low"}]}
Imported columns: {import_columns}
Record fields: {record_fields}"""

PROMPT_VALIDATION_RULES = """Suggest validation rules for these fields. Return JSON:
{"rules": [{"field": "...", "checks": [{"type": "required|range|length|format", "params": {...}}]}]}
Fields: {fields}"""

PROMPT_ACCEPTANCE_CHECKLIST = """Write a checklist for testing the finished app. Return JSON:
{"checklist": [{"item": "...", "category": "basic|edge_case|error_handling"}]}
Cards used: {cards}"""

PROMPT_EXPLAIN_APP = """Write a 2-3 sentence plain-language explanation of what this app does.
Return JSON: {"explanation": "..."}
Cards: {cards}
Connections: {connections}"""

PROMPT_FIELD_HELP = """Write brief help text (under 80 chars each) for these input fields. Return JSON:
{"help": [{"field": "...", "text": "..."}]}
Fields: {fields}"""


@card(
    "Suggest Record Layout", category=CATEGORY, group=GROUP,
    inputs=["proposal"], outputs=["schema"],
    phase="generation", effects=[], idempotent=True, role="data",
    examples=[
        {"label": "basic table proposal",
         "args": {"proposal": {"fields": [{"name": "item_name", "type": "text", "required": True},
                                          {"name": "quantity", "type": "integer", "required": True}]}},
         "expect": {"schema": [{"name": "item_name", "type": "text", "required": True},
                               {"name": "quantity", "type": "integer", "required": True}]}},
        {"label": "choice field with options",
         "args": {"proposal": {"fields": [{"name": "status", "type": "choice", "required": True,
                                          "choices": ["pending", "shipped"]}]}},
         "expect": {"schema": [{"name": "status", "type": "choice", "required": True,
                               "choices": ["pending", "shipped"]}]}},
    ],
    invalid=[
        {"label": "missing fields list", "args": {"proposal": {}}, "code": "invalid_input"},
        {"label": "unknown field type", "args": {"proposal": {"fields": [{"name": "x", "type": "unknown"}]}},
         "code": "bad_type"},
    ],
)
def suggest_record_layout(ctx, *, proposal) -> dict:
    """Validates and normalizes a table schema proposal from the build-time generator."""
    if not isinstance(proposal, dict) or "fields" not in proposal:
        raise CardError("invalid_input", "Proposal must have a 'fields' list.")
    if not isinstance(proposal["fields"], list) or not proposal["fields"]:
        raise CardError("invalid_input", "Proposal must have at least one field.")
    
    valid_types = {"text", "number", "integer", "bool", "date", "datetime", "time",
                   "choice", "multichoice", "email", "phone", "currency"}
    schema = []
    for field in proposal["fields"]:
        if not isinstance(field, dict) or "name" not in field or "type" not in field:
            raise CardError("invalid_input", "Each field needs 'name' and 'type'.")
        if field["type"] not in valid_types:
            raise CardError("bad_type", f"Unknown type: {field['type']}.")
        clean = {"name": field["name"], "type": field["type"]}
        if field.get("required"):
            clean["required"] = True
        if field["type"] in ("choice", "multichoice") and "choices" in field:
            if not isinstance(field["choices"], list) or not field["choices"]:
                raise CardError("invalid_input", f"Field {field['name']} needs a non-empty choices list.")
            clean["choices"] = field["choices"]
        if "min" in field:
            clean["min"] = field["min"]
        if "max" in field:
            clean["max"] = field["max"]
        if "min_length" in field:
            clean["min_length"] = field["min_length"]
        if "max_length" in field:
            clean["max_length"] = field["max_length"]
        if "default" in field:
            clean["default"] = field["default"]
        schema.append(clean)
    return {"schema": schema}


@card(
    "Draft Sample Records", category=CATEGORY, group=GROUP,
    inputs=["proposal"], outputs=["records"],
    phase="generation", effects=[], idempotent=True, role="data",
    examples=[
        {"label": "generates valid records",
         "args": {"proposal": {"records": [{"item": "Bolt", "qty": 10}, {"item": "Nut", "qty": 5}]},
                  "schema": {"item": {"type": "text", "required": True},
                            "qty": {"type": "integer", "required": True}}},
         "expect": {"records": [{"item": "Bolt", "qty": 10}, {"item": "Nut", "qty": 5}]}},
        {"label": "single record",
         "args": {"proposal": {"records": [{"status": "pending"}]},
                  "schema": {"status": {"type": "text"}}},
         "expect": {"records": [{"status": "pending"}]}},
    ],
    invalid=[
        {"label": "missing records list", "args": {"proposal": {}, "schema": {}}, "code": "invalid_input"},
        {"label": "record missing required field",
         "args": {"proposal": {"records": [{"qty": 5}]},
                  "schema": {"item": {"type": "text", "required": True}, "qty": {"type": "integer"}}},
         "code": "invalid_record"},
    ],
)
def draft_sample_records(ctx, *, proposal, schema: dict) -> dict:
    """Validates example records from the build-time generator against the schema."""
    if not isinstance(proposal, dict) or "records" not in proposal:
        raise CardError("invalid_input", "Proposal must have a 'records' list.")
    if not isinstance(proposal["records"], list) or not proposal["records"]:
        raise CardError("invalid_input", "Proposal must have at least one record.")
    if not isinstance(schema, dict):
        raise CardError("invalid_input", "Schema must be a field map.")
    
    validated = []
    for rec in proposal["records"]:
        clean = validate_against(schema, rec)
        validated.append(clean)
    return {"records": validated}


@card(
    "Propose Field Mappings", category=CATEGORY, group=GROUP,
    inputs=["proposal"], outputs=["mappings"],
    phase="generation", effects=[], idempotent=True, role="data",
    examples=[
        {"label": "simple column mappings",
         "args": {"proposal": {"mappings": [{"import_column": "Item Name", "record_field": "item_name",
                                            "confidence": "high"}]}},
         "expect": {"mappings": [{"import_column": "Item Name", "record_field": "item_name",
                                 "confidence": "high"}]}},
        {"label": "mixed confidence levels",
         "args": {"proposal": {"mappings": [{"import_column": "qty", "record_field": "quantity",
                                            "confidence": "medium"},
                                           {"import_column": "date", "record_field": "order_date",
                                            "confidence": "high"}]}},
         "expect": {"mappings": [{"import_column": "qty", "record_field": "quantity", "confidence": "medium"},
                                {"import_column": "date", "record_field": "order_date", "confidence": "high"}]}},
    ],
    invalid=[
        {"label": "missing mappings list", "args": {"proposal": {}}, "code": "invalid_input"},
        {"label": "invalid confidence level",
         "args": {"proposal": {"mappings": [{"import_column": "x", "record_field": "y", "confidence": "unknown"}]}},
         "code": "invalid_input"},
    ],
)
def propose_field_mappings(ctx, *, proposal) -> dict:
    """Validates and normalizes field mapping proposals from the build-time generator."""
    if not isinstance(proposal, dict) or "mappings" not in proposal:
        raise CardError("invalid_input", "Proposal must have a 'mappings' list.")
    if not isinstance(proposal["mappings"], list):
        raise CardError("invalid_input", "Mappings must be a list.")
    
    valid_confidence = {"high", "medium", "low"}
    cleaned = []
    for mapping in proposal["mappings"]:
        if not isinstance(mapping, dict):
            raise CardError("invalid_input", "Each mapping must be a record.")
        if "import_column" not in mapping or "record_field" not in mapping:
            raise CardError("invalid_input", "Each mapping needs 'import_column' and 'record_field'.")
        confidence = mapping.get("confidence", "medium")
        if confidence not in valid_confidence:
            raise CardError("invalid_input", f"Confidence must be high, medium, or low (got {confidence}).")
        cleaned.append({
            "import_column": str(mapping["import_column"]),
            "record_field": str(mapping["record_field"]),
            "confidence": confidence
        })
    return {"mappings": cleaned}


@card(
    "Draft Validation Rules", category=CATEGORY, group=GROUP,
    inputs=["proposal"], outputs=["rules"],
    phase="generation", effects=[], idempotent=True, role="data",
    examples=[
        {"label": "required field rule",
         "args": {"proposal": {"rules": [{"field": "item_name", "checks": [{"type": "required"}]}]}},
         "expect": {"rules": [{"field": "item_name", "checks": [{"type": "required"}]}]}},
        {"label": "range and length checks",
         "args": {"proposal": {"rules": [{"field": "qty", "checks": [{"type": "range", "params": {"min": 0, "max": 100}}]},
                                        {"field": "name", "checks": [{"type": "length", "params": {"max_length": 50}}]}]}},
         "expect": {"rules": [{"field": "qty", "checks": [{"type": "range", "params": {"min": 0, "max": 100}}]},
                             {"field": "name", "checks": [{"type": "length", "params": {"max_length": 50}}]}]}},
    ],
    invalid=[
        {"label": "missing rules list", "args": {"proposal": {}}, "code": "invalid_input"},
        {"label": "unknown check type",
         "args": {"proposal": {"rules": [{"field": "x", "checks": [{"type": "unknown"}]}]}},
         "code": "invalid_input"},
    ],
)
def draft_validation_rules(ctx, *, proposal) -> dict:
    """Validates and normalizes validation rule proposals from the build-time generator."""
    if not isinstance(proposal, dict) or "rules" not in proposal:
        raise CardError("invalid_input", "Proposal must have a 'rules' list.")
    if not isinstance(proposal["rules"], list):
        raise CardError("invalid_input", "Rules must be a list.")
    
    valid_check_types = {"required", "range", "length", "format", "unique", "pattern"}
    cleaned = []
    for rule in proposal["rules"]:
        if not isinstance(rule, dict) or "field" not in rule or "checks" not in rule:
            raise CardError("invalid_input", "Each rule needs 'field' and 'checks'.")
        if not isinstance(rule["checks"], list):
            raise CardError("invalid_input", "Checks must be a list.")
        clean_checks = []
        for check in rule["checks"]:
            if not isinstance(check, dict) or "type" not in check:
                raise CardError("invalid_input", "Each check needs a 'type'.")
            if check["type"] not in valid_check_types:
                raise CardError("invalid_input", f"Unknown check type: {check['type']}.")
            clean_check = {"type": check["type"]}
            if "params" in check:
                clean_check["params"] = check["params"]
            clean_checks.append(clean_check)
        cleaned.append({"field": str(rule["field"]), "checks": clean_checks})
    return {"rules": cleaned}


@card(
    "Draft Acceptance Checklist", category=CATEGORY, group=GROUP,
    inputs=["proposal"], outputs=["checklist"],
    phase="generation", effects=[], idempotent=True, role="data",
    examples=[
        {"label": "basic checklist items",
         "args": {"proposal": {"checklist": [{"item": "Create a new record", "category": "basic"},
                                            {"item": "Try empty required field", "category": "error_handling"}]}},
         "expect": {"checklist": [{"item": "Create a new record", "category": "basic"},
                                 {"item": "Try empty required field", "category": "error_handling"}]}},
        {"label": "edge case testing",
         "args": {"proposal": {"checklist": [{"item": "Import 100 records", "category": "edge_case"}]}},
         "expect": {"checklist": [{"item": "Import 100 records", "category": "edge_case"}]}},
    ],
    invalid=[
        {"label": "missing checklist", "args": {"proposal": {}}, "code": "invalid_input"},
        {"label": "invalid category",
         "args": {"proposal": {"checklist": [{"item": "test", "category": "unknown"}]}},
         "code": "invalid_input"},
    ],
)
def draft_acceptance_checklist(ctx, *, proposal) -> dict:
    """Validates and normalizes an acceptance checklist proposal from the build-time generator."""
    if not isinstance(proposal, dict) or "checklist" not in proposal:
        raise CardError("invalid_input", "Proposal must have a 'checklist' list.")
    if not isinstance(proposal["checklist"], list) or not proposal["checklist"]:
        raise CardError("invalid_input", "Checklist must have at least one item.")
    
    valid_categories = {"basic", "edge_case", "error_handling"}
    cleaned = []
    for item in proposal["checklist"]:
        if not isinstance(item, dict) or "item" not in item:
            raise CardError("invalid_input", "Each checklist item needs an 'item' field.")
        category = item.get("category", "basic")
        if category not in valid_categories:
            raise CardError("invalid_input", f"Category must be basic, edge_case, or error_handling (got {category}).")
        cleaned.append({"item": str(item["item"]), "category": category})
    return {"checklist": cleaned}


@card(
    "Explain App In Plain Words", category=CATEGORY, group=GROUP,
    inputs=["proposal"], outputs=["explanation"],
    phase="generation", effects=[], idempotent=True, role="data",
    examples=[
        {"label": "short explanation",
         "args": {"proposal": {"explanation": "This app tracks inventory levels and alerts when items need reordering."}},
         "expect": {"explanation": "This app tracks inventory levels and alerts when items need reordering."}},
        {"label": "multi-sentence explanation",
         "args": {"proposal": {"explanation": "Users enter orders and shipments. The app calculates stock on hand. "
                                              "It flags items below the reorder point."}},
         "expect": {"explanation": "Users enter orders and shipments. The app calculates stock on hand. "
                                   "It flags items below the reorder point."}},
    ],
    invalid=[
        {"label": "missing explanation", "args": {"proposal": {}}, "code": "invalid_input"},
        {"label": "explanation too long",
         "args": {"proposal": {"explanation": "x" * 1001}},
         "code": "too_long"},
    ],
)
def explain_app_in_plain_words(ctx, *, proposal, max_length: int = 1000) -> dict:
    """Validates and normalizes an app explanation from the build-time generator."""
    if not isinstance(proposal, dict) or "explanation" not in proposal:
        raise CardError("invalid_input", "Proposal must have an 'explanation' field.")
    text = str(proposal["explanation"]).strip()
    if not text:
        raise CardError("invalid_input", "Explanation cannot be empty.")
    if len(text) > max_length:
        raise CardError("too_long", f"Explanation must be at most {max_length} characters.")
    return {"explanation": text}


@card(
    "Draft Field Help Text", category=CATEGORY, group=GROUP,
    inputs=["proposal"], outputs=["help"],
    phase="generation", effects=[], idempotent=True, role="data",
    examples=[
        {"label": "help text for fields",
         "args": {"proposal": {"help": [{"field": "item_name", "text": "Enter the product name"},
                                       {"field": "quantity", "text": "How many items in stock"}]}},
         "expect": {"help": [{"field": "item_name", "text": "Enter the product name"},
                            {"field": "quantity", "text": "How many items in stock"}]}},
        {"label": "single field help",
         "args": {"proposal": {"help": [{"field": "email", "text": "Your contact email"}]}},
         "expect": {"help": [{"field": "email", "text": "Your contact email"}]}},
    ],
    invalid=[
        {"label": "missing help list", "args": {"proposal": {}}, "code": "invalid_input"},
        {"label": "help text too long",
         "args": {"proposal": {"help": [{"field": "x", "text": "a" * 201}]}},
         "code": "too_long"},
    ],
)
def draft_field_help_text(ctx, *, proposal, max_length: int = 200) -> dict:
    """Validates and normalizes field help text from the build-time generator."""
    if not isinstance(proposal, dict) or "help" not in proposal:
        raise CardError("invalid_input", "Proposal must have a 'help' list.")
    if not isinstance(proposal["help"], list):
        raise CardError("invalid_input", "Help must be a list.")
    
    cleaned = []
    for item in proposal["help"]:
        if not isinstance(item, dict) or "field" not in item or "text" not in item:
            raise CardError("invalid_input", "Each help item needs 'field' and 'text'.")
        text = str(item["text"]).strip()
        if len(text) > max_length:
            raise CardError("too_long", f"Help text for {item['field']} must be at most {max_length} characters.")
        cleaned.append({"field": str(item["field"]), "text": text})
    return {"help": cleaned}
