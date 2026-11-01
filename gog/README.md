# cyberpunk-gog-port

Notes and tools for running [codeman101/RED4ext-macos](https://github.com/codeman101/RED4ext-macos) on the **GOG native macOS build** of Cyberpunk 2077 2.5.0 (LC_UUID `1DFA005C-ED12-306F-B349-67BE555F2F72`, image base `0x100000000`).

Discussion and candidate tables: https://github.com/codeman101/RED4ext-macos/issues/1

## Status (unverified against the official address DB)
- RED4ext core: 21 GOG candidates, all startup self-checks pass in a debug copy under lldb.
- TweakXL: runs (TweakDB loads, 196423 records) once its own tables are patched: 21 embedded copies of the 79-entry address table, `InitializeAddressTable` immediates, and the memory-vault expected-offset table (4 pools x 5 allocator slots).
- Not done: TweakXL StatService hook cluster, 5 ArchiveXL hook targets, Codeware.
- Tested only on a debug copy launched from lldb, not through the normal launcher.

## Layout
- `notes/gog_candidates.tsv`: hash, name, Steam 2.5 offset, GOG candidate, confidence.
- `tools/`: static analysis scripts (`python3 -I`). `shape3.py` = shape-based function matcher.
- `dbg/`: `setup.sh` makes a debuggable copy outside the .app; `crash.py` / `trace.py` are lldb commands.
- `probe/`: read-only `DYLD_INSERT_LIBRARIES` probes (edit the log path first).

## Not included
No game binary, no patched plugin dylibs, no saves. Bring your own game and plugins; patch locally.
