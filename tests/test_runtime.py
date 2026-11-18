"""Tests for card_templates/runtime.py (run:  python -m unittest discover -s tests -v)"""
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from card_templates import runtime as rt  # noqa: E402
from card_templates.runtime import CardError, Context, Store  # noqa: E402


def code_of(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except CardError as err:
        return err.code
    return None


ITEMS = [
    {"name": "name", "type": "text", "required": True},
    {"name": "qty", "type": "integer", "min": 0},
    {"name": "price", "type": "currency"},
    {"name": "status", "type": "choice", "choices": ["new", "shipped", "late"], "default": "new"},
    {"name": "sku", "type": "text", "unique": True},
    {"name": "due", "type": "date"},
    {"name": "tags", "type": "multichoice", "choices": ["a", "b", "c"]},
    {"name": "total", "type": "number", "computed": {"expr": "qty * price"}},
]


def make_ctx():
    ctx = Context.for_tests()
    ctx.store.define_table("items", ITEMS)
    return ctx


class ValueTests(unittest.TestCase):
    def test_numbers(self):
        self.assertEqual(rt.to_number("1,234.50"), 1234.5)
        self.assertEqual(rt.to_number(" 42 "), 42)
        for bad in ("abc", True, None, float("nan"), "1,2"):
            self.assertEqual(code_of(rt.to_number, bad), "not_a_number", bad)

    def test_rounding_is_half_up(self):
        self.assertEqual(rt.round_half_up(2.675, 2), 2.68)
        self.assertEqual(rt.round_half_up(0.5, 0), 1.0)

    def test_dates(self):
        self.assertEqual(rt.to_date("2026/01/31").isoformat(), "2026-01-31")
        self.assertEqual(code_of(rt.to_date, "31 Jan"), "not_a_date")
        self.assertEqual(rt.iso(rt.to_datetime("2026-01-31")), "2026-01-31T00:00:00")

    def test_coerce(self):
        self.assertEqual(rt.coerce_value({"type": "currency"}, "12.345"), 12.35)
        self.assertEqual(rt.coerce_value({"type": "choice", "choices": ["New"]}, "new"), "New")
        self.assertEqual(rt.coerce_value({"type": "time"}, "9:05"), "09:05")
        self.assertEqual(rt.coerce_value({"type": "bool"}, "Yes"), True)
        self.assertEqual(rt.coerce_value({"type": "bool"}, None), False)
        self.assertEqual(rt.coerce_value({"type": "email"}, " A@B.org "), "a@b.org")
        self.assertIsNone(rt.coerce_value({"type": "number"}, ""))
        for spec, value, code in [
            ({"type": "text", "required": True}, "  ", "required"),
            ({"type": "integer"}, 2.5, "not_an_integer"),
            ({"type": "number", "max": 5}, 6, "too_large"),
            ({"type": "email"}, "nope", "bad_format"),
            ({"type": "phone"}, "12", "bad_format"),
            ({"type": "choice", "choices": ["a"]}, "z", "not_allowed"),
            ({"type": "date", "max": "2026-01-01"}, "2026-02-01", "too_large"),
            ({"type": "text", "max_length": 3}, "abcd", "too_long"),
            ({"type": "wat"}, "x", "bad_type"),
        ]:
            self.assertEqual(code_of(rt.coerce_value, spec, value), code, (spec, value))

    def test_validate_against_lists_every_problem(self):
        try:
            rt.validate_against({"a": {"required": True}, "b": {"type": "integer"}}, {"b": "x", "zzz": 1})
        except CardError as err:
            self.assertEqual(err.code, "invalid_record")
            self.assertEqual(len(err.details["problems"]), 3)
        else:
            self.fail("expected CardError")

    def test_safe_eval(self):
        self.assertEqual(rt.safe_eval("qty * (price + 1)", {"qty": 2, "price": 3}), 8)
        self.assertEqual(rt.safe_eval("max(a, 3) // 2", {"a": 10}), 5)
        for bad, code in [("__import__('os')", "bad_expression"), ("a.b", "bad_expression"), ("x + 1", "unknown_name"),
                          ("1/0", "divide_by_zero"), ("", "bad_expression"), ("2 ** 99", "bad_expression"),
                          ("(lambda: 1)()", "bad_expression"), ("'a' * 3", "bad_expression")]:
            self.assertEqual(code_of(rt.safe_eval, bad, {"a": 1}), code, bad)


class ViewTests(unittest.TestCase):
    def test_view(self):
        node = rt.view("input.text", id="a", label="Name")
        self.assertEqual(node["props"], {"label": "Name"})
        for kwargs in [{"html": "<b>"}, {"onclick": "x()"}, {"href": "http://x"}, {"style": "x"}, {"bad": object()}]:
            self.assertEqual(code_of(rt.view, "display.text", **kwargs), "invalid_view", kwargs)
        self.assertEqual(code_of(rt.view, "script.run"), "invalid_view")
        self.assertEqual(code_of(rt.view, "layout.panel", children=["x"]), "invalid_view")


class ConditionTests(unittest.TestCase):
    def test_validation(self):
        for bad in [{}, {"field": "a"}, {"field": "a", "op": "zz", "value": 1}, {"field": "a", "op": "in", "value": 1},
                    {"field": "a", "op": "between", "value": [1]}, {"all": 1}, {"field": "a", "op": "eq"}]:
            self.assertEqual(code_of(rt.validate_condition, bad), "invalid_condition", bad)
        self.assertEqual(code_of(rt.validate_condition, {"field": "x", "op": "eq", "value": 1}, ["a"]), "unknown_field")

    def test_memory_and_sql_agree(self):
        """The same condition must select the same records in a list and in saved data."""
        ctx = make_ctx()
        rng = random.Random(7)
        names = ["Bolt", "bolt nut", "Screw", "washer", "Nut"]
        rows = []
        for i in range(60):
            rows.append({"name": rng.choice(names), "qty": rng.choice([0, 1, 5, 10, None]),
                         "price": rng.choice([0.5, 1.25, 9.99, None]), "status": rng.choice(["new", "shipped", "late"]),
                         "due": rng.choice(["2026-01-01", "2026-03-15", None]), "sku": f"s{i}"})
        saved = [ctx.store.insert("items", r) for r in rows]
        conds = [
            {"field": "name", "op": "eq", "value": "BOLT"},
            {"field": "name", "op": "ne", "value": "bolt"},
            {"field": "name", "op": "contains", "value": "NU"},
            {"field": "name", "op": "startswith", "value": "s"},
            {"field": "name", "op": "endswith", "value": "t"},
            {"field": "qty", "op": "gt", "value": 4},
            {"field": "qty", "op": "gte", "value": "5"},
            {"field": "qty", "op": "lt", "value": 5},
            {"field": "qty", "op": "lte", "value": 1},
            {"field": "qty", "op": "eq", "value": None},
            {"field": "qty", "op": "between", "value": [1, 5]},
            {"field": "price", "op": "is_empty"},
            {"field": "price", "op": "not_empty"},
            {"field": "status", "op": "in", "value": ["New", "late"]},
            {"field": "status", "op": "not_in", "value": ["new"]},
            {"field": "due", "op": "lt", "value": "2026-02-01"},
            {"field": "due", "op": "between", "value": ["2026-01-01", "2026-12-31"]},
            {"all": [{"field": "qty", "op": "gt", "value": 0}, {"field": "status", "op": "eq", "value": "late"}]},
            {"any": [{"field": "qty", "op": "eq", "value": 0}, {"field": "name", "op": "contains", "value": "%"}]},
            {"all": []}, {"any": []},
            {"field": "name", "op": "contains", "value": "_"},
        ]
        for cond in conds:
            by_sql = sorted(r["id"] for r in ctx.store.find("items", cond))
            by_mem = sorted(r["id"] for r in saved if rt.matches(r, cond))
            self.assertEqual(by_sql, by_mem, cond)
            self.assertEqual(ctx.store.count("items", cond), len(by_sql))

    def test_unknown_field_and_injection(self):
        ctx = make_ctx()
        self.assertEqual(code_of(ctx.store.find, "items", {"field": 'name" OR 1=1 --', "op": "eq", "value": 1}), "unknown_field")
        self.assertEqual(code_of(ctx.store.find, "items", None, order_by="name; DROP TABLE items"), "unknown_field")
        ctx.store.insert("items", {"name": "x'); DROP TABLE items; --", "sku": "1"})
        self.assertEqual(len(ctx.store.find("items", {"field": "name", "op": "contains", "value": "'); DROP"})), 1)
        self.assertEqual(ctx.store.count("items"), 1)


class StoreTests(unittest.TestCase):
    def test_names_are_checked(self):
        s = Store()
        for bad in ["a b", "1x", "x;y", "", "sqlite_x", "vp_x", 'a"b', "_vp_tables"]:
            self.assertEqual(code_of(s.define_table, bad, [{"name": "a"}]), "bad_name", bad)
        self.assertEqual(code_of(s.define_table, "ok", [{"name": "a b"}]), "bad_name")
        self.assertEqual(code_of(s.define_table, "ok", [{"name": "id"}]), "bad_name")
        self.assertEqual(code_of(s.define_table, "ok", [{"name": "a"}, {"name": "a"}]), "duplicate_field")
        self.assertEqual(code_of(s.define_table, "ok", [{"name": "a", "type": "choice"}]), "invalid_input")

    def test_crud_and_validation(self):
        ctx = make_ctx()
        st = ctx.store
        a = st.insert("items", {"name": "Bolt", "qty": "5", "price": "2.50", "sku": "A1", "tags": ["a", "B"]})
        self.assertEqual((a["id"], a["_version"], a["qty"], a["price"], a["status"], a["tags"], a["total"]),
                         (1, 1, 5, 2.5, "new", ["a", "b"], 12.5))
        self.assertEqual(a["_created_at"], "2026-01-15T09:30:00")
        self.assertEqual(code_of(st.insert, "items", {"qty": 1}), "required")
        self.assertEqual(code_of(st.insert, "items", {"name": "x", "bogus": 1}), "unknown_field")
        self.assertEqual(code_of(st.insert, "items", {"name": "x", "sku": "a1"}), "duplicate_value")
        self.assertEqual(code_of(st.insert, "items", {"name": "x", "qty": -1}), "too_small")
        self.assertEqual(code_of(st.insert, "nope", {}), "no_such_table")
        self.assertEqual(st.count("items"), 1)
        b = st.update("items", 1, {"qty": 7})
        self.assertEqual((b["_version"], b["qty"], b["total"]), (2, 7, 17.5))
        self.assertEqual(code_of(st.update, "items", 1, {"qty": 1}, expected_version=1), "version_conflict")
        self.assertEqual(code_of(st.update, "items", 99, {"qty": 1}), "not_found")
        self.assertEqual(code_of(st.update, "items", 1, {"name": ""}), "required")
        st.insert("items", {"name": "Nut", "sku": "B1"})
        self.assertEqual(code_of(st.update, "items", 2, {"sku": "A1"}), "duplicate_value")
        st.update("items", 2, {"sku": "B1"})  # same value, same record: fine
        self.assertEqual(st.delete("items", 2)["name"], "Nut")
        self.assertIsNone(st.get("items", 2))
        self.assertIsNone(st.get("items", "abc"))

    def test_archive_hides_records(self):
        ctx = make_ctx()
        st = ctx.store
        st.insert("items", {"name": "a", "sku": "1"})
        st.set_archived("items", 1, True)
        self.assertEqual(st.count("items"), 0)
        self.assertEqual(st.count("items", include_archived=True), 1)
        self.assertEqual(st.set_archived("items", 1, False)["_archived"], False)
        self.assertEqual(st.count("items"), 1)

    def test_sort_limit_offset(self):
        ctx = make_ctx()
        for i, n in enumerate(["b", "C", "a", "d"]):
            ctx.store.insert("items", {"name": n, "sku": str(i)})
        names = lambda **kw: [r["name"] for r in ctx.store.find("items", **kw)]
        self.assertEqual(names(order_by="name"), ["a", "b", "C", "d"])
        self.assertEqual(names(order_by="-name", limit=2), ["d", "C"])
        self.assertEqual(names(order_by=[{"field": "name"}], limit=2, offset=1), ["b", "C"])
        self.assertEqual(code_of(ctx.store.find, "items", limit=-1), "invalid_input")

    def test_transactions_roll_back_and_nest(self):
        ctx = make_ctx()
        st = ctx.store
        with self.assertRaises(CardError):
            with st.transaction():
                st.insert("items", {"name": "a", "sku": "1"})
                with self.assertRaises(CardError):
                    with st.transaction():
                        st.insert("items", {"name": "b", "sku": "2"})
                        st.insert("items", {"name": "c", "sku": "2"})  # duplicate -> inner rolls back
                self.assertEqual(st.count("items"), 1)
                raise CardError("boom", "outer fails too")
        self.assertEqual(st.count("items"), 0)
        self.assertFalse(st.in_transaction)
        self.assertEqual(len(st.insert_many("items", [{"name": "a", "sku": "1"}, {"name": "b", "sku": "2"}])), 2)
        self.assertEqual(code_of(st.insert_many, "items", [{"name": "c", "sku": "3"}, {"name": "d", "sku": "1"}]), "duplicate_value")
        self.assertEqual(st.count("items"), 2)

    def test_apply_once_and_counter(self):
        st = Store()
        self.assertTrue(st.apply_once("evt-1"))
        self.assertFalse(st.apply_once("evt-1"))
        self.assertTrue(st.apply_once("evt-2"))
        self.assertEqual([st.next_counter("po"), st.next_counter("po"), st.next_counter("inv")], [1, 2, 1])
        self.assertEqual(code_of(st.apply_once, ""), "invalid_input")

    def test_references_and_protected_delete(self):
        st = Store()
        st.define_table("suppliers", [{"name": "name", "required": True}])
        st.define_table("orders", [{"name": "supplier_id", "type": "integer", "references": "suppliers", "protect_delete": True}])
        st.insert("suppliers", {"name": "Acme"})
        self.assertEqual(code_of(st.insert, "orders", {"supplier_id": 9}), "missing_reference")
        st.insert("orders", {"supplier_id": 1})
        self.assertEqual(code_of(st.delete, "suppliers", 1), "in_use")
        st.delete("orders", 1)
        st.delete("suppliers", 1)

    def test_history_keeps_last_versions(self):
        ctx = make_ctx()
        st = ctx.store
        st.enable_history("items", keep=3)
        st.insert("items", {"name": "a", "qty": 0, "sku": "1"})
        for q in range(1, 6):
            st.update("items", 1, {"qty": q})
        hist = st.history("items", 1)
        self.assertEqual([h["version"] for h in hist], [4, 5, 6])
        self.assertEqual(hist[-1]["before"]["qty"], 4)
        self.assertEqual(hist[-1]["after"]["qty"], 5)
        self.assertEqual(code_of(st.enable_history, "items", keep=0), "invalid_input")

    def test_add_field_and_defaults(self):
        ctx = make_ctx()
        ctx.store.insert("items", {"name": "a", "sku": "1"})
        ctx.store.add_field("items", {"name": "note", "type": "text", "default": "n/a"})
        ctx.store.add_field("items", {"name": "made", "type": "date", "default": "{today}"})
        r = ctx.store.insert("items", {"name": "b", "sku": "2"})
        self.assertEqual((r["note"], r["made"]), ("n/a", "2026-01-15"))
        self.assertIsNone(ctx.store.get("items", 1)["note"])
        self.assertEqual(code_of(ctx.store.add_field, "items", {"name": "note"}), "duplicate_field")

    def test_outbox_is_replay_safe(self):
        ctx = make_ctx()
        st = ctx.store
        first = st.outbox_put("p1/evt1/card1", "order_request", {"qty": 5}, "Place the order.", {"ref": {"required": True}})
        again = st.outbox_put("p1/evt1/card1", "order_request", {"qty": 999})
        self.assertEqual(again["payload"], {"qty": 5})
        self.assertEqual(first["status"], "pending")
        self.assertEqual(len(st.outbox_list()), 1)
        self.assertEqual(st.outbox_set("p1/evt1/card1", "done", {"ref": "X1"})["result"], {"ref": "X1"})
        self.assertEqual(st.outbox_list("pending"), [])
        self.assertEqual(code_of(st.outbox_set, "p1/evt1/card1", "weird"), "invalid_input")
        self.assertEqual(code_of(st.outbox_set, "missing", "done"), "not_found")

    def test_event_log(self):
        st = Store()
        st.log_event("error", "bad row", {"row": 3})
        st.log_event("info", "ok")
        self.assertEqual([e["kind"] for e in st.events()], ["error", "info"])
        self.assertEqual(st.events("error")[0]["details"], {"row": 3})


class ContextTests(unittest.TestCase):
    def test_context(self):
        ctx = Context.for_tests(now="2026-02-03T10:20:30", preview=False)
        self.assertEqual(ctx.now().isoformat(), "2026-02-03T10:20:30")
        self.assertEqual(ctx.today().isoformat(), "2026-02-03")
        self.assertEqual(code_of(ctx.require_preview), "preview_only")
        Context.for_tests().require_preview()


class DecoratorTests(unittest.TestCase):
    def setUp(self):
        self._saved = dict(rt.REGISTRY)

    def tearDown(self):
        rt.REGISTRY.clear()
        rt.REGISTRY.update(self._saved)

    def deco(self, **overrides):
        base = dict(category="UI / Interface", group="g", inputs=["a"], outputs=["out"],
                    examples=[{"args": {"a": 1}, "expect": {"out": 1}}], invalid=[{"args": {"a": 0}, "code": "x"}])
        base.update(overrides)
        return rt.card("Test Card", **base)

    def test_good_card_registers(self):
        @self.deco()
        def test_card(ctx, *, a, scale=1):
            """Doubles a."""
            return {"out": a * scale}
        spec = rt.REGISTRY["Test Card"]
        self.assertEqual((spec.inputs, spec.config, spec.outputs, spec.summary), (("a",), ("scale",), ("out",), "Doubles a."))
        self.assertEqual(spec.contract()["function"], "test_card")

    def test_setting_without_default_is_a_required_setting(self):
        @self.deco()
        def test_card(ctx, *, a, table):
            """Doc."""
            return {"out": a}
        spec = rt.REGISTRY["Test Card"]
        self.assertEqual((spec.config, spec.required_config), (("table",), ("table",)))

    def test_bad_cards_are_refused(self):
        def positional(ctx, a):
            """Doc."""
        def no_default(ctx, *, a, b):
            """Doc."""
        def no_doc(ctx, *, a):
            pass
        def no_ctx(*, a):
            """Doc."""
        cases = [
            (self.deco(), positional), (self.deco(), no_doc), (self.deco(), no_ctx),
            (self.deco(category="Nope"), lambda ctx, *, a: {}), (self.deco(phase="later"), lambda ctx, *, a: {}),
            (self.deco(role="x"), lambda ctx, *, a: {}), (self.deco(effects=["magic"]), lambda ctx, *, a: {}),
            (self.deco(inputs=["zzz"]), lambda ctx, *, a: {}), (self.deco(outputs=[]), lambda ctx, *, a: {}),
            (self.deco(examples=[]), lambda ctx, *, a: {}), (self.deco(invalid=[]), lambda ctx, *, a: {}),
        ]
        for decorator, fn in cases:
            fn.__doc__ = fn.__doc__ if fn.__doc__ is not None else None
            if fn.__name__ == "<lambda>":
                fn.__doc__ = "Doc."
            with self.assertRaises(ValueError, msg=fn.__name__):
                decorator(fn)

    def test_duplicate_name(self):
        @self.deco()
        def one(ctx, *, a):
            """Doc."""
            return {"out": a}
        with self.assertRaises(ValueError):
            self.deco()(one)


if __name__ == "__main__":
    unittest.main()
