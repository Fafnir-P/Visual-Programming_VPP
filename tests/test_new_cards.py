"""The cards added to close the wiring gaps, and the Start and End cards."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from card_templates import REGISTRY, load_all  # noqa: E402
from card_templates import ports as P  # noqa: E402
from card_templates.runtime import CardError, Context  # noqa: E402

load_all()


def run(name, ctx=None, **kwargs):
    return REGISTRY[name].func(ctx or Context.for_tests(), **kwargs)


def code_of(name, ctx=None, **kwargs):
    try:
        run(name, ctx, **kwargs)
    except CardError as err:
        return err.code
    return None


class Branch(unittest.TestCase):
    def test_only_a_real_yes_or_no_chooses(self):
        for bad in ("yes", 1, 0, None, [], {}):
            self.assertEqual(code_of("Branch On Yes/No", condition=bad), "invalid_input", bad)

    def test_the_value_goes_out_of_one_port_only(self):
        spec = REGISTRY["Branch On Yes/No"]
        self.assertEqual(spec.outputs, ("yes", "no"))
        for cond, port in ((True, "yes"), (False, "no")):
            out = run("Branch On Yes/No", condition=cond, value={"a": 1})
            self.assertEqual(set(out), {"route", "value"})
            self.assertEqual((out["route"], out["value"]), (port, {"a": 1}))


class Compare(unittest.TestCase):
    def test_every_operator(self):
        table = {"eq": (False, True, False), "ne": (True, False, True), "gt": (False, False, True),
                 "gte": (False, True, True), "lt": (True, False, False), "lte": (True, True, False)}
        for op, (less, same, more) in table.items():
            self.assertEqual(run("Compare Two Numbers", first=1, second=2, operator=op)["result"], less, op)
            self.assertEqual(run("Compare Two Numbers", first=2, second=2, operator=op)["result"], same, op)
            self.assertEqual(run("Compare Two Numbers", first=3, second=2, operator=op)["result"], more, op)

    def test_decimal_noise_and_text_numbers(self):
        self.assertTrue(run("Compare Two Numbers", first=0.1 + 0.2, second=0.3, operator="eq")["result"])
        self.assertFalse(run("Compare Two Numbers", first=0.1 + 0.2, second=0.3, operator="gt")["result"])
        self.assertTrue(run("Compare Two Numbers", first="1,000", second=999, operator="gt")["result"])
        self.assertEqual(code_of("Compare Two Numbers", first=True, second=1), "not_a_number")


class PickAndFilter(unittest.TestCase):
    def test_pick_field_keeps_order_and_leaves_input_alone(self):
        records = [{"id": 2}, {"id": 1}, {"id": 2}]
        before = copy.deepcopy(records)
        self.assertEqual(run("Pick Field From Records", records=records, field="id")["values"], [2, 1, 2])
        self.assertEqual(run("Pick Field From Records", records=records, field="id", unique=True)["values"], [2, 1])
        self.assertEqual(records, before)

    def test_pick_field_dotted_and_zero_is_not_blank(self):
        out = run("Pick Field From Records", records=[{"a": {"b": 0}}, {"a": {"b": False}}, {"a": {}}], field="a.b")
        self.assertEqual(out["values"], [0, False])

    def test_filter_by_date_boundaries(self):
        records = [{"id": i, "d": d} for i, d in enumerate(["2026-01-14", "2026-01-15", "2026-01-16"], 1)]
        ids = lambda op: [r["id"] for r in run("Filter Records By Date", records=records, compare_date="2026-01-15", field="d", operator=op)["records"]]
        self.assertEqual(ids("before"), [1])
        self.assertEqual(ids("on_or_before"), [1, 2])
        self.assertEqual(ids("on"), [2])
        self.assertEqual(ids("on_or_after"), [2, 3])
        self.assertEqual(ids("after"), [3])

    def test_filter_by_date_uses_the_run_time_date(self):
        """The date comes in as an input, so the same card answers differently on another day."""
        records = [{"id": 1, "due": "2026-02-01"}]
        late = run("Filter Records By Date", records=records, compare_date="2026-03-01", field="due", operator="before")["records"]
        early = run("Filter Records By Date", records=records, compare_date="2026-01-01", field="due", operator="before")["records"]
        self.assertEqual((len(late), len(early)), (1, 0))

    def test_filter_returns_the_same_records_not_changed_ones(self):
        records = [{"id": 1, "due": "2026-01-01", "extra": [1]}]
        out = run("Filter Records By Date", records=records, compare_date="2026-02-01", field="due")["records"]
        self.assertEqual(out, records)


class Assembly(unittest.TestCase):
    def test_summary_rows_fit_the_summary_table(self):
        out = run("Build Summary Record", value_1=5, value_2=7.5, labels=["Orders", "Average"])
        self.assertEqual(out["rows"], [{"label": "Orders", "value": 5}, {"label": "Average", "value": 7.5}])
        view = run("Summary Table", data=out["rows"])["view"]
        self.assertEqual(view["props"]["rows"], out["rows"])

    def test_summary_label_rules(self):
        self.assertEqual(code_of("Build Summary Record", value_1=1, labels=["", "b"]), "invalid_input")
        self.assertEqual(code_of("Build Summary Record", value_1=1, labels=[1]), "invalid_input")
        self.assertEqual(code_of("Build Summary Record", value_1=1, value_2=2, labels=["Same", " same "]), "duplicate_value")
        self.assertEqual(code_of("Build Summary Record"), "required")

    def test_set_field_does_not_change_its_input(self):
        base = {"id": 1, "status": "new"}
        out = run("Set Field Of Record", value="late", field=" status ", record=base)["record"]
        self.assertEqual(out, {"id": 1, "status": "late"})
        self.assertEqual(base, {"id": 1, "status": "new"})
        self.assertIsNot(out, base)

    def test_set_field_makes_a_change_record_that_updates_a_saved_record(self):
        ctx = Context.for_tests()
        ctx.store.define_table("items", [{"name": "stock", "type": "integer"}, {"name": "name", "type": "text"}])
        ctx.store.insert("items", {"stock": 1, "name": "Bolt"})
        changes = run("Set Field Of Record", ctx, value=120, field="stock")["record"]
        updated = run("Update Existing Record", ctx, id=1, changes=changes, table="items")["record"]
        self.assertEqual((updated["stock"], updated["name"], updated["_version"]), (120, "Bolt", 2))


class ReadFile(unittest.TestCase):
    def test_the_card_checks_name_type_and_size_and_never_opens_a_file(self):
        self.assertEqual(run("Read Chosen File", filename="a.CSV", content="x")["size"], 1)
        for bad in ("a/b.csv", "..\\a.csv", "C:a.csv", "..", "", "   "):
            self.assertIn(code_of("Read Chosen File", filename=bad, content="x"), ("bad_filename", "file_type_not_allowed"), bad)
        self.assertEqual(code_of("Read Chosen File", filename="a.csv", content=None), "no_file")
        self.assertEqual(code_of("Read Chosen File", filename="a.exe", content="x"), "file_type_not_allowed")

    def test_the_chosen_file_feeds_the_csv_import(self):
        ctx = Context.for_tests()
        ctx.store.define_table("items", [{"name": "sku", "type": "text"}, {"name": "qty", "type": "integer"}])
        file = run("Read Chosen File", ctx, filename="count.csv", content="sku,qty\nA,3\nB,4\n")
        out = run("Import Records", ctx, content=file["content"], table="items")
        self.assertEqual(out["count"], 2)


class StartAndEnd(unittest.TestCase):
    def test_start_is_the_only_card_with_the_start_role_and_has_no_inputs(self):
        starts = [n for n, s in REGISTRY.items() if s.role == "start"]
        ends = [n for n, s in REGISTRY.items() if s.role == "end"]
        self.assertEqual((starts, ends), (["App Start"], ["App End"]))
        self.assertEqual(REGISTRY["App Start"].inputs, ())
        self.assertEqual(REGISTRY["App End"].outputs, ())

    def test_start_runs_only_in_the_preview(self):
        self.assertEqual(code_of("App Start", Context.for_tests(preview=False)), "preview_only")
        out = run("App Start", Context.for_tests(now="2026-01-15T09:30:00"))
        self.assertEqual((out["started_at"], out["event"]["kind"]), ("2026-01-15T09:30:00", "app_start"))

    def test_end_writes_to_the_event_log(self):
        ctx = Context.for_tests(now="2026-01-15T09:30:00")
        self.assertEqual(run("App End", ctx, finish=True, message="Orders sent"), {})
        events = ctx.store.events("app_end")
        self.assertEqual([(e["message"], e["details"]) for e in events], [("Orders sent", {"at": "2026-01-15T09:30:00"})])
        self.assertEqual(code_of("App End", ctx, finish=None), "invalid_input")
        self.assertEqual(len(ctx.store.events("app_end")), 1)

    def test_ports(self):
        start = P.ports_for_card(REGISTRY["App Start"])
        end = P.ports_for_card(REGISTRY["App End"])
        self.assertEqual(start["inputs"], [])
        self.assertEqual([(p["name"], p["cls"]) for p in start["outputs"]], [("event", "control"), ("started_at", "date")])
        self.assertEqual([(p["name"], p["cls"], p["multi"], p["optional"]) for p in end["inputs"]], [("finish", "control", True, False)])
        self.assertEqual(end["outputs"], [])

    def test_the_decorator_allows_no_outputs_only_for_end(self):
        from card_templates import runtime as rt
        saved = dict(rt.REGISTRY)
        try:
            def make(role):
                @rt.card("Temp Card", category="UI / Interface", group="g", inputs=[], outputs=[], role=role,
                         examples=[{"args": {}, "expect": {}}], invalid=[])
                def temp_card(ctx):
                    """Doc."""
                    return {}
            with self.assertRaises(ValueError):
                make("data")
            make("end")
        finally:
            rt.REGISTRY.clear()
            rt.REGISTRY.update(saved)


class Classes(unittest.TestCase):
    def test_value_list_and_record_list_stay_separate(self):
        self.assertFalse(P.classes_compatible("values", "records"))
        self.assertFalse(P.classes_compatible("records", "values"))
        self.assertEqual(P.compat_table()["values"], ["values", "any"])

    def test_new_card_ports(self):
        want = {
            "Branch On Yes/No": ([("condition", "flag"), ("value", "any")], [("yes", "any"), ("no", "any")]),
            "Compare Two Numbers": ([("first", "number"), ("second", "number")], [("result", "flag")]),
            "Pick Field From Records": ([("records", "records")], [("values", "values")]),
            "Filter Records By Date": ([("records", "records"), ("compare_date", "date")], [("records", "records")]),
            "Build Summary Record": ([(f"value_{i}", "any") for i in range(1, 5)], [("record", "record"), ("rows", "records")]),
            "Set Field Of Record": ([("value", "any"), ("record", "record")], [("record", "record")]),
            "Read Chosen File": ([("filename", "text"), ("content", "text")], [("content", "text"), ("filename", "text"), ("size", "number")]),
        }
        for name, (ins, outs) in want.items():
            ports = P.ports_for_card(REGISTRY[name])
            listed = lambda side: [(p["name"], p["cls"]) for p in ports[side] if not p["implicit"]]
            self.assertEqual((listed("inputs"), listed("outputs")), (ins, outs), name)


if __name__ == "__main__":
    unittest.main()
