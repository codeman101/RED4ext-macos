# cyberpunk-gog-port

Notes and tools for running [codeman101/RED4ext-macos](https://github.com/codeman101/RED4ext-macos) on the **GOG native macOS build** of Cyberpunk 2077 2.5.0 (LC_UUID `1DFA005C-ED12-306F-B349-67BE555F2F72`, image base `0x100000000`).

Discussion and candidate tables: https://github.com/codeman101/RED4ext-macos/issues/1

## Status (unverified against the official address DB)
- RED4ext core: 21 GOG candidates, all startup self-checks pass in a debug copy under lldb.
- TweakXL: runs (TweakDB loads, 196423 records) once its own tables are patched: 21 embedded copies of the 79-entry address table, `InitializeAddressTable` immediates, and the memory-vault expected-offset table (4 pools x 5 allocator slots).
- ArchiveXL (`tools/patch_archivexl.py`): loads without crashing next to TweakXL in the debug copy. Patched: table entries matched by Steam offset (ArchiveXL lists some functions under extra hashes), the `TweakDB_Load` hook, `CBaseEngine_LoadGatheredResources` (candidate `1:0x3C4FA84`) and its own memory-vault table (35 slots, incl. PoolEngine/PoolRefCount/PoolDefault at Steam-0x20).
- ResourceDepot (hash 1704595399): GOG `0x934F518`. Found through the "Resource depot not initialized" assert string: its caller uses getter `0x41ece58` (`adrp; ldr; ret`, setter right after, 67 callers). Checked at runtime in the debug copy: the global holds an object with a binary vtable, a heap array at `+0x10` and 4 entries at `+0x1c` once the game is up. It is null early in boot, so a hook that fires before the depot exists crashes in `ExtensionLoader::Configure()`.
- ArchiveXL hook 2923109755 -> `0x252F8D4` (candidate). Tested 52 shape candidates with `dbg/hit.py` (breakpoint on the detour). 40 fire before the depot exists and crash in `ExtensionLoader::Configure()`, 11 never fire, and `0x252F8D4` is the only one that fires once, with the depot filled, and keeps the game alive for 120 s. After it, `ExtensionLoader::Load()` runs and registers more hooks. Two of them are `ResourceLoader_IssueLoadingRequestByPath` (`0x41E3ABC`, 43 insns, request built with 1 at `+0x19`, -1 at `+0x20`, 0 at `+0x28`, as the SDK note says) and `ResourceLoader_IssueLoadingRequest` (`0x41E3B68`, the next function, same `0xAC` distance as in Steam). Both now attach. With them in place `Load()` goes further and 76 more hooks fail with `Detour error -2` (list in `notes/axl_failing_hooks.txt`, Steam offsets). Game stays up for 120 s.
- ArchiveXL hook 2885423437 = `ResourceDepot_InitializeArchives` (name from ArchiveXL's own table) -> `0x3EF35A8` (candidate): exactly 241 insns and 1 caller like Steam, and it holds the "Failed to find any archives in the base data directory" assert (found by xref of that string). The hook attaches and the game stays up 100 s; not checked that it fires.
- `gameIGameSystem_Spawn*` (hash 2509382878) -> `0x515E35C` (weak candidate): 228 insns, 13 callees, 9 callers vs Steam 232/14/9, the only close shape match (`0x3e7ffd8` and `0x3be3f50` were rejected earlier). The hook attaches and the game stays up 100 s; it can only fire once entities spawn, which a menu-only run does not reach, so it is untested.
- Not done: TweakXL StatService hook cluster; the 76 hooks registered by `Load()` still fail with `Detour error -2`, so those features stay off; Codeware.
- `ResourcePath_Create*` candidate `1:0x416DDE0`: exactly 107 insns (same as Steam), leaf FNV-1a 64 that strips leading quotes and slashes, 220 caller functions. Found with `tools/fnvleaf.py`. The hook attaches and the game keeps running; not checked that ArchiveXL's path mapping actually works.
- `LoadGatheredResources` candidate `1:0x3C4FA84`: virtual call `[vtbl+0x100]`, then a `bool` check whose failure path calls a helper (`0x3C530B4`) holding the "Not all Gathered Resources were loaded!" assert; the only caller function is `0x3C4EE94`. Found with `tools/callers.py`. Static only, not confirmed at runtime.
- Skipping the logos/intro to speed up test runs: `-skipStartScreen` has no effect in this build (runs with and without it end the same). The string is a `gsm::Params` session key (next to `sessionType`, `save`, `forceShutdownAfterSessionLoaded`), not a command-line argument; the only argument string found is `-jobDebugger`. `dbg/hit.py` takes extra launch arguments from `CPG_ARGS`.
- Played with it (reported by the owner of the install, not logged by tooling): on the debug copy launched through lldb (`dbg/play.py`) with RED4ext, TweakXL and ArchiveXL as patched here (Codeware ignored), a real saved game loaded and played for about 5 minutes with no crash and no corrupted-data message; RED4ext shut down cleanly. The `Spawn` candidate was in place. Which ArchiveXL/TweakXL features actually worked in game was not checked.
- Signing: the original-signature binary cannot run with RED4ext (hooks rewrite game code and macOS kills the process: `SIGKILL (Code Signature Invalid)`, `Invalid Page`). The ad-hoc re-signed debug copy (`dbg/setup.sh`) works and loads/saves games; the Galaxy sign-in errors appear with or without it.
- Tested only on a debug copy launched from lldb, not through the normal launcher.

## Layout
- `notes/gog_candidates.tsv`: hash, name, Steam 2.5 offset, GOG candidate, confidence.
- `tools/`: static analysis scripts (`python3 -I`). `tools/patch_tweakxl.py` patches an original TweakXL 0.2.0 dylib for GOG (sha256-checked, re-signs ad hoc). `shape3.py` = shape-based function matcher.
- `dbg/`: `setup.sh` makes a debuggable copy outside the .app; `crash.py` / `trace.py` are lldb commands.
- `probe/`: read-only `DYLD_INSERT_LIBRARIES` probes (edit the log path first).

## Not included
No game binary, no patched plugin dylibs, no saves. Bring your own game and plugins; patch locally.
