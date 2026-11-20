"""Query Building (Data Modeling / Storage). Query and search saved data."""
from __future__ import annotations

from ..runtime import CardError, bounded, card, compile_condition, get_field, to_number, MAX_LOOP_ITEMS

CATEGORY = "Data Modeling / Storage"
GROUP = "Query Building"


@card(
    "Query Saved Records By Criteria", category=CATEGORY, group=GROUP,
    inputs=["where"], outputs=["records", "count"],
    effects=["reads_store"],
    examples=[
        {"label": "simple equality filter",
         "tables": {"items": [{"name": "name", "type": "text"}, {"name": "status", "type": "text"}]},
         "rows": {"items": [{"name": "Bolt", "status": "shipped"}, {"name": "Nut", "status": "pending"}]},
         "args": {"where": {"field": "status", "op": "eq", "value": "shipped"}, "table": "items"},
         "expect": {"count": 1, "records": [{"id": 1, "name": "Bolt", "status": "shipped"}]}},
        {"label": "complex condition with all",
         "tables": {"items": [{"name": "qty", "type": "integer"}, {"name": "status", "type": "text"}]},
         "rows": {"items": [{"qty": 10, "status": "active"}, {"qty": 5, "status": "inactive"}, {"qty": 20, "status": "active"}]},
         "args": {"where": {"all": [{"field": "status", "op": "eq", "value": "active"}, {"field": "qty", "op": "gte", "value": 10}]}, "table": "items"},
         "expect": {"count": 2, "records": [{"id": 1, "qty": 10}, {"id": 3, "qty": 20}]}},
    ],
    invalid=[
        {"label": "invalid condition format",
         "tables": {"items": [{"name": "name", "type": "text"}]},
         "args": {"where": {"field": "name"}, "table": "items"}, "code": "invalid_condition"},
        {"label": "table does not exist",
         "args": {"where": {"field": "name", "op": "eq", "value": "Bolt"}, "table": "missing"}, "code": "no_such_table"},
    ],
)
def query_saved_records_by_criteria(ctx, *, where, table: str = "records", order_by: str | None = None,
                                    limit: int = MAX_LOOP_ITEMS, offset: int = 0,
                                    include_archived: bool = False) -> dict:
    """Reads the saved records of a table that match one or more conditions, joined with AND or OR."""
    if not isinstance(where, dict):
        raise CardError("invalid_input", "Where clause must be a condition record.")
    records = ctx.store.find(table, where=where, order_by=order_by, limit=limit, offset=offset, include_archived=include_archived)
    return {"records": records, "count": len(records)}


@card(
    "Join Related Tables", category=CATEGORY, group=GROUP,
    inputs=["left_records"], outputs=["records", "count"],
    effects=["reads_store"],
    examples=[
        {"label": "join orders with customers",
         "tables": {
             "customers": [{"name": "name", "type": "text"}],
             "orders": [{"name": "customer_id", "type": "integer"}, {"name": "amount", "type": "number"}]
         },
         "rows": {
             "customers": [{"name": "Alice"}, {"name": "Bob"}],
             "orders": [{"customer_id": 1, "amount": 100}, {"customer_id": 2, "amount": 200}, {"customer_id": 1, "amount": 150}]
         },
         "args": {
             "left_records": [{"id": 1, "customer_id": 1, "amount": 100}, {"id": 3, "customer_id": 1, "amount": 150}],
             "right_table": "customers", "left_key": "customer_id", "right_key": "id"
         },
         "expect": {"count": 2, "records": [
             {"id": 1, "customer_id": 1, "amount": 100, "customer": {"id": 1, "name": "Alice"}},
             {"id": 3, "customer_id": 1, "amount": 150, "customer": {"id": 1, "name": "Alice"}}
         ]}},
        {"label": "no match returns empty nested record",
         "tables": {"customers": [{"name": "name", "type": "text"}], "orders": [{"name": "customer_id", "type": "integer"}]},
         "rows": {"customers": [{"name": "Alice"}], "orders": [{"customer_id": 99}]},
         "args": {"left_records": [{"id": 1, "customer_id": 99}], "right_table": "customers", "left_key": "customer_id", "right_key": "id"},
         "expect": {"count": 1, "records": [{"id": 1, "customer_id": 99, "customer": None}]}},
    ],
    invalid=[
        {"label": "left records not a list",
         "tables": {"customers": [{"name": "name", "type": "text"}]},
         "args": {"left_records": "invalid", "right_table": "customers", "left_key": "id", "right_key": "id"}, "code": "invalid_input"},
        {"label": "right table does not exist",
         "args": {"left_records": [], "right_table": "missing", "left_key": "id", "right_key": "id"}, "code": "no_such_table"},
    ],
)
def join_related_tables(ctx, *, left_records, right_table: str, left_key: str = "id", right_key: str = "id",
                        nested_name: str | None = None, limit: int = MAX_LOOP_ITEMS) -> dict:
    """Combines records from two related tables into one result set for display or export."""
    if not isinstance(left_records, (list, tuple)):
        raise CardError("invalid_input", "Left records must be a list.")
    ctx.store.schema(right_table)  # raises no_such_table when the table is missing
    items = bounded(left_records, limit, "records")
    nested = nested_name or right_table.rstrip("s")
    result = []
    for rec in items:
        joined = dict(rec)
        key_value = get_field(rec, left_key)
        if key_value is not None:
            matches = ctx.store.find(right_table, where={"field": right_key, "op": "eq", "value": key_value}, limit=1)
            joined[nested] = matches[0] if matches else None
        else:
            joined[nested] = None
        result.append(joined)
    return {"records": result, "count": len(result)}


@card(
    "Search Saved Records By Text", category=CATEGORY, group=GROUP,
    inputs=["query"], outputs=["records", "count"],
    effects=["reads_store"],
    examples=[
        {"label": "search finds matches in any text field",
         "tables": {"items": [{"name": "name", "type": "text"}, {"name": "description", "type": "text"}]},
         "rows": {"items": [{"name": "Bolt", "description": "Metal fastener"}, {"name": "Nut", "description": "Threaded bolt companion"}]},
         "args": {"query": "bolt", "table": "items"},
         "expect": {"count": 2, "records": [{"id": 1, "name": "Bolt"}, {"id": 2, "description": "Threaded bolt companion"}]}},
        {"label": "empty query returns all records",
         "tables": {"items": [{"name": "name", "type": "text"}]},
         "rows": {"items": [{"name": "Bolt"}, {"name": "Nut"}]},
         "args": {"query": "", "table": "items"},
         "expect": {"count": 2, "records": [{"id": 1}, {"id": 2}]}},
    ],
    invalid=[
        {"label": "query not a string",
         "tables": {"items": [{"name": "name", "type": "text"}]},
         "args": {"query": 123, "table": "items"}, "code": "invalid_input"},
        {"label": "table does not exist",
         "args": {"query": "test", "table": "missing"}, "code": "no_such_table"},
    ],
)
def search_saved_records_by_text(ctx, *, query, table: str = "records", fields: list[str] | None = None,
                                 limit: int = 1000, include_archived: bool = False) -> dict:
    """Finds saved records where any text field contains the words or phrase the user enters."""
    if not isinstance(query, str):
        raise CardError("invalid_input", "Query must be text.")
    search_text = query.strip()
    if not search_text:
        records = ctx.store.find(table, limit=limit, include_archived=include_archived)
        return {"records": records, "count": len(records)}
    schema = ctx.store.schema(table)["fields"]
    search_fields = fields if fields else [f["name"] for f in schema if f.get("type") in ("text", "email", "phone", "choice")]
    if not search_fields:
        raise CardError("invalid_input", f"No text fields to search in table {table}.")
    condition = {"any": [{"field": f, "op": "contains", "value": search_text} for f in search_fields]}
    records = ctx.store.find(table, where=condition, limit=limit, include_archived=include_archived)
    return {"records": records, "count": len(records)}


@card(
    "Group And Summarize Saved Data", category=CATEGORY, group=GROUP,
    inputs=[], outputs=["groups", "count"],
    effects=["reads_store"],
    examples=[
        {"label": "group by status and count",
         "tables": {"items": [{"name": "status", "type": "text"}, {"name": "qty", "type": "integer"}]},
         "rows": {"items": [{"status": "active", "qty": 10}, {"status": "inactive", "qty": 5}, {"status": "active", "qty": 20}]},
         "args": {"table": "items", "group_by": "status", "aggregates": [{"field": "qty", "op": "sum", "name": "total_qty"}]},
         "expect": {"count": 2, "groups": [
             {"status": "active", "total_qty": 30, "_count": 2},
             {"status": "inactive", "total_qty": 5, "_count": 1}
         ]}},
        {"label": "count only",
         "tables": {"items": [{"name": "category", "type": "text"}]},
         "rows": {"items": [{"category": "A"}, {"category": "B"}, {"category": "A"}]},
         "args": {"table": "items", "group_by": "category", "aggregates": []},
         "expect": {"count": 2, "groups": [{"category": "A", "_count": 2}, {"category": "B", "_count": 1}]}},
    ],
    invalid=[
        {"label": "table does not exist",
         "args": {"table": "missing", "group_by": "status", "aggregates": []}, "code": "no_such_table"},
        {"label": "aggregates not a list",
         "tables": {"items": [{"name": "status", "type": "text"}]},
         "args": {"table": "items", "group_by": "status", "aggregates": "invalid"}, "code": "invalid_input"},
    ],
)
def group_and_summarize_saved_data(ctx, *, table: str = "records", group_by: str = "status",
                                   aggregates: list[dict] | None = None,
                                   where: dict | None = None, include_archived: bool = False) -> dict:
    """Groups saved records by a field and calculates totals, averages or counts for each group."""
    aggs = aggregates if aggregates is not None else []
    if not isinstance(aggs, list):
        raise CardError("invalid_input", "Aggregates must be a list.")
    records = ctx.store.find(table, where=where, include_archived=include_archived)
    groups_dict: dict[str, dict] = {}
    for rec in records:
        key = str(get_field(rec, group_by, ""))
        if key not in groups_dict:
            groups_dict[key] = {group_by: get_field(rec, group_by), "_count": 0, "_records": []}
        groups_dict[key]["_count"] += 1
        groups_dict[key]["_records"].append(rec)
    result = []
    for group in groups_dict.values():
        group_result = {group_by: group[group_by], "_count": group["_count"]}
        for agg in aggs:
            if not isinstance(agg, dict) or "field" not in agg or "op" not in agg:
                raise CardError("invalid_input", "Each aggregate needs 'field' and 'op'.")
            field_name = agg["field"]
            op = agg["op"]
            name = agg.get("name", f"{op}_{field_name}")
            values = [to_number(get_field(r, field_name), field_name) for r in group["_records"] if get_field(r, field_name) is not None]
            if op == "sum":
                group_result[name] = sum(values) if values else 0
            elif op == "avg":
                group_result[name] = sum(values) / len(values) if values else 0
            elif op == "min":
                group_result[name] = min(values) if values else None
            elif op == "max":
                group_result[name] = max(values) if values else None
            elif op == "count":
                group_result[name] = len(values)
            else:
                raise CardError("invalid_input", f"Unknown aggregate operation: {op}.")
        result.append(group_result)
    return {"groups": result, "count": len(result)}
