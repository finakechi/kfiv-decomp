# Assistant instructions — finakechi/kfiv-decomp

Read [CONTRIBUTING.md](CONTRIBUTING.md), the relevant source and
[validation/README.md](validation/README.md) before substantial work.
This fork is the matching game-source and build workspace. Preserve the inherited
matching implementation and attribution; inspect existing source before redoing
reverse engineering.

## Repository responsibilities

- This fork owns matching game code, build changes and its behavioral CI.
- [KF4AncientCity](https://github.com/finakechi/KF4AncientCity/blob/main/MASTER_HANDOFF.md)
  owns independent evidence, original models, provenance and detailed game-project
  progress. Update its master and starting guide together after milestones; link
  there instead of creating another canonical progress handoff in this fork.
- [PS2DInfo](https://github.com/finakechi/PS2DInfo/blob/main/START_HERE.md)
  owns shared PS2 tools, integrations and reusable workflows.

## Before changing anything

Inspect effective GIT_DIR/GIT_WORK_TREE, HEAD, branch, upstream, worktrees and
dirty changes. Preserve existing work and original media. Use reviewable branches
and PRs; commit, push and merge are separate actions. Do not force-push or merge
without specific authority. Repository access does not establish MainPC, Ghidra,
emulator or another client's MCP access.

The target is the USA `SLUS_203.18`, SHA-256
`3f826468322ada9fda0db8529213e97801a1c71b4e801078bdb7a0b58dab7c18`.
Verify inputs before applying addresses. Identical ELF hashes do not establish
identical disc revisions. Use the configured input checker documented in
[KF4AncientCity's development guide](https://github.com/finakechi/KF4AncientCity/blob/main/DEVELOPMENT.md#local-inputs-machine-specific-paths);
keep machine paths outside Git. Never commit discs, executables, extracted assets,
secrets or local Ghidra databases. Keep originals read-only; do not convert a CHD
when a verified ISO works. MainPC commands must be fish-compatible when relevant.

## Implementation and verification

- `src/game/` and `src/sce/` enter the period-toolchain build automatically.
  Host reference models belong in `validation/models/`; they must not replace
  matching game functions.
- Keep models independent: cite the original evidence and any adaptation.
  Upstream game names are candidate interpretations until independently supported.
  Check widths, signedness, delay slots, side effects and callers against evidence.
- Run behavioral tests and the existing readability/symbol checks. Matching-source,
  compiler or build changes also require `./build.sh` with lawful local inputs.
  If those inputs are unavailable, report that the retail rebuild was not run;
  passing host tests does not substitute for it.
- Keep static checks, synthetic host behavior, retail-data checks, runtime gameplay
  and measured matching distinct. The C18 byte-identical ROM result is historical
  evidence for its pinned revision, not a full-ELF match or a current gameplay run.
- Do not silently skip missing compilers or hide sanitizer failures. If tracing
  blocks LeakSanitizer, use `ASAN_OPTIONS=detect_leaks=0` only for that environment
  and explicitly report that leak checks did not run.
- Preserve existing licence notices. Do not expand or redistribute SDK/runtime
  material while the third-party provenance questions in C17 remain unresolved.
  No SDK source needs to be copied for the host validation workflow.

Report changes, actual commands/results/skips, evidence limits, exact branch/commit
and integration state. Continue authorized safe work without routine checkpoints.
