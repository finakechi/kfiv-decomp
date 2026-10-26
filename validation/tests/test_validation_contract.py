"""Regressions for F1/F2 from the 2026-10-25 MainPC review.

These check that an invalid validation run cannot be reported as a successful
mutation control, and that unsupported item-base expressions fail closed.
"""
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest
from unittest import mock

import test_key_items as subject


class ValidationContracts(unittest.TestCase):
    def behavior_case(self):
        case = subject.KeyItemBehavior("test_detects_wrong_reset_sentinel")
        case.source = subject.game_units()
        case.compiler = shlex.split(os.environ.get("CC", "cc"))
        return case

    def test_sanitizer_failure_after_valid_mutation_output_is_rejected(self):
        case = self.behavior_case()
        # Produce the real exit-time UBSan failure demonstrated by the review.
        case.compiler += ["-fsanitize=undefined", "-fno-sanitize-recover=all"]
        mutant = case.source.replace("s32 empty = -1;", "s32 empty = 0;", 1)
        mutant += r"""
#include <stdio.h>
__attribute__((destructor)) static void validation_exit_defect(void) {
    fflush(stdout);
    volatile int32_t value = INT32_MAX;
    value = value + 1;
}
"""
        run = case.compile_and_run(mutant)
        self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
        self.assertEqual(run.stdout, "differential cases=144000 mismatches=4000\n"
                                    "sequence cases=128000 mismatches=64000\n")
        self.assertIn("runtime error:", run.stderr)
        with mock.patch.object(case, "compile_and_run", return_value=run):
            with self.assertRaisesRegex(AssertionError, "stderr"):
                case.test_detects_wrong_reset_sentinel()

    def test_mutation_output_requires_exact_counts_and_two_lines(self):
        case = self.behavior_case()
        valid = "differential cases=144000 mismatches=4000\nsequence cases=128000 mismatches=64000\n"
        malformed = ("unexpected output\n" + valid, valid + "\n",
                     valid.replace("cases=144000", "cases=1"),
                     valid.replace("mismatches=4000", "mismatches=144001"))
        for output in malformed:
            with self.subTest(output=output):
                run = subprocess.CompletedProcess([], 1, output, "")
                with mock.patch.object(case, "compile_and_run", return_value=run):
                    with self.assertRaises(AssertionError):
                        case.test_detects_wrong_reset_sentinel()

    def test_item_base_expression_tails_fail_closed(self):
        # Exercise game_units through a real temporary header, not a replacement parser.
        with tempfile.TemporaryDirectory(prefix="kfiv-macro-contract-") as temporary:
            checkout = Path(temporary)
            menu = checkout / "src/game/ui/menu_screens.c"
            header = checkout / "src/game/item/item.h"
            menu.parent.mkdir(parents=True)
            header.parent.mkdir(parents=True)
            menu.write_text((subject.ROOT / "src/game/ui/menu_screens.c").read_text(),
                            encoding="utf-8")
            definitions = ("47 + 1", "47 /* comment */ + 1", "47 /* multi\nline */ + 1",
                           "47 " + chr(92) + "\n+ 1", "(47)", "047", "47U", "0x2f")
            for value in definitions:
                with self.subTest(value=value):
                    header.write_text("#define ITEM_KEY_FIRST " + value + "\n", encoding="utf-8")
                    with mock.patch.object(subject, "ROOT", checkout):
                        with self.assertRaisesRegex(ValueError, "ITEM_KEY_FIRST"):
                            subject.game_units()

    def test_item_base_literal_and_comments_are_preserved(self):
        with tempfile.TemporaryDirectory(prefix="kfiv-macro-contract-") as temporary:
            checkout = Path(temporary)
            menu = checkout / "src/game/ui/menu_screens.c"
            header = checkout / "src/game/item/item.h"
            menu.parent.mkdir(parents=True)
            header.parent.mkdir(parents=True)
            menu.write_text((subject.ROOT / "src/game/ui/menu_screens.c").read_text(),
                            encoding="utf-8")
            for value in ("47", "47 /* comment */", "47 // trailing comment"):
                with self.subTest(value=value):
                    header.write_text("#define ITEM_KEY_FIRST " + value + "\n", encoding="utf-8")
                    with mock.patch.object(subject, "ROOT", checkout):
                        self.assertIn("#define ITEM_KEY_FIRST 47\n", subject.game_units())


if __name__ == "__main__":
    unittest.main()
