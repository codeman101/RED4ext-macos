# RED4ext for macOS

RED4ext is the script extender and plugin loader for Cyberpunk 2077. This is its macOS port. It loads `.dylib` plugins
into the game and hooks game functions natively, with an in-process arm64 hook engine. The release also contains
Codeware, ArchiveXL and TweakXL.

Supported: **Cyberpunk 2077 2.5.0, Steam, Apple silicon Mac, macOS 15.5 or later.** Other game builds are refused.

Maintained by codeman101, continuing jackmaxwil's macOS port (the 0.1.0 releases for game 2.3.1).

RED4ext is fail-closed. It uses only game addresses that have been verified for this exact game build. A plugin that
takes its game addresses from RED4ext's address database is not loaded if it needs any unverified address; the game then
starts without that plugin. A plugin that carries its own address table (built with the macOS RED4ext.SDK) is loaded
as it is.

## Install

Quit the game, open Terminal and run:

```bash
curl -fsSL https://raw.githubusercontent.com/codeman101/RED4ext-macos/main/install.sh | bash
```

- Update: `curl -fsSL https://raw.githubusercontent.com/codeman101/RED4ext-macos/main/install.sh | bash -s -- update`
- Uninstall: `curl -fsSL https://raw.githubusercontent.com/codeman101/RED4ext-macos/main/install.sh | bash -s -- uninstall`
- Check your setup: `curl -fsSL https://raw.githubusercontent.com/codeman101/RED4ext-macos/main/install.sh | bash -s -- doctor`
- Play with mods: `curl -fsSL https://raw.githubusercontent.com/codeman101/RED4ext-macos/main/install.sh | bash -s -- play`

**Requirements:** Cyberpunk 2077 2.5.0 (Steam) on an Apple silicon Mac with macOS 15.5 or later, and redscript 0.5.32 or
newer: download `redscript-vX.Y.Z-macos.zip` from [redscript's releases](https://github.com/jac3km4/redscript/releases)
and unzip it into the game folder (it adds `engine/tools/scc`). The launcher compiles every mod's scripts with it,
including those of Codeware, ArchiveXL and TweakXL.

Prefer to do it by hand? See [docs/INSTALL_MACOS.md](docs/INSTALL_MACOS.md).

## Play

1. Start Steam and sign in.
2. Run:
   ```bash
   "$HOME/Library/Application Support/Steam/steamapps/common/Cyberpunk 2077/launch_red4ext.sh"
   ```

The Steam **Play** button starts the game **without** mods. Always use `launch_red4ext.sh`.

## Installing mods

Put each kind of mod where it would go on Windows, inside the game folder:

| Mod files | Folder | Needs |
| --- | --- | --- |
| `.archive` (and `.archive.xl`) | `archive/Mac/mod/` | ArchiveXL. The macOS game does not read this folder itself; ArchiveXL loads it. |
| `.yaml` / `.tweak` tweaks | `r6/tweaks/` | TweakXL |
| `.reds` scripts | `r6/scripts/` | Nothing. The launcher compiles them. |
| RED4ext plugins (`.dylib`) | `red4ext/plugins/<Name>/` | A macOS build of the plugin. Windows `.dll` plugins do not work. |

## Uninstall

```bash
curl -fsSL https://raw.githubusercontent.com/codeman101/RED4ext-macos/main/install.sh | bash -s -- uninstall
```

It removes RED4ext, its plugins and their key bindings, and restores the original game binary. Your mods in
`archive/Mac/mod`, `r6/scripts` and `r6/tweaks` stay. Steam > Cyberpunk 2077 > Properties > Installed Files > **Verify
integrity of game files** also restores the original game binary. To uninstall by hand, see
[docs/INSTALL_MACOS.md](docs/INSTALL_MACOS.md#uninstall).

## Troubleshooting

First run `curl -fsSL https://raw.githubusercontent.com/codeman101/RED4ext-macos/main/install.sh | bash -s -- doctor`. It changes nothing and says what is wrong.

- **The game starts without mods:** you started it from Steam. Start it with `launch_red4ext.sh`.
- **`install_macos.sh` says the game build does not match:** your game version is not supported by this release. Wait
  for a release for your game version.
- **A plugin does not load:** open the newest `red4ext/logs/red4ext-*.log` in the game folder. It names each refused
  plugin and the reason, usually unverified addresses. That plugin needs an update; the game runs without it.
- **After a game update, no mods work:** a game patch changes the binary, and RED4ext refuses all hooks until its
  addresses are verified again for the new build. Wait for a new release. Do not edit the address database.
- **The launcher stops with "REDscript compilation failed":** a mod's scripts have errors. The printed errors name the
  file. Remove that mod, then launch again. If every script fails, check that redscript 0.5.32 or newer is installed.
- **Saves or achievements are missing:** Steam was not running. Start Steam and sign in first.

## Build from source (developers)

Requires Xcode command line tools, CMake 3.23+ and Python 3.

```bash
git clone --recursive -b main https://github.com/codeman101/RED4ext-macos.git RED4ext
cd RED4ext
cmake -S . -B build-dev && cmake --build build-dev -j8
ctest --test-dir build-dev --output-on-failure
```

`deps/red4ext.sdk` is [codeman101/RED4ext.SDK-macos](https://github.com/codeman101/RED4ext.SDK-macos) (branch
`loader-2.5`), which holds the 2.5.0 address database. The Codeware, ArchiveXL and TweakXL builds in the release come from
codeman101/cp2077-codeware, codeman101/cp2077-archive-xl-macos and codeman101/cp2077-tweak-xl (branch `mac-v1-2.5`).

Test loop (needs the game installed and re-signed once with `scripts/codesign_macos.sh exe <game binary>`). These tools
still expect the 0.1.0 workspace: the component repos with a root CMake build, cloned next to this one.

```bash
tools/cp-dev tweakxl --plugins TweakXL,ArchiveXL
```

`tools/cp-dev` builds RED4ext and the listed plugins, signs and installs them into the game folder, then runs
`tools/cp-run`, which starts the game in the background and runs an unattended in-game test. Scenarios are in
`tools/autotest/scenarios` (`tweakxl`, `tweakxl-reload`, `archivexl`, `modmenu`, `modmenu-ui`) plus `boot` and `load`.
Results go to `runs/<timestamp>-<scenario>/`. Exit code 0 means pass. `tools/cp-rollback` restores the stock game
binary.

`tools/cp-regress` runs the gate and every scenario with the plugins it needs (about 10 minutes, all in the
background) and prints a pass/fail table. Run it before every release.

`tools/cp-gate` is the offline release and patch-day gate. It never starts the game. It checks that the installed game
matches the address database, that the verified entries validate, and that every address each plugin uses is verified.
After a game update, follow the patch-day steps in its header.

Release: add a `## [X.Y.Z]` section to `CHANGELOG.md` and build the zip with `scripts/create_release_pub25.sh X.Y.Z`
from the prebuilt components, then publish it as the GitHub release `vX.Y.Z`. `.github/workflows/release.yml` still builds
the 0.1.0 component set and runs only by hand. Each zip has `red4ext/VERSION` and `red4ext/BUILD_INFO.json` (the commit
of every component).

## Repository layout

| Path | Contents |
| --- | --- |
| `src/dll/` | The loader. `Platform/NativeHook*` is the arm64 hook engine, `Platform/PluginRequirements.cpp` the plugin address gate. |
| `src/plugin_check/` | `red4ext_plugin_check`, the same address gate as a command-line tool. |
| `deps/` | Git submodules. `deps/red4ext.sdk` is the macOS SDK (codeman101/RED4ext.SDK-macos) and holds `cyberpunk2077_addresses.json`. |
| `install.sh` | The one-command installer (install, update, uninstall, doctor, play). Also attached to each release. |
| `scripts/` | Install, launch, signing and release scripts. |
| `tools/` | `cp-dev`, `cp-run`, `cp-gate`, `cp-rollback` and the in-game autotest scenarios. |
| `tests/` | Unit, integration and native hook tests (CTest). |
| `docs/` | Install guide and reference notes. |

## Credits

Forked from [WopsS/RED4ext](https://github.com/WopsS/RED4ext) by WopsS and contributors, through jackmaxwil's macOS port. MIT license, see
[LICENSE.md](LICENSE.md) and [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).
