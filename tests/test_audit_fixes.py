"""Regression tests for the final audit fixes (probes taken from final_check/audit_report.txt)."""
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from card_templates import REGISTRY, load_all  # noqa: E402
from card_templates import runtime as rt  # noqa: E402
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


def ctx_with(table, fields, rows=()):
    ctx = Context.for_tests(now="2026-01-15T09:30:00")
    ctx.store.define_table(table, fields)
    for r in rows:
        ctx.store.insert(table, r)
    return ctx


class SearchPatternLimits(unittest.TestCase):
    def test_nested_quantifier_probe_fails_fast(self):
        start = time.time()
        self.assertEqual(code_of("Search Text For Pattern", text="a" * 28 + "!", pattern="(a+)+$"), "bad_expression")
        self.assertLess(time.time() - start, 1)

    def test_other_dangerous_shapes_are_refused(self):
        for pattern in ["(a|a)*$", "(a*)*b", "(a+){2,}", "a*a*a*b", "x" * 201]:
            self.assertIn(code_of("Search Text For Pattern", text="aaa", pattern=pattern),
                          ("bad_expression", "invalid_input"), pattern)

    def test_normal_patterns_still_work(self):
        for text, pattern, expect in [("order 12-34", r"\d+-\d+", "12-34"), ("ab ab", "(ab)+", "ab"),
                                      ("x[y]", r"[\]]", "]"), ("aaa", "a{2,3}", "aaa"), ("Cat", "c.t", "Cat")]:
            self.assertEqual(run("Search Text For Pattern", text=text, pattern=pattern)["match"], expect, pattern)

    def test_long_text_is_refused(self):
        self.assertEqual(code_of("Search Text For Pattern", text="a" * (rt.MAX_TEXT_LENGTH + 1), pattern="a"), "limit_exceeded")
        self.assertEqual(code_of("Search Text For Pattern", text="a" * 10_001, pattern="a+"), "limit_exceeded")
        self.assertEqual(code_of("Search Text For Pattern", text="a" * 1_001, pattern="a*a*b"), "limit_exceeded")

    def test_slow_but_allowed_patterns_are_fast(self):
        start = time.time()
        run("Search Text For Pattern", text="a" * 1_000, pattern="a*a*b")
        run("Search Text For Pattern", text="a" * 10_000, pattern="a*b")
        self.assertLess(time.time() - start, 5)


class ImportLimit(unittest.TestCase):
    def test_12000_rows_import(self):
        ctx = ctx_with("t", [{"name": "n", "type": "integer"}])
        text = "n\n" + "\n".join(str(i) for i in range(12_000)) + "\n"
        self.assertEqual(run("Import Records", ctx, content=text, table="t")["count"], 12_000)

    def test_over_the_import_limit_is_too_many_rows(self):
        ctx = ctx_with("t", [{"name": "n", "type": "integer"}])
        text = "n\n" + "\n".join("1" for _ in range(rt.MAX_IMPORT_ROWS + 1)) + "\n"
        self.assertEqual(code_of("Import Records", ctx, content=text, table="t"), "too_many_rows")

    def test_insert_many_default_limit_still_10000(self):
        ctx = ctx_with("t", [{"name": "n", "type": "integer"}])
        with self.assertRaises(CardError) as e:
            ctx.store.insert_many("t", [{"n": 1}] * 10_001)
        self.assertEqual(e.exception.code, "limit_exceeded")


class InputGuards(unittest.TestCase):
    def test_delete_multiple_ids(self):
        ctx = ctx_with("t", [{"name": "n", "type": "integer"}], [{"n": 1}, {"n": 2}])
        for ids in (["abc"], [None], [0.5], [True]):
            self.assertEqual(code_of("Delete Multiple Records", ctx, ids=ids, table="t"), "invalid_input", ids)
        self.assertEqual(ctx.store.count("t"), 2)
        self.assertEqual(code_of("Delete Multiple Records", ctx, ids=[1, "x"], table="t"), "invalid_input")
        self.assertEqual(ctx.store.count("t"), 2)   # bad id stops everything, nothing deleted
        self.assertEqual(run("Delete Multiple Records", ctx, ids=[1, 2], table="t")["count"], 2)

    def test_paginate_take_extract_types(self):
        recs = [{"id": i} for i in range(5)]
        self.assertEqual(code_of("Paginate Record List", records=recs, page="1"), "invalid_input")
        self.assertEqual(code_of("Paginate Record List", records=recs, page_size=0.5), "invalid_input")
        self.assertEqual(code_of("Take Record Range", records=recs, start="0", end=2), "invalid_input")
        self.assertEqual(code_of("Take Record Range", records=recs, start=0.5, end=2), "invalid_input")
        self.assertEqual(code_of("Extract Substring", text="abc", start="0"), "invalid_input")
        self.assertEqual(code_of("Extract Substring", text="abc", length=None), "invalid_input")
        self.assertEqual(run("Take Record Range", records=recs, start=1, end=3)["records"], [{"id": 1}, {"id": 2}])
        self.assertEqual(run("Paginate Record List", records=recs, page=2, page_size=2)["records"], [{"id": 2}, {"id": 3}])
        self.assertEqual(run("Extract Substring", text="abcdef", start=1, length=2)["text"], "bc")


class SafeEval(unittest.TestCase):
    def test_bad_arguments_are_card_errors(self):
        for expr in ("round(1, 2.5)", "round(1, 2, 3)", "max()", "round(1e308 * 10)"):
            with self.assertRaises(CardError, msg=expr) as e:
                rt.safe_eval(expr)
            self.assertEqual(e.exception.code, "bad_expression", expr)

    def test_non_finite_result_is_refused(self):
        with self.assertRaises(CardError) as e:
            rt.safe_eval("a * a", {"a": 1e200})
        self.assertEqual(e.exception.code, "bad_expression")

    def test_normal_math(self):
        self.assertEqual(rt.safe_eval("qty * price - 1", {"qty": 2, "price": 3}), 5)
        with self.assertRaises(CardError) as e:
            rt.safe_eval("1 / 0")
        self.assertEqual(e.exception.code, "divide_by_zero")


class WorkingDays(unittest.TestCase):
    def test_huge_span_refused_fast(self):
        start = time.time()
        self.assertEqual(code_of("Calculate Working Days", start_date="0001-01-01", end_date="9999-12-31"), "limit_exceeded")
        self.assertLess(time.time() - start, 1)

    def test_last_day_of_year_9999_does_not_overflow(self):
        self.assertEqual(run("Calculate Working Days", start_date="9999-12-27", end_date="9999-12-31")["working_days"], 5)

    def test_normal(self):
        self.assertEqual(run("Calculate Working Days", start_date="2026-01-05", end_date="2026-01-09")["working_days"], 5)


class ExportAndSamples(unittest.TestCase):
    def test_export_filename_is_validated(self):
        ctx = ctx_with("t", [{"name": "n", "type": "text"}])
        for bad in ("../../x.csv", "a/b.csv", "a\\b.csv", "C:x.csv", "..", "."):
            for fmt in ("csv", "json"):
                self.assertEqual(code_of("Export Table", ctx, table="t", filename=bad, format=fmt), "bad_filename", bad)
        self.assertEqual(code_of("Export Table", ctx, table="t", filename=5), "invalid_input")
        self.assertEqual(run("Export Table", ctx, table="t", filename="out.csv")["filename"], "out.csv")
        self.assertEqual(run("Export Table", ctx, table="t")["filename"], "t.csv")

    def test_default_samples_cover_every_required_type(self):
        fields = [
            {"name": "c", "type": "choice", "choices": ["red", "blue"], "required": True},
            {"name": "m", "type": "multichoice", "choices": ["x", "y"], "required": True},
            {"name": "p", "type": "phone", "required": True},
            {"name": "t", "type": "time", "required": True},
            {"name": "d", "type": "datetime", "required": True},
        ]
        ctx = ctx_with("t", fields)
        out = run("Load Sample Data Set", ctx, table="t")
        self.assertEqual(out["count"], 3)
        self.assertEqual(out["records"][0]["c"], "red")


class UniqueIndexNames(unittest.TestCase):
    def test_table_field_pairs_with_same_joined_name_do_not_collide(self):
        ctx = Context.for_tests(now="2026-01-15T09:30:00")
        ctx.store.define_table("a_b", [{"name": "c", "type": "text", "unique": True}])
        ctx.store.define_table("a", [{"name": "b_c", "type": "text", "unique": True}])
        ctx.store.insert("a_b", {"c": "x"})
        ctx.store.insert("a", {"b_c": "x"})
        with self.assertRaises(CardError):
            ctx.store.insert("a", {"b_c": "X"})   # still unique, case-insensitive


if __name__ == "__main__":
    unittest.main()
