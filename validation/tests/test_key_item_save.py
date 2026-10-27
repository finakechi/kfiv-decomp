"""Host test of actual key-item copy slices within game save/load functions.

The expected bytes come from independently researched KF4AncientCity C16
models. This deliberately does not test complete functions, memory-card I/O,
save-file checksums or execution on a PS2.
"""
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tempfile
import unittest

from test_key_items import COMMENTS_AND_STRINGS, extract_function, ROOT

SOURCE_PATH = ROOT / "src/game/core/game.c"
NAMES = ("Game_WriteSaveImage", "Game_ReadSaveImage")
WINDOWS = (
    re.compile(
        r"\bmemcpy\s*\(\s*save_cursor\s*,\s*key_item_slots\s*,\s*0x30\s*\)\s*;"
        r"\s*save_cursor\s*\+=\s*0x30\s*;"
    ),
    re.compile(
        r"\bmemcpy\s*\(\s*key_item_slots\s*,\s*save_cursor\s*,\s*0x30\s*\)\s*;"
        r"\s*save_cursor\s*\+=\s*0x30\s*;"
    ),
)
RESULT = re.compile(
    r"save cases=4096 mismatches=([0-9]+)\n"
    r"restore cases=4096 mismatches=([0-9]+)\n"
)


def game_copy_units(source):
    """Extract exactly one reviewed copy-and-advance site per actual function.

    Source or syntax changes fail closed instead of silently validating a
    hand-written substitute. Only these two consecutive statements are run
    under a host shim, not the surrounding save/load functions.
    """
    windows = []
    for name, pattern in zip(NAMES, WINDOWS):
        body = extract_function(source, name)
        # Keep positions unchanged while excluding comments and string literals.
        visible = COMMENTS_AND_STRINGS.sub(
            lambda match: re.sub(r"[^\n]", " ", match.group()), body
        )
        matches = list(pattern.finditer(visible))
        if len(matches) != 1:
            raise ValueError(f"{name}: expected one 48-byte copy-and-advance window, "
                             f"found {len(matches)}")
        match = matches[0]
        windows.append(body[match.start():match.end()])
    return (
        "#include <stddef.h>\n#include <stdint.h>\n#include <string.h>\n"
        "int32_t key_item_slots[12];\n"
        "size_t kfiv_game_pack_slice(uint8_t *base) {\n"
        "    uint8_t *save_cursor = base;\n    " + windows[0] + "\n"
        "    return (size_t)(save_cursor - base);\n}\n"
        "size_t kfiv_game_unpack_slice(uint8_t *base) {\n"
        "    uint8_t *save_cursor = base;\n    " + windows[1] + "\n"
        "    return (size_t)(save_cursor - base);\n}\n"
    )


class SaveLoadCopyBehavior(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compiler = shlex.split(os.environ.get("CC", "cc"))
        if not cls.compiler or shutil.which(cls.compiler[0]) is None:
            raise RuntimeError("host compiler required (set CC)")
        cls.source = SOURCE_PATH.read_text(encoding="utf-8")
        cls.units = game_copy_units(cls.source)

    def compile_and_run(self, units):
        with tempfile.TemporaryDirectory(prefix="kfiv-save-copy-") as temp:
            tmp = Path(temp)
            file = tmp / "copy_units.c"
            file.write_text(units, encoding="utf-8")
            exe = tmp / "check"
            cmd = self.compiler + ["-std=c11", "-O1", "-g",
                                   "-Wall", "-Wextra", "-Werror"]
            if os.environ.get("KFIV_VALIDATION_SANITIZERS") == "1":
                cmd += ["-fsanitize=address,undefined",
                        "-fno-sanitize-recover=all", "-fno-omit-frame-pointer"]
            cmd += ["-I" + str(ROOT / "validation/models"),
                    str(file),
                    str(ROOT / "validation/key_item_save_harness.c"),
                    str(ROOT / "validation/models/key_item_save.c"),
                    "-o", str(exe)]
            built = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            self.assertEqual(built.returncode, 0, shlex.join(cmd) + "\n" + built.stderr)
            return subprocess.run([str(exe)], capture_output=True, text=True,
                                  timeout=30)

    def check_result(self, run, expected_exit):
        diagnostic = f"stdout:\n{run.stdout}\nstderr:\n{run.stderr}"
        self.assertEqual(run.stderr, "", "unexpected runtime stderr\n" + diagnostic)
        self.assertEqual(run.returncode, expected_exit, diagnostic)
        match = RESULT.fullmatch(run.stdout)
        self.assertIsNotNone(match, "invalid result/count contract\n" + diagnostic)
        mismatches = tuple(map(int, match.groups()))
        self.assertTrue(all(count <= 4096 for count in mismatches), diagnostic)
        if expected_exit == 0:
            self.assertEqual(mismatches, (0, 0), diagnostic)
        else:
            self.assertGreater(sum(mismatches), 0, diagnostic)

    def assert_mutation_detected(self, original, changed):
        self.assertEqual(self.units.count(original), 1,
                         "mutation anchor changed; revise this test")
        run = self.compile_and_run(self.units.replace(original, changed, 1))
        self.check_result(run, expected_exit=1)

    def test_real_save_and_restore_copy_slices_match_c16(self):
        run = self.compile_and_run(self.units)
        self.check_result(run, expected_exit=0)
        print(run.stdout, end="")

    def test_detects_short_save_copy(self):
        self.assert_mutation_detected(
            "memcpy(save_cursor, key_item_slots, 0x30);",
            "memcpy(save_cursor, key_item_slots, 0x2C);"
        )

    def test_detects_short_restore_copy(self):
        self.assert_mutation_detected(
            "memcpy(key_item_slots, save_cursor, 0x30);",
            "memcpy(key_item_slots, save_cursor, 0x2C);"
        )

    def test_detects_wrong_save_cursor_advance(self):
        # There are two cursor advances: patch only the pack function.
        self.assert_mutation_detected(
            "memcpy(save_cursor, key_item_slots, 0x30); save_cursor += 0x30;",
            "memcpy(save_cursor, key_item_slots, 0x30); save_cursor += 0x2C;"
        )

    def test_detects_wrong_restore_cursor_advance(self):
        self.assert_mutation_detected(
            "memcpy(key_item_slots, save_cursor, 0x30); save_cursor += 0x30;",
            "memcpy(key_item_slots, save_cursor, 0x30); save_cursor += 0x2C;"
        )

    def test_extract_rejects_missing_copy_window(self):
        anchor = "memcpy(save_cursor, key_item_slots, 0x30); save_cursor += 0x30;"
        self.assertEqual(self.source.count(anchor), 1)
        changed = self.source.replace(
            anchor, "memcpy(save_cursor, key_item_slots, 0x2C); save_cursor += 0x30;", 1
        )
        with self.assertRaisesRegex(ValueError, "Game_WriteSaveImage"):
            game_copy_units(changed)

    def test_extract_rejects_duplicate_copy_window(self):
        anchor = "memcpy(key_item_slots, save_cursor, 0x30); save_cursor += 0x30;"
        self.assertEqual(self.source.count(anchor), 1)
        with self.assertRaisesRegex(ValueError, "found 2"):
            game_copy_units(self.source.replace(anchor, anchor + "\n" + anchor, 1))


    def test_extract_rejects_commented_out_live_copy(self):
        anchor = "memcpy(save_cursor, key_item_slots, 0x30); save_cursor += 0x30;"
        self.assertEqual(self.source.count(anchor), 1)
        changed = self.source.replace(anchor, "/* " + anchor + " */", 1)
        with self.assertRaisesRegex(ValueError, "Game_WriteSaveImage"):
            game_copy_units(changed)

    def test_extract_ignores_extra_commented_copy(self):
        anchor = "memcpy(key_item_slots, save_cursor, 0x30); save_cursor += 0x30;"
        self.assertEqual(self.source.count(anchor), 1)
        changed = self.source.replace(anchor, "/* " + anchor + " */\n" + anchor, 1)
        self.assertEqual(game_copy_units(changed), self.units)

    def test_extract_ignores_extra_string_literal_copy(self):
        anchor = "memcpy(key_item_slots, save_cursor, 0x30); save_cursor += 0x30;"
        self.assertEqual(self.source.count(anchor), 1)
        changed = self.source.replace(anchor, '"' + anchor + '"\n' + anchor, 1)
        self.assertEqual(game_copy_units(changed), self.units)

if __name__ == "__main__":
    unittest.main()
