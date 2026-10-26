"""Host differential checks of the current checkout's actual game functions.

Adapted from KF4AncientCity/tests/test_upstream_functional.py at
04d294f52fd0df96e13027e74933094d11dce1a2. No retail inputs or external checkout.
Temporary source mutations prove that the behavioral comparison detects errors.
"""
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
NAMES = ("Menu_ClearKeyItems", "Menu_AddKeyItem")
RESULTS = re.compile(r"differential cases=144000 mismatches=([0-9]+)\n"
                     r"sequence cases=128000 mismatches=([0-9]+)\n")
COMMENTS_AND_STRINGS = re.compile(
    r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', re.S
)


def extract_function(source, name):
    # Keep offsets stable while ignoring braces in comments and string literals.
    code = COMMENTS_AND_STRINGS.sub(
        lambda match: re.sub(r"[^\n]", " ", match.group()), source
    )
    definitions = list(re.finditer(
        rf"^[A-Za-z_][^\n;{{}}]*\b{re.escape(name)}\s*\([^)]*\)\s*\{{", code, re.M
    ))
    if len(definitions) != 1:
        raise ValueError(f"expected one definition of {name}, found {len(definitions)}")
    match = definitions[0]
    depth = 1
    for index in range(match.end(), len(code)):
        depth += {"{": 1, "}": -1}.get(code[index], 0)
        if depth == 0:
            return source[match.start():index + 1]
    raise ValueError(f"unterminated definition of {name}")


def game_units():
    menu = (ROOT / "src/game/ui/menu_screens.c").read_text(encoding="utf-8")
    item = (ROOT / "src/game/item/item.h").read_text(encoding="utf-8")
    # Only a complete unsuffixed decimal literal is supported by this shim.
    # Collapse block comments to whitespace so a tail after a multiline comment
    # cannot become a different preprocessor line and be silently discarded.
    item = re.sub(r"//[^\n]*|/\*.*?\*/", " ", item, flags=re.S)
    constants = re.findall(r"^[ \t]*#[ \t]*define[ \t]+ITEM_KEY_FIRST\b([^\n]*)$", item, re.M)
    if len(constants) != 1 or re.fullmatch(r"0|[1-9][0-9]*", constants[0].strip()) is None:
        raise ValueError("expected one complete decimal-literal ITEM_KEY_FIRST in item.h; "
                         "expressions, suffixes, octal and hexadecimal need a reviewed shim")
    bodies = "\n\n".join(extract_function(menu, name) for name in NAMES)
    return ("#include <stdint.h>\ntypedef int32_t s32;\n"
            f"#define ITEM_KEY_FIRST {constants[0].strip()}\n"
            "s32 key_item_slots[12];\n" + bodies + "\n")


class KeyItemBehavior(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compiler = shlex.split(os.environ.get("CC", "cc"))
        if not cls.compiler or shutil.which(cls.compiler[0]) is None:
            raise RuntimeError("a host C compiler is required (set CC); checks were not run")
        cls.source = game_units()

    def compile_and_run(self, source):
        with tempfile.TemporaryDirectory(prefix="kfiv-key-items-") as temporary:
            directory = Path(temporary)
            unit = directory / "game_units.c"
            unit.write_text(source, encoding="utf-8")
            executable = directory / "key_items"
            command = self.compiler + ["-std=c11", "-O1", "-g", "-Wall", "-Wextra", "-Werror"]
            if os.environ.get("KFIV_VALIDATION_SANITIZERS") == "1":
                command += ["-fsanitize=address,undefined", "-fno-sanitize-recover=all",
                            "-fno-omit-frame-pointer"]
            command += [f"-I{ROOT / 'validation/models'}", str(unit),
                        str(ROOT / "validation/key_item_harness.c"),
                        str(ROOT / "validation/models/key_items.c"), "-o", str(executable)]
            build = subprocess.run(command, capture_output=True, text=True, timeout=60)
            self.assertEqual(build.returncode, 0, shlex.join(command) + "\n" + build.stderr)
            return subprocess.run([str(executable)], capture_output=True, text=True, timeout=30)

    def test_actual_reset_and_insert_agree_with_independent_models(self):
        run = self.compile_and_run(self.source)
        self.assert_harness_result(run, expected_returncode=0)
        print(run.stdout, end="")

    def assert_harness_result(self, run, expected_returncode):
        details = f"stdout:\n{run.stdout}\nstderr:\n{run.stderr}"
        # This deterministic harness has no expected runtime stderr. In particular,
        # an exit-time sanitizer error must not count as a successful mutant.
        self.assertEqual(run.stderr, "", "unexpected runtime stderr\n" + details)
        self.assertEqual(run.returncode, expected_returncode, details)
        result = RESULTS.fullmatch(run.stdout)
        self.assertIsNotNone(result, "invalid harness result/count contract\n" + details)
        mismatches = tuple(map(int, result.groups()))
        for count, maximum in zip(mismatches, (144000, 128000)):
            self.assertLessEqual(count, maximum, details)
        if expected_returncode == 0:
            self.assertEqual(sum(mismatches), 0, details)
        else:
            self.assertGreater(sum(mismatches), 0, details)

    def assert_mutation_detected(self, original, replacement):
        self.assertEqual(self.source.count(original), 1,
                         f"mutation anchor changed: {original!r}; review the control")
        run = self.compile_and_run(self.source.replace(original, replacement, 1))
        self.assert_harness_result(run, expected_returncode=1)

    def test_detects_wrong_reset_sentinel(self):
        self.assert_mutation_detected("s32 empty = -1;", "s32 empty = 0;")

    def test_detects_wrong_dispatch_value(self):
        self.assert_mutation_detected("key_item_slots[slot] = 0;", "key_item_slots[slot] = 12;")

    def test_detects_only_minus_one_treated_as_empty(self):
        self.assert_mutation_detected("key_item_slots[slot] < 0", "key_item_slots[slot] == -1")


if __name__ == "__main__":
    unittest.main()
