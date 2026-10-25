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
a measured disagreement and exit 1. A crash or missing output is a failed control.
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
