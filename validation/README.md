# Independent behavioral validation

Run from this checkout, with Python 3.10+ and a host C compiler:

```sh
python3 -I -m unittest discover -s validation/tests -v
env CC=gcc KFIV_VALIDATION_SANITIZERS=1 python3 -I -m unittest discover -s validation/tests -v
```

The tests require no disc, extracted files, SDK, period compiler, Ghidra, network
or second checkout. `CC` selects the compiler (default `cc`). A missing compiler,
changed extraction contract or compile failure fails the checks instead of
reporting a successful skip. Temporary files are removed after each test.

## What is compared

The test reads `Menu_ClearKeyItems` and `Menu_AddKeyItem` directly from the current
`src/game/ui/menu_screens.c`, and `ITEM_KEY_FIRST` from `src/game/item/item.h`.
It compiles those original function bodies with a minimal shim: `s32` is
`int32_t`, and the twelve-slot global is host memory. No stored copy of the game
functions is tested. New dependencies or signatures require reviewing the shim.
The item-base definition must be exactly one unsuffixed decimal literal after
comment removal. Expressions, continuations, suffixes, octal and hexadecimal
definitions fail closed; they require reviewing the shim instead of truncating
a numeric prefix.

The independent C reference models retain the C15/C16 reset and insertion logic:
reset twelve words to -1; insert the mapped value for IDs 47..59 into the first
negative slot; leave the list unchanged for ID 54, other IDs or a full list.
Model null-pointer checks are host-only guards. They are not retail behavior and
are outside the game-vs-model comparison, which supplies valid twelve-word arrays.

Each unmodified run compares:

- 144,000 independent cases: 4,000 initial states × 36 operations, including full
  prefixes, arbitrary negative slots, boundary IDs, extreme signed inputs and reset.
- 128,000 operations in 4,000 sequences, retaining state across insertions and reset,
  including an `INT32_MIN` empty slot.

Three controls modify temporary copies of the actual game functions: a wrong reset
sentinel, a wrong dispatch value, and treating only -1 as empty. Each must produce
a measured disagreement and exit 1, with empty runtime stderr and exactly the two
expected result lines/counts. A crash, sanitizer diagnostic, extra output or
impossible mismatch count is a failed control. The diagnostic output is retained
in the assertion failure.
The checkout's game source is never modified by these tests.

## Provenance and scope

Adapted with the owner's authorization from
[KF4AncientCity at `04d294f`](https://github.com/finakechi/KF4AncientCity/tree/04d294f52fd0df96e13027e74933094d11dce1a2):

| File here | Original source |
|---|---|
| `models/key_items.c` insertion | [`kf_effect_1dc120`](https://github.com/finakechi/KF4AncientCity/blob/04d294f52fd0df96e13027e74933094d11dce1a2/src/common_item_effects/kf_common_item_effects.c) |
| `models/key_items.c` reset | [`kf_list_reset`](https://github.com/finakechi/KF4AncientCity/blob/04d294f52fd0df96e13027e74933094d11dce1a2/src/common_item_effects/kf_common_item_list.c) |
| Harness and Python comparison | [`test_upstream_functional.py`](https://github.com/finakechi/KF4AncientCity/blob/04d294f52fd0df96e13027e74933094d11dce1a2/tests/test_upstream_functional.py) |

Only the two model bodies were retained, with renamed functions/slot macro and
a minimal header; unrelated parameter, message and rendering models were omitted.
The original 144,000-case harness was adapted to the local checkout and extended
with sequences and three mutation controls. Models keep their instruction-derived
dispatch table instead of deriving expectations from the fork's switch statement.
Evidence remains in
[C15](https://github.com/finakechi/KF4AncientCity/blob/04d294f52fd0df96e13027e74933094d11dce1a2/evidence/2026-10-24-common-item-effects.md),
[C16](https://github.com/finakechi/KF4AncientCity/blob/04d294f52fd0df96e13027e74933094d11dce1a2/evidence/2026-10-24-list-lifecycle.md)
and [C17](https://github.com/finakechi/KF4AncientCity/blob/04d294f52fd0df96e13027e74933094d11dce1a2/evidence/2026-10-24-c17-upstream-correspondence.md).
The inherited repository licence and upstream attribution remain in place.

These are synthetic host checks of final array states for two functions. They do
not observe individual memory-write order, PS2 execution, rendering, saving,
complete translation units, byte matching or a PC port. The upstream name "key
items" identifies source symbols; it adds no independently verified gameplay meaning.
Nothing under `validation/` enters the matching build's `src/game`/`src/sce` scan.

## Save and restore copy slices — 2026-10-26

The additional `test_key_item_save.py` checks two **bounded statements**
in the merged game's actual `src/game/core/game.c`, not copied versions of
its whole functions:

- `Game_WriteSaveImage`: copy 48 bytes from the twelve `key_item_slots`
  into the current `save_cursor`, then advance the cursor by 48.
- `Game_ReadSaveImage`: copy the same 48 bytes in the opposite direction,
  then advance the cursor by 48.

The extractor finds the complete game function definitions and requires
**exactly one** supported two-statement copy window in each. Missing or
duplicate windows fail rather than silently testing a substitute. It
compiles those exact source statements into a minimal host wrapper.
If the game changes to a different expression or adds relevant effects,
the extractor and model must be reviewed rather than broadening an
unchecked source parser.

The reference models in `models/key_item_save.c` are adapted from
[KF4AncientCity C16's instruction-derived pack/unpack functions](https://github.com/finakechi/KF4AncientCity/blob/04d294f52fd0df96e13027e74933094d11dce1a2/src/common_item_effects/kf_common_item_list.c).
They calculate twelve little-endian 32-bit values independently of the
fork's `memcpy` statements. The 4,096 save and 4,096 restore comparisons
include all-empty slots, signed extremes, sequential values and seeded
random bit patterns. Tests check bytes, the 48-byte cursor movement,
unchanged sources and untouched 16-byte buffer tails. Four separate
temporary mutations shorten a copy or an advance and must produce
real mismatches with the exact two-line output contract. Two additional
extractor tests reject missing/duplicate source sites. The original
eight reset/insertion validation tests remain independent.

**Limits:** the harness explicitly requires a little-endian host, like
the EE target. It tests final effects of the actual **two copy windows
only**; it does not run the enclosing game functions, infer the offset
of the fields within the full save, validate header/checksum logic or
exercise a memory card, emulator or retail gameplay. Host safeguards
and buffer ownership are not assertions about the PS2 implementation.
No commercial images, ELF, SDK or Ghidra access are needed. Matching
source and build inputs remain unchanged.

## Sanitizers and CI

CI runs GCC and Clang, with and without address/undefined-behavior sanitizers.
Leak detection is enabled in the CI environment. On a traced host where
LeakSanitizer reports that it cannot run, the explicit workaround is:

```sh
env CC=gcc KFIV_VALIDATION_SANITIZERS=1 ASAN_OPTIONS=detect_leaks=0 python3 -I -m unittest discover -s validation/tests -v
```

Report that leak checking did not run whenever using that workaround. The tests
preserve caller sanitizer options and never disable leaks automatically.

## First transfer verification — 2026-10-24

Cloud host: Python 3.12.14 and GCC 13.3.0. Four tests pass normally: the unmodified
272,000 state comparisons agree, and all three deliberate errors are detected.
The initial sanitizer run was blocked by LeakSanitizer under tracing. All four
tests then passed under ASan/UBSan with the documented leak-disabled workaround;
leak checks did not run. Clang is absent on this host; CI supplies that coverage.

The matching game source, headers, build scripts and symbol map are unchanged from
`09adc15974b2936b09943d2a55cc29fa472a79b2`. A retail rebuild was not run here because
commercial inputs and the MainPC toolchain are unavailable. The prior successful
build at that source revision is documented in
[C18](https://github.com/finakechi/KF4AncientCity/blob/04d294f52fd0df96e13027e74933094d11dce1a2/evidence/2026-10-24-c18-upstream-build-reproduction.md).
Before claiming the complete fork milestone, run `./build.sh` on MainPC against
verified read-only media and record its output. Detailed project progress remains
in KF4AncientCity's master handoff.

## Review corrections — 2026-10-25

The MainPC review of `2e90eca` reproduced two gaps: exit-time sanitizer errors
could satisfy the mutation assertion, and macro expressions could be truncated to
a decimal prefix. The fixes reject runtime stderr, enforce exact output/count
contracts and require a complete supported macro literal. Four new regression
tests supplement the original four behavioral tests. One compiles the review's
real exit-time signed-overflow specimen and proves its UBSan diagnostic is rejected
despite valid mismatch output. The macro regressions exercise temporary headers.
The new regressions failed against the reviewed implementation before the fixes.

The unmodified game comparisons remain 144,000 independent cases plus 128,000
stateful operations; added contract regressions are not extra game-behavior cases.
Cloud GCC 13.3.0/Python 3.12.14 passes all eight tests normally and under ASan/UBSan
with `ASAN_OPTIONS=detect_leaks=0`; local leak checks did not run. Clang coverage
is supplied by CI, rather than claimed as a cloud-local run.

The supplied MainPC report separately records a failed fresh build: the existing
period compiler/assembler received SIGSYS through that execution route and no
fresh linked ROM was produced. Its comparison of the existing C18 ROM with retail
is historical output validation. These test fixes do not resolve that execution
blocker or establish a fresh retail rebuild. No matching source/build input changes
are needed for these corrections.
