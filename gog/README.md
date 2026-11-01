# cyberpunk-gog-port

Notes and tools for running [codeman101/RED4ext-macos](https://github.com/codeman101/RED4ext-macos) on the **GOG native macOS build** of Cyberpunk 2077 2.5.0 (LC_UUID `1DFA005C-ED12-306F-B349-67BE555F2F72`, image base `0x100000000`).

Discussion and candidate tables: https://github.com/codeman101/RED4ext-macos/issues/1

## Status (unverified against the official address DB)
- RED4ext core: 21 GOG candidates, all startup self-checks pass in a debug copy under lldb.
- TweakXL: runs (TweakDB loads, 196423 records) once its own tables are patched: 21 embedded copies of the 79-entry address table, `InitializeAddressTable` immediates, and the memory-vault expected-offset table (4 pools x 5 allocator slots).
- ArchiveXL (`tools/patch_archivexl.py`): loads without crashing next to TweakXL in the debug copy. Patched: table entries matched by Steam offset (ArchiveXL lists some functions under extra hashes), the `TweakDB_Load` hook, `CBaseEngine_LoadGatheredResources` (candidate `1:0x3C4FA84`) and its own memory-vault table (35 slots, incl. PoolEngine/PoolRefCount/PoolDefault at Steam-0x20).
- ResourceDepot (hash 1704595399): GOG `0x934F518`. Found through the "Resource depot not initialized" assert string: its caller uses getter `0x41ece58` (`adrp; ldr; ret`, setter right after, 67 callers). Checked at runtime in the debug copy: the global holds an object with a binary vtable, a heap array at `+0x10` and 4 entries at `+0x1c` once the game is up. It is null early in boot, so a hook that fires before the depot exists crashes in `ExtensionLoader::Configure()`.
- ArchiveXL hook 2923109755: three early-boot functions (`0x143766c`, `0x143bfa0`, `0x146f6bc`) make the detour fire, but too early (depot still null), so they are not the target. Tested with `dbg/hit.py` (breakpoint on the detour, no log needed).
- Not done: TweakXL StatService hook cluster; 3 ArchiveXL hooks (hashes 2885423437 and 2923109755, `gameIGameSystem_Spawn*`) still fail with `Detour error -2`, so those features stay off; Codeware.
- `ResourcePath_Create*` candidate `1:0x416DDE0`: exactly 107 insns (same as Steam), leaf FNV-1a 64 that strips leading quotes and slashes, 220 caller functions. Found with `tools/fnvleaf.py`. The hook attaches and the game keeps running; not checked that ArchiveXL's path mapping actually works.
- `LoadGatheredResources` candidate `1:0x3C4FA84`: virtual call `[vtbl+0x100]`, then a `bool` check whose failure path calls a helper (`0x3C530B4`) holding the "Not all Gathered Resources were loaded!" assert; the only caller function is `0x3C4EE94`. Found with `tools/callers.py`. Static only, not confirmed at runtime.
- Tested only on a debug copy launched from lldb, not through the normal launcher.

## Layout
- `notes/gog_candidates.tsv`: hash, name, Steam 2.5 offset, GOG candidate, confidence.
- `tools/`: static analysis scripts (`python3 -I`). `tools/patch_tweakxl.py` patches an original TweakXL 0.2.0 dylib for GOG (sha256-checked, re-signs ad hoc). `shape3.py` = shape-based function matcher.
- `dbg/`: `setup.sh` makes a debuggable copy outside the .app; `crash.py` / `trace.py` are lldb commands.
- `probe/`: read-only `DYLD_INSERT_LIBRARIES` probes (edit the log path first).

## Not included
No game binary, no patched plugin dylibs, no saves. Bring your own game and plugins; patch locally.
