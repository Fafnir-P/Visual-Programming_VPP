"""Regression tests for defects found by the independent code review of the card templates."""
import csv
import io
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from card_templates import REGISTRY, load_all  # noqa: E402
from card_templates import runtime as rt  # noqa: E402
from card_templates.runtime import CardError, Context, Store  # noqa: E402

load_all()


def run(name, ctx=None, **kwargs):
    return REGISTRY[name].func(ctx or Context.for_tests(), **kwargs)


def code_of(name, ctx=None, **kwargs):
    try:
        run(name, ctx, **kwargs)
    except CardError as err:
        return err.code
    return None


def ctx_with(table, fields, rows=(), now="2026-01-15T09:30:00", **kw):
    ctx = Context.for_tests(now=now, **kw)
    ctx.store.define_table(table, fields)
    for r in rows:
        ctx.store.insert(table, r)
    return ctx


class Csv(unittest.TestCase):
    FIELDS = [{"name": "name", "type": "text"}, {"name": "price", "type": "number"}]

    def test_import_handles_bom_quotes_newlines_and_converts_types(self):
        ctx = ctx_with("items", self.FIELDS)
        text = '\ufeffname,price\n"Red, Hot",1.5\n"two\nlines",2\n'
        out = run("Import Records From CSV", ctx, content=text, table="items")
        self.assertEqual(out["count"], 2)
        self.assertEqual([(r["name"], r["price"]) for r in out["records"]], [("Red, Hot", 1.5), ("two\nlines", 2)])
        self.assertIsInstance(ctx.store.get("items", 1)["price"], float)

    def test_import_refuses_a_file_with_no_matching_column(self):
        ctx = ctx_with("items", self.FIELDS)
        self.assertEqual(code_of("Import Records From CSV", ctx, content="a,b\n1,2\n", table="items"), "no_matching_columns")
        self.assertEqual(ctx.store.count("items"), 0)

    def test_import_is_all_or_nothing(self):
        ctx = ctx_with("items", self.FIELDS)
        self.assertEqual(code_of("Import Records From CSV", ctx, content="name,price\nA,1\nB,notnumber\n", table="items"), "not_a_number")
        self.assertEqual(ctx.store.count("items"), 0)

    def test_export_blocks_spreadsheet_formulas_and_round_trips(self):
        rows = [{"name": "=HYPERLINK(\"x\")", "price": -5}, {"name": "+1", "price": 2}, {"name": "plain, text", "price": 3}]
        ctx = ctx_with("items", self.FIELDS, rows)
        out = run("Export Table To CSV", ctx, table="items")
        cells = list(csv.DictReader(io.StringIO(out["content"])))
        self.assertEqual(cells[0]["name"], "'=HYPERLINK(\"x\")")
        self.assertEqual(cells[1]["name"], "'+1")
        self.assertEqual(cells[2]["name"], "plain, text")
        self.assertEqual(cells[0]["price"], "-5.0")   # a real number is not touched

    def test_connector_payloads_block_formulas(self):
        out = run("Build Spreadsheet Export", records=[{"a": "=1+1", "b": 3}], headers=["a", "b"])
        self.assertEqual(out["payload"]["rows"], [["'=1+1", 3]])
        out = run("Build Data File", records=[{"a": "@SUM(A1)", "b": "ok"}], format="csv")
        self.assertIn("'@SUM(A1)", out["payload"]["content"])

    def test_csv_safe_cell(self):
        self.assertEqual([rt.csv_safe_cell(v) for v in ("=a", "-a", "@a", "\tx", "ok", 5, None)], ["'=a", "'-a", "'@a", "'\tx", "ok", 5, None])


class RuntimeFixes(unittest.TestCase):
    def test_multichoice_contains_means_a_whole_choice_in_sql_and_memory(self):
        ctx = ctx_with("items", [{"name": "tags", "type": "multichoice", "choices": ["apple", "pineapple", "Fig"]}],
                       [{"tags": ["pineapple"]}, {"tags": ["apple", "Fig"]}, {"tags": []}])
        cond = {"field": "tags", "op": "contains", "value": "APPLE"}
        by_sql = [r["id"] for r in ctx.store.find("items", cond)]
        by_mem = [r["id"] for r in ctx.store.find("items") if rt.matches(r, cond)]
        self.assertEqual((by_sql, by_mem), ([2], [2]))
        self.assertEqual(ctx.store.count("items", {"field": "tags", "op": "contains", "value": "fig"}), 1)

    def test_unique_is_case_insensitive_at_every_level(self):
        st = Store()
        st.define_table("t", [{"name": "sku", "type": "text", "unique": True}])
        st.insert("t", {"sku": "ABC"})
        with self.assertRaises(CardError) as cm:
            st.insert("t", {"sku": "abc"})
        self.assertEqual(cm.exception.code, "duplicate_value")
        # the database index itself refuses it too (second line of defence)
        with self.assertRaises(Exception):
            st._db.execute('INSERT INTO "t" (_created_at,_updated_at,"sku") VALUES (?,?,?)', ("x", "x", "aBc"))
        st2 = Store()
        st2.define_table("t", [{"name": "sku", "type": "text"}])
        st2.insert("t", {"sku": "A"})
        st2.insert("t", {"sku": "a"})
        with self.assertRaises(CardError) as cm:
            st2.update_field("t", "sku", {"unique": True})
        self.assertEqual(cm.exception.code, "duplicate_value")

    def test_datetime_and_time_limits(self):
        spec = {"type": "datetime", "min": "2026-01-01T00:00:00", "max": "2026-12-31T00:00:00"}
        self.assertEqual(rt.coerce_value(spec, "2026-06-01"), "2026-06-01T00:00:00")
        for bad, code in (("2025-12-31", "too_small"), ("2027-01-01", "too_large")):
            with self.assertRaises(CardError) as cm:
                rt.coerce_value(spec, bad)
            self.assertEqual(cm.exception.code, code)
        spec = {"type": "time", "min": "09:00", "max": "17:00"}
        self.assertEqual(rt.coerce_value(spec, "9:30"), "09:30")
        for bad, code in (("08:59", "too_small"), ("17:01", "too_large")):
            with self.assertRaises(CardError) as cm:
                rt.coerce_value(spec, bad)
            self.assertEqual(cm.exception.code, code)

    def test_view_blocks_link_and_markup_prop_names(self):
        for name in ("dataUrl", "imageSrc", "linkHref", "bodyHtml", "onClick", "onload", "html", "style"):
            with self.assertRaises(CardError, msg=name):
                rt.view("display.text", **{name: "x"})
        node = rt.view("display.text", description="ok", scriptable=True, props={"label": "x"})   # these are fine
        self.assertEqual(node["props"], {"label": "x", "description": "ok", "scriptable": True})

    def test_view_props_argument_is_merged(self):
        self.assertEqual(rt.view("display.text", props={"a": 1}, b=2)["props"], {"a": 1, "b": 2})


class CardFixes(unittest.TestCase):
    def test_update_field_across_records_is_all_or_nothing(self):
        ctx = ctx_with("items", [{"name": "qty", "type": "integer", "min": 0}], [{"qty": 1}, {"qty": 2}])
        self.assertEqual(code_of("Update Field Across Records", ctx, ids=[1, 2, 99], field="qty", value=5, table="items"), "not_found")
        self.assertEqual([r["qty"] for r in ctx.store.find("items")], [1, 2])
        self.assertEqual(code_of("Update Field Across Records", ctx, ids=[1, 2], field="qty", value=-1, table="items"), "too_small")
        self.assertEqual([r["qty"] for r in ctx.store.find("items")], [1, 2])
        self.assertEqual(run("Update Field Across Records", ctx, ids=[1, 2], field="qty", value=9, table="items")["count"], 2)

    def test_delete_multiple_records_is_all_or_nothing(self):
        st = Store()
        st.define_table("a", [{"name": "n"}])
        st.define_table("b", [{"name": "a_id", "type": "integer", "references": "a", "protect_delete": True}])
        st.insert_many("a", [{"n": "1"}, {"n": "2"}])
        st.insert("b", {"a_id": 2})
        ctx = Context.for_tests(store=st)
        self.assertEqual(code_of("Delete Multiple Records", ctx, ids=[1, 2], table="a"), "in_use")
        self.assertEqual(st.count("a"), 2)
        self.assertEqual(run("Delete Multiple Records", ctx, ids=[1, 77], table="a")["count"], 1)

    def test_restore_previous_record_version(self):
        ctx = ctx_with("items", [{"name": "qty", "type": "integer"}])
        ctx.store.enable_history("items", 5)
        ctx.store.insert("items", {"qty": 1})
        ctx.store.update("items", 1, {"qty": 2})
        ctx.store.update("items", 1, {"qty": 3})
        self.assertEqual(run("Restore Previous Record Version", ctx, id=1, table="items")["record"]["qty"], 2)
        self.assertEqual(run("Restore Previous Record Version", ctx, id=1, table="items", version=1)["record"]["qty"], 1)

    def test_working_days_refuses_a_backwards_range(self):
        self.assertEqual(code_of("Calculate Working Days", start_date="2026-01-10", end_date="2026-01-05"), "invalid_input")
        self.assertEqual(run("Calculate Working Days", start_date="2026-01-05", end_date="2026-01-05")["working_days"], 1)

    def test_date_cards_keep_the_shape_of_their_input(self):
        self.assertEqual(run("Add Time To Date", date="2026-01-31", amount=1, unit="days")["result"], "2026-02-01")
        self.assertEqual(run("Add Time To Date", date="2026-01-31T10:00:00", amount=1, unit="days")["result"], "2026-02-01T10:00:00")
        self.assertEqual(run("Add Time To Date", date="2026-02-28", amount=1, unit="days")["result"], "2026-03-01")
        self.assertEqual(run("Add Time To Date", date="2028-02-28", amount=1, unit="days")["result"], "2028-02-29")

    def test_approval_is_needed_only_above_the_amount(self):
        for total, expected in ((1000, False), (1000.01, True), (999, False)):
            self.assertEqual(run("Require Approval Above Amount", record={"total": total}, amount_field="total", threshold=1000)["requires_approval"], expected)

    def test_reject_invalid_result_compares_versions(self):
        item = {"key": "o1", "_version": 3}
        self.assertEqual(run("Reject Invalid Result", result={"item_key": "o1", "item_version": 3}, item=item)["valid"], True)
        self.assertEqual(run("Reject Invalid Result", result={"item_key": "o1", "item_version": 2}, item=item)["reason"], "stale")
        self.assertEqual(run("Reject Invalid Result", result={"item_key": "o1"}, item=item)["valid"], True)

    def test_retry_undoes_the_writes_of_a_failed_attempt(self):
        ctx = ctx_with("log", [{"name": "n", "type": "integer"}])
        calls = []

        def step():
            ctx.store.insert("log", {"n": len(calls)})
            calls.append(1)
            if len(calls) < 3:
                raise ValueError("not yet")
            return "done"

        out = run("Retry Failed Step", ctx, step=step, max_attempts=3)
        self.assertEqual((out["success"], out["attempts"]), (True, 3))
        self.assertEqual(ctx.store.count("log"), 1)   # only the attempt that worked stays

    def test_handle_error_catches_a_failing_step_and_undoes_its_writes(self):
        ctx = ctx_with("log", [{"name": "n", "type": "integer"}])

        def step(rec):
            ctx.store.insert("log", {"n": 1})
            raise CardError("boom", "no")

        out = run("Handle Error Without Stopping", ctx, value={"a": 1}, step=step)
        self.assertEqual((out["ok"], out["error"]["code"], out["value"]), (False, "boom", {"a": 1}))
        self.assertEqual(ctx.store.count("log"), 0)

    def test_define_app_settings_is_atomic_and_updates(self):
        ctx = Context.for_tests()
        self.assertEqual(run("Define App Settings", ctx, settings={"currency": "USD", "reorder": 5})["record"]["reorder"], 5)
        self.assertEqual(run("Define App Settings", ctx, settings={"currency": "EUR"})["record"]["currency"], "EUR")
        self.assertEqual(ctx.store.count("app_settings"), 1)

    def test_slider_names_do_not_shadow_builtins(self):
        out = run("Adjust Slider", value=150, min_value=0, max_value=100)
        self.assertEqual((out["value"], out["view"]["props"]["min"], out["view"]["props"]["max"]), (100, 0, 100))

    def test_ai_answer_json_nesting_bomb_is_refused(self):
        bomb = "[" * 5000 + "]" * 5000
        self.assertEqual(code_of("Accept AI Answer", text=bomb, format="json"), "bad_format")

    def test_prepare_prompt_dotted_fields(self):
        out = run("Prepare AI Prompt", record={"product": {"name": "Wrench"}}, template="Classify {product.name}", fields=["product.name"])
        self.assertEqual(out["prompt"], "Classify Wrench")
        self.assertEqual(code_of("Prepare AI Prompt", record={"a": "x"}, template="{a} {", fields=["a"]), "invalid_input")


class ListAndTextFixes(unittest.TestCase):
    def test_sort_puts_blanks_last_both_ways_and_mixes_numbers_with_text(self):
        recs = [{"v": "b"}, {"v": None}, {"v": 10}, {"v": "2"}, {"v": ""}, {"v": "A"}]
        asc = [r["v"] for r in run("Sort Records By Field", records=recs, fields=["v"])["records"]]
        desc = [r["v"] for r in run("Sort Records By Field", records=recs, fields=["v"], descending=True)["records"]]
        self.assertEqual(asc, ["2", 10, "A", "b", None, ""])
        self.assertEqual(desc, ["b", "A", 10, "2", None, ""])

    def test_sort_is_stable_and_leaves_the_input_alone(self):
        recs = [{"k": 1, "n": "a"}, {"k": 1, "n": "b"}, {"k": 0, "n": "c"}]
        out = run("Sort Records By Field", records=recs, fields=["k"])["records"]
        self.assertEqual([r["n"] for r in out], ["c", "a", "b"])
        self.assertEqual([r["n"] for r in recs], ["a", "b", "c"])

    def test_extract_number(self):
        for text, expected in (("Total 5.", 5), ("Price: $12.50 each", 12.5), ("temp -3 C", -3), ("a 7 b 8", 7)):
            self.assertEqual(run("Extract Number From Text", text=text)["number"], expected, text)
        self.assertEqual(code_of("Extract Number From Text", text="none"), "not_a_number")

    def test_template_values_are_not_filled_twice(self):
        out = run("Fill Text Template", record={"a": "{b}", "b": "X"}, template="{a} and {b}")
        self.assertEqual(out["text"], "{b} and X")


class RecordCreatedTrigger(unittest.TestCase):
    def test_walks_through_new_records_one_at_a_time(self):
        ctx = ctx_with("items", [{"name": "name"}], [{"name": "A"}, {"name": "B"}, {"name": "C"}])
        seen, out = None, None
        order = []
        for _ in range(5):
            out = run("Run When Record Created", ctx, table="items", last_checked_id=seen)
            if not out["fire"]:
                break
            order.append(out["record"]["name"])
            seen = out["last_seen_id"]
        self.assertEqual(order, ["A", "B", "C"])
        ctx.store.insert("items", {"name": "D"})
        self.assertEqual(run("Run When Record Created", ctx, table="items", last_checked_id=seen)["record"]["name"], "D")

    def test_record_changed_needs_history_to_watch_fields(self):
        ctx = ctx_with("items", [{"name": "qty", "type": "integer"}, {"name": "note"}], [{"qty": 1, "note": "a"}])
        ctx.store.update("items", 1, {"note": "b"})
        self.assertEqual(code_of("Run When Record Changed", ctx, table="items", record_id=1, last_version=1, watch_fields=["qty"]), "history_required")

    def test_threshold_crossing_directions(self):
        ctx = ctx_with("items", [{"name": "qty", "type": "integer"}], [{"qty": 5}])
        f = lambda **kw: run("Run When Value Crosses Threshold", ctx, table="items", record_id=1, field="qty", threshold=10, **kw)["fire"]
        self.assertTrue(f(direction="below", last_value=12))      # went from 12 to 5: crossed below 10
        self.assertFalse(f(direction="below", last_value=7))      # was already below
        self.assertFalse(f(direction="above", last_value=12))     # not above now


class Timer(unittest.TestCase):
    def test_late_tick_fires_once_and_skips_missed_ticks(self):
        ctx = Context.for_tests(now="2026-01-15T09:30:00")
        out = run("Run On A Timer", ctx, interval_seconds=60, last_fired="2026-01-15T06:00:00")
        self.assertEqual((out["fire"], out["next_due"]), (True, "2026-01-15T09:31:00"))

    def test_tick_not_due_does_not_fire(self):
        ctx = Context.for_tests(now="2026-01-15T09:30:00")
        out = run("Run On A Timer", ctx, interval_seconds=60, last_fired="2026-01-15T09:29:45")
        self.assertEqual((out["fire"], out["next_due"]), (False, "2026-01-15T09:30:45"))

    def test_nothing_fires_outside_preview(self):
        ctx = Context.for_tests(preview=False)
        for name in ("Run On A Timer", "Run At App Start"):
            self.assertEqual(code_of(name, ctx, **({"started": True} if name == "Run At App Start" else {})), "preview_only")


if __name__ == "__main__":
    unittest.main()
