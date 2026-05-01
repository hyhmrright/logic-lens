"""
Unit tests for scripts/grade-iteration.py.

Run with:  python3 -m unittest discover tests/
Or:        python3 tests/test_grader.py
"""

from __future__ import annotations
import importlib.util
import tempfile
import unittest
from pathlib import Path

# Python identifiers cannot contain hyphens, so importlib is required here.
_SCRIPT = Path(__file__).parent.parent / "scripts" / "grade-iteration.py"
_spec = importlib.util.spec_from_file_location("grade_iteration", _SCRIPT)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

count_chinese = _mod.count_chinese
is_chinese_output = _mod.is_chinese_output
check = _mod.check
grade_case = _mod.grade_case
_case200_await_boundary = _mod._case200_await_boundary
_case201_multiple_leak_paths = _mod._case201_multiple_leak_paths
_case204_not_ready_leak = _mod._case204_not_ready_leak
_case208_both_skip_paths = _mod._case208_both_skip_paths
_CASE_EXTRA_RULES = _mod._CASE_EXTRA_RULES
EVALS_BY_ID = _mod.EVALS_BY_ID


class TestCountChinese(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(count_chinese(""), 0)

    def test_ascii_only(self):
        self.assertEqual(count_chinese("hello world"), 0)

    def test_cjk_chars(self):
        self.assertEqual(count_chinese("你好世界"), 4)

    def test_mixed(self):
        self.assertEqual(count_chinese("hello 你好 world"), 2)


class TestIsChineseOutput(unittest.TestCase):
    def test_empty_is_not_chinese(self):
        self.assertFalse(is_chinese_output(""))

    def test_few_cjk_is_not_chinese(self):
        self.assertFalse(is_chinese_output("你好" * 10))  # 20 chars, below 50

    def test_sufficient_cjk_is_chinese(self):
        self.assertTrue(is_chinese_output("你好世界" * 15))  # 60 chars

    def test_english_findings_header_disqualifies(self):
        text = "你好世界" * 15 + "\n## Findings\n"
        self.assertFalse(is_chinese_output(text))

    def test_english_summary_header_disqualifies(self):
        text = "你好世界" * 15 + "\n# Summary\n"
        self.assertFalse(is_chinese_output(text))

    def test_inline_english_does_not_disqualify(self):
        # English words mid-line do not count as section headers
        text = "你好世界" * 15 + "\nSome inline Findings text here"
        self.assertTrue(is_chinese_output(text))

    def test_double_hash_scope_does_not_disqualify(self):
        # ## Scope was NOT in the original bad_headers list; must not disqualify
        text = "你好世界" * 15 + "\n## Scope\n"
        self.assertTrue(is_chinese_output(text))

    def test_double_hash_mode_does_not_disqualify(self):
        # ## Mode was NOT in the original bad_headers list; must not disqualify
        text = "你好世界" * 15 + "\n## Mode\n"
        self.assertTrue(is_chinese_output(text))

    def test_single_hash_scope_disqualifies(self):
        # # Scope WAS in the original bad_headers list
        text = "你好世界" * 15 + "\n# Scope\n"
        self.assertFalse(is_chinese_output(text))


class TestCheck(unittest.TestCase):
    def test_all_pass(self):
        rules = [("has hello", lambda t: "hello" in t)]
        result = check("hello world", rules)
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0]["passed"])

    def test_all_fail(self):
        rules = [("has goodbye", lambda t: "goodbye" in t)]
        result = check("hello world", rules)
        self.assertFalse(result[0]["passed"])

    def test_predicate_exception_marks_failed(self):
        def boom(t):
            raise ValueError("oops")
        result = check("text", [("boom rule", boom)])
        self.assertFalse(result[0]["passed"])
        self.assertIn("grader error", result[0]["text"])

    def test_multiple_rules(self):
        rules = [
            ("has L1", lambda t: "L1" in t),
            ("has L2", lambda t: "L2" in t),
        ]
        result = check("L1 only", rules)
        self.assertTrue(result[0]["passed"])
        self.assertFalse(result[1]["passed"])


class TestGradeCaseEdgeCases(unittest.TestCase):
    def test_unknown_case_id(self):
        result = grade_case(99999, Path("/nonexistent/output.md"))
        self.assertIn("error", result)
        self.assertEqual(result["eval_id"], 99999)

    def test_missing_output_file(self):
        # Pick any known case id
        known_id = next(iter(EVALS_BY_ID))
        result = grade_case(known_id, Path("/nonexistent/output.md"))
        self.assertIn("error", result)
        self.assertEqual(result["pass_rate"], 0.0)

    def test_grade_case_with_output(self):
        # Case 1 requires 'L1' and 'formatted' in the output
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "output.md"
            output.write_text(
                "Premises: ...\nTrace: ...\nDivergence: ...\n"
                "L1 risk: module-level format shadows builtin. "
                "The (formatted) suffix shows up in the output.",
                encoding="utf-8"
            )
            result = grade_case(1, output)
            self.assertIn("pass_rate", result)
            self.assertGreater(result["pass_rate"], 0.0)

    def test_grade_case_explain_mode_skips_four_field(self):
        # logic-explain mode should not require four-field labels
        explain_cases = [cid for cid, c in EVALS_BY_ID.items() if c["mode"] == "logic-explain"]
        if not explain_cases:
            self.skipTest("no logic-explain cases in evals-v2.json")
        cid = explain_cases[0]
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "output.md"
            output.write_text("Some explanation without Premises/Trace/Divergence labels.",
                               encoding="utf-8")
            result = grade_case(cid, output)
            # Verify no four-field rule was checked
            four_field_texts = [e["text"] for e in result["expectations"]
                                if "Premises" in e["text"]]
            self.assertEqual(four_field_texts, [])


class TestHelperPredicates(unittest.TestCase):
    def test_case200_await_boundary_pass(self):
        text = "The function awaits a coroutine; the event loop interleaves other tasks."
        self.assertTrue(_case200_await_boundary(text))

    def test_case200_await_boundary_needs_both(self):
        self.assertFalse(_case200_await_boundary("uses await only"))
        self.assertFalse(_case200_await_boundary("event loop only"))

    def test_case201_multiple_leak_paths_pass(self):
        text = "empty data path and UploadError exception handler both never close the file handle"
        self.assertTrue(_case201_multiple_leak_paths(text))

    def test_case201_needs_two_paths_and_release(self):
        self.assertFalse(_case201_multiple_leak_paths("empty data only, no release"))

    def test_case204_not_ready_leak_pass(self):
        text = "if not job.is_ready() returns early without calling pool.release"
        self.assertTrue(_case204_not_ready_leak(text))

    def test_case204_needs_both_anchor_and_release(self):
        self.assertFalse(_case204_not_ready_leak("is_ready() mentioned but no pool cleanup"))
        self.assertFalse(_case204_not_ready_leak("pool.release mentioned but no ready check"))

    def test_case208_both_skip_paths_pass(self):
        text = ("unauthorized return 401 skips audit_log.record; "
                "malformed BadRequest also skips the audit log")
        self.assertTrue(_case208_both_skip_paths(text))

    def test_case208_needs_all_three_elements(self):
        self.assertFalse(_case208_both_skip_paths("unauthorized and malformed only"))


class TestCaseRulesCompleteness(unittest.TestCase):
    """Verify _CASE_EXTRA_RULES entries are well-formed (no empty rule lists)."""

    def test_all_entries_have_rules(self):
        for case_id, rules in _CASE_EXTRA_RULES.items():
            self.assertGreater(len(rules), 0, f"case {case_id} has empty rules list")

    def test_all_rule_tuples_have_two_elements(self):
        for case_id, rules in _CASE_EXTRA_RULES.items():
            for i, rule in enumerate(rules):
                self.assertEqual(len(rule), 2,
                                 f"case {case_id} rule[{i}] is not a 2-tuple")

    def test_all_predicates_are_callable(self):
        for case_id, rules in _CASE_EXTRA_RULES.items():
            for i, (desc, pred) in enumerate(rules):
                self.assertTrue(callable(pred),
                                f"case {case_id} rule[{i}] predicate is not callable")

    def test_all_predicates_accept_string(self):
        for case_id, rules in _CASE_EXTRA_RULES.items():
            for desc, pred in rules:
                try:
                    pred("")  # must not raise on empty string
                except Exception as e:
                    self.fail(f"case {case_id} predicate '{desc}' raised on empty string: {e}")


if __name__ == "__main__":
    unittest.main()
