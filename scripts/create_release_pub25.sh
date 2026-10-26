#!/bin/bash
# Builds the macOS release zip for Cyberpunk 2077 2.5.0 from PREBUILT inputs: the portable loader build, the address database of the SDK it
# was built against, and the portable builds of Codeware, ArchiveXL and TweakXL. It builds nothing and downloads nothing.
#
#   scripts/create_release_pub25.sh VERSION --frameworks DIR [--loader-build DIR] [--plugins DIR] [--sdk DIR] [--out DIR] [--allow-dirty]
#
#   VERSION          vX.Y.Z or vX.Y.Z-rcN without the v (install.sh accepts only those), for example 0.2.0
#   --frameworks DIR the release folder that tools/build-all.sh --portable wrote (cp2077-mac repository): Codeware/, ArchiveXL/, TweakXL/,
#                    SHA256SUMS and manifest.json. Its manifest must say it is a portable build, and the plugin checkouts must be at the
#                    commits it names. Required.
#   --loader-build D the CMake build directory of this repository (default: build-release). It needs libs/RED4ext.dylib and
#                    bin/red4ext_plugin_check, and must have been configured Release with a deployment target of 15.5 or older.
#   --plugins DIR    the folder with the three plugin checkouts cp2077-codeware, cp2077-archive-xl-macos and cp2077-tweak-xl-macos
#                    (default: ../plugins). Their Scripts, Data, licenses and the Codeware composition tools come from there.
#   --sdk DIR        the RED4ext.SDK checkout with cyberpunk2077_addresses.json (default: the one the loader build was configured with).
#   --out DIR        default: release/ in this repository. Writes RED4ext-macOS-arm64-VERSION.zip, install.sh and SHA256SUMS there.
#   --allow-dirty    package although a repository has uncommitted changes (BUILD_INFO.json then says -dirty).
#
# Zip layout (the contents of its top-level folder go into the game folder; the same as scripts/create_release.sh, which install.sh relies on):
#   launch_red4ext.sh, INSTALL_MACOS.md
#   red4ext/VERSION, BUILD_INFO.json   version, build date, commit of every component and library, sha256 of every binary
#   red4ext/RED4ext.dylib, config.ini, LICENSE.txt, THIRD_PARTY_LICENSES.md
#   red4ext/bin/red4ext_plugin_check, red4ext/bin/x64/cyberpunk2077_addresses.json
#   red4ext/macos/scripts/install_macos.sh, codesign_macos.sh, red4ext_entitlements.plist
#   red4ext/plugins/Codeware/    Codeware.dylib, Scripts/ (composed like the macOS script cache build composes them), LICENSE, THIRD_PARTY_LICENSES.txt
#   red4ext/plugins/ArchiveXL/   ArchiveXL.dylib, Scripts/, Bundle/VisualTags.xl, mac-mount-skip.example.txt, LICENSE, THIRD_PARTY_LICENSES.txt
#   red4ext/plugins/TweakXL/     TweakXL.dylib, Scripts/ (composed), Data/*.dat, LICENSE, THIRD_PARTY_LICENSES.txt
# No ModMenu. No r6/input files: none of the three plugins has one on macOS.
#
# The dylibs are statically linked against fmt, spdlog and yaml-cpp (CP2077_MAC_PORTABLE), so no library ships next to them. Every binary
# is checked before packaging: deployment target 15.5 or older, only /usr/lib and /System libraries, no /opt/homebrew string, and
# red4ext_plugin_check (with the packaged database) must accept all plugins.
set -euo pipefail

die() { echo "[release] $*" >&2; exit 1; }

VERSION=${1:?usage: create_release_pub25.sh VERSION --frameworks DIR [--loader-build DIR] [--plugins DIR] [--sdk DIR] [--out DIR] [--allow-dirty]}
shift
[[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-rc[0-9]+)?$ ]] || die "VERSION must look like 0.2.0 or 0.2.0-rc1 (install.sh accepts vX.Y.Z and vX.Y.Z-rcN), not '$VERSION'"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WS="$ROOT/.."
FRAMEWORKS=""
LOADER_BUILD="$ROOT/build-release"
PLUGINS="$WS/plugins"
SDK=""
OUT="$ROOT/release"
ALLOW_DIRTY=0
while [[ $# -gt 0 ]]; do
    case "$1" in
    --frameworks) FRAMEWORKS="$2"; shift 2 ;;
    --loader-build) LOADER_BUILD="$2"; shift 2 ;;
    --plugins) PLUGINS="$2"; shift 2 ;;
    --sdk) SDK="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;;
    --allow-dirty) ALLOW_DIRTY=1; shift ;;
    *) die "unknown option: $1" ;;
    esac
done
[[ -n "$FRAMEWORKS" ]] || die "--frameworks DIR is required (the release folder of tools/build-all.sh --portable)"
FRAMEWORKS="$(cd "$FRAMEWORKS" && pwd)"
LOADER_BUILD="$(cd "$LOADER_BUILD" && pwd)"
PLUGINS="$(cd "$PLUGINS" && pwd)"
mkdir -p "$OUT"
OUT="$(cd "$OUT" && pwd)"

CW="$PLUGINS/cp2077-codeware"
AXL="$PLUGINS/cp2077-archive-xl-macos"
TXL="$PLUGINS/cp2077-tweak-xl-macos"
NAME="RED4ext-macOS-arm64-$VERSION"
STAGE="$OUT/$NAME"

# --- inputs -----------------------------------------------------------------------------------------------------------------------------
echo "[release] checking the inputs"
for f in "$LOADER_BUILD/libs/RED4ext.dylib" "$LOADER_BUILD/bin/red4ext_plugin_check" "$FRAMEWORKS/SHA256SUMS" "$FRAMEWORKS/manifest.json" \
    "$FRAMEWORKS/Codeware/Codeware.dylib" "$FRAMEWORKS/ArchiveXL/ArchiveXL.dylib" "$FRAMEWORKS/TweakXL/TweakXL.dylib" \
    "$FRAMEWORKS/ArchiveXL/Bundle/VisualTags.xl"; do
    [[ -f "$f" ]] || die "missing input: $f"
done
(cd "$FRAMEWORKS" && shasum -a 256 -c SHA256SUMS >/dev/null) || die "$FRAMEWORKS does not match its SHA256SUMS"

cache_var() { sed -n "s/^$1:[A-Z]*=//p" "$LOADER_BUILD/CMakeCache.txt"; }
[[ "$(cache_var CMAKE_HOME_DIRECTORY)" == "$ROOT" ]] || die "$LOADER_BUILD was not configured from $ROOT"
[[ "$(cache_var CMAKE_BUILD_TYPE)" == "Release" ]] || die "$LOADER_BUILD is not a Release build"
if [[ -z "$SDK" ]]; then SDK="$(cache_var RED4EXT_SDK_DIR)"; fi
DB="$SDK/cyberpunk2077_addresses.json"
[[ -f "$DB" ]] || die "no address database at $DB"

rev() { echo "$(git -C "$1" rev-parse HEAD)$(git -C "$1" diff --quiet HEAD || echo -dirty)"; }
for d in "$ROOT" "$CW" "$AXL" "$TXL"; do
    if [[ "$(rev "$d")" == *-dirty && "$ALLOW_DIRTY" -ne 1 ]]; then die "$d has uncommitted changes (commit them, or use --allow-dirty)"; fi
done

# The plugin checkouts have to be the commits the frameworks were built from, and the build has to be the portable one.
python3 - "$FRAMEWORKS/manifest.json" "$CW" "$AXL" "$TXL" <<'PY' || die "the plugin checkouts do not match the frameworks build"
import json, subprocess, sys
m = json.load(open(sys.argv[1]))
if not m.get('portable'):
    sys.exit('manifest.json has no "portable" entry: build with tools/build-all.sh --portable')
want = {s['name']: s['commit'] for s in m['sources']}
for name, path in zip(('Codeware', 'ArchiveXL', 'TweakXL'), sys.argv[2:5]):
    have = subprocess.check_output(['git', '-C', path, 'rev-parse', 'HEAD'], text=True).strip()
    if want.get(name) != have:
        sys.exit('%s: the frameworks build is of %s, the checkout %s is at %s' % (name, want.get(name), path, have))
PY

# --- staging ----------------------------------------------------------------------------------------------------------------------------
echo "[release] staging $NAME"
rm -rf "$STAGE"
R4E="$STAGE/red4ext"
mkdir -p "$R4E/bin/x64" "$R4E/macos/scripts" "$R4E/plugins/Codeware" "$R4E/plugins/ArchiveXL" "$R4E/plugins/TweakXL"

install -m 755 "$LOADER_BUILD/libs/RED4ext.dylib" "$R4E/RED4ext.dylib"
install -m 755 "$LOADER_BUILD/bin/red4ext_plugin_check" "$R4E/bin/red4ext_plugin_check"
cp "$DB" "$R4E/bin/x64/"
install -m 755 "$ROOT/scripts/launch_red4ext.sh" "$STAGE/launch_red4ext.sh"
install -m 755 "$ROOT/scripts/codesign_macos.sh" "$R4E/macos/scripts/codesign_macos.sh"
cp "$ROOT/scripts/red4ext_entitlements.plist" "$R4E/macos/scripts/"
install -m 755 "$ROOT/scripts/install_macos.sh" "$R4E/macos/scripts/install_macos.sh"
cp "$ROOT/LICENSE.md" "$R4E/LICENSE.txt"
cp "$ROOT/THIRD_PARTY_LICENSES.md" "$R4E/THIRD_PARTY_LICENSES.md"
cp "$ROOT/docs/INSTALL_MACOS.md" "$STAGE/INSTALL_MACOS.md"

# The loader's configuration. WinMain always attaches; of the optional core hooks only CGameApplication_AddState is on for game 2.5.0.
# ScriptValidator_Validate and AssertionFailed stay off until a boot shows them attaching on 2.5.0 (Codeware hooks the script validator itself).
cat >"$R4E/config.ini" <<'INI'
version = 0

# WinMain always attaches. Of the optional core hooks only CGameApplication_AddState is on for game 2.5.0; ScriptValidator_Validate and
# AssertionFailed are left off until a boot shows them attaching on 2.5.0.
[hooking]
core_hooks = ["CGameApplication_AddState"]
INI

# Plugin dylibs, and the Bundle file of ArchiveXL, from the portable frameworks build.
for p in Codeware ArchiveXL TweakXL; do install -m 755 "$FRAMEWORKS/$p/$p.dylib" "$R4E/plugins/$p/$p.dylib"; done
mkdir -p "$R4E/plugins/ArchiveXL/Bundle"
cp "$FRAMEWORKS/ArchiveXL/Bundle/VisualTags.xl" "$R4E/plugins/ArchiveXL/Bundle/VisualTags.xl"
# Anything else the frameworks build shipped next to a dylib (it must be nothing but the Bundle file: the portable build has no libraries).
extra=$(cd "$FRAMEWORKS" && find Codeware ArchiveXL TweakXL -type f ! -name '*.dylib' ! -path 'ArchiveXL/Bundle/VisualTags.xl' | sort)
[[ -z "$extra" ]] || die "the frameworks build has files this script does not place: $extra"

# Scripts. Codeware and TweakXL are composed into one file per module like the Windows package does and like the macOS script cache build
# does (cp2077-codeware/tools/compose-redscripts.py, with the Mac exclusions of tools/build-cache.exclude); ArchiveXL ships its three files as
# they are. launch_red4ext.sh compiles red4ext/plugins/<Plugin>/Scripts together with the game's scripts.
upstream_version() { sed -n 's/.*set_version("\([0-9.]*\)".*/\1/p' "$1/xmake.lua" | head -n 1; }
CW_VERSION="$(upstream_version "$CW")"
TXL_VERSION="$(upstream_version "$TXL")"
[[ -n "$CW_VERSION" && -n "$TXL_VERSION" ]] || die "no set_version in the xmake.lua of Codeware or TweakXL"
python3 - "$CW" "$CW_VERSION" "$R4E/plugins/Codeware/Scripts" "$TXL" "$TXL_VERSION" "$R4E/plugins/TweakXL/Scripts" <<'PY' || die "composing the scripts failed"
import importlib.util, os, sys
cw, cw_version, cw_out, txl, txl_version, txl_out = sys.argv[1:7]
spec = importlib.util.spec_from_file_location('compose_redscripts', os.path.join(cw, 'tools', 'compose-redscripts.py'))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def write(bundles, out, skip=()):
    os.makedirs(out, exist_ok=True)
    for scope in sorted(bundles):
        if scope + '.reds' in skip:
            continue
        with open(os.path.join(out, scope + '.reds'), 'wb') as f:
            f.write(bundles[scope].encode('ascii', 'replace'))   # the Windows script writes ASCII too

excl = []
skip = set()
for line in open(os.path.join(cw, 'tools', 'build-cache.exclude')):
    line = line.split('#', 1)[0].strip()
    if line.startswith('Codeware-src/'):
        excl.append(line[len('Codeware-src/'):])
    elif line.startswith('Codeware/'):
        skip.add(line[len('Codeware/'):])
write(mod.compose(os.path.join(cw, 'scripts'), 'Codeware', cw_version, excl), cw_out, skip)
write(mod.compose(os.path.join(txl, 'scripts'), 'TweakXL', txl_version, []), txl_out)
PY
mkdir -p "$R4E/plugins/ArchiveXL/Scripts"
cp "$AXL"/scripts/*.reds "$R4E/plugins/ArchiveXL/Scripts/"

# TweakXL reads only the .dat files of its Data folder.
mkdir -p "$R4E/plugins/TweakXL/Data"
cp "$TXL/data/InheritanceMap.dat" "$TXL/data/ExtraFlats.dat" "$R4E/plugins/TweakXL/Data/"
# ArchiveXL: the template for the list of archives it must not mount (the user's own mac-mount-skip.txt is never shipped).
cp "$AXL/macos/mac-mount-skip.example.txt" "$R4E/plugins/ArchiveXL/mac-mount-skip.example.txt"

# Licenses: the plugin's own and, in one file, its repository's third-party licenses followed by the libraries compiled into the dylib.
LIC="$ROOT/scripts/pub25-licenses"
for pair in "Codeware:$CW:fmt-12.2.0 spdlog-1.17.0" "ArchiveXL:$AXL:fmt-12.2.0 spdlog-1.17.0 yaml-cpp-0.9.0" "TweakXL:$TXL:fmt-12.2.0 spdlog-1.17.0 yaml-cpp-0.9.0"; do
    p="${pair%%:*}"; rest="${pair#*:}"; src="${rest%%:*}"; libs="${rest#*:}"
    cp "$src/LICENSE" "$R4E/plugins/$p/LICENSE"
    {
        echo "Third-party licenses of $p"
        echo
        echo "Libraries compiled into $p.dylib (static libraries): ${libs}"
        for l in $libs; do
            echo
            echo "=============================================================================="
            echo "$l"
            echo "=============================================================================="
            cat "$LIC/$l.txt"
        done
        echo
        echo "=============================================================================="
        echo "Libraries and code included in the sources of $p (its THIRD_PARTY_LICENSES)"
        echo "=============================================================================="
        cat "$src/THIRD_PARTY_LICENSES"
    } >"$R4E/plugins/$p/THIRD_PARTY_LICENSES.txt"
done

# --- signing and checks -------------------------------------------------------------------------------------------------------------------
"$ROOT/scripts/codesign_macos.sh" dylib "$R4E/RED4ext.dylib" "$R4E/plugins/"*/*.dylib
codesign -f -s - "$R4E/bin/red4ext_plugin_check"

# Players' Macs have only the system libraries: refuse any binary that links something else (for example from Homebrew), is built for a
# newer macOS than the game needs, or carries a Homebrew path.
for bin in "$R4E/RED4ext.dylib" "$R4E/bin/red4ext_plugin_check" "$R4E/plugins/"*/*.dylib; do
    id=$(otool -D "$bin" 2>/dev/null | tail -n +2)
    foreign=$(otool -L "$bin" | tail -n +2 | awk '{ print $1 }' | grep -v -e '^/usr/lib/' -e '^/System/' | grep -vxF "${id:-none}" || true)
    if [[ -n "$foreign" ]]; then
        echo "[release] $bin links libraries players don't have:"; echo "$foreign"; exit 1
    fi
    minos=$(otool -l "$bin" | awk '/LC_BUILD_VERSION/ { b = 1 } b && /minos/ { print $2; exit }')
    [[ -n "$minos" && "$(printf '%s\n15.5\n' "$minos" | sort -V | tail -n 1)" == "15.5" ]] || die "$bin is built for macOS ${minos:-?}, not 15.5 or older"
    brew=$(strings "$bin" | grep -c /opt/homebrew || true)
    [[ "$brew" == "0" ]] || die "$bin contains $brew /opt/homebrew strings"
    codesign -v "$bin" || die "$bin: signature does not verify"
done
"$R4E/bin/red4ext_plugin_check" "$R4E/bin/x64/cyberpunk2077_addresses.json" "$R4E/plugins/"*/*.dylib

# --- traceability -------------------------------------------------------------------------------------------------------------------------
echo "$VERSION" >"$R4E/VERSION"
python3 - "$R4E" "$VERSION" "$ROOT" "$SDK" "$FRAMEWORKS/manifest.json" "$CW/macos/PortableDeps.cmake" <<'PY'
import hashlib, json, os, re, subprocess, sys
r4e, version, root, sdk, manifest_path, deps_cmake = sys.argv[1:7]

def git(repo, *a):
    return subprocess.check_output(['git', '-C', repo] + list(a), text=True).strip()

def rev(repo):
    dirty = subprocess.call(['git', '-C', repo, 'diff', '--quiet', 'HEAD']) != 0
    return git(repo, 'rev-parse', 'HEAD') + ('-dirty' if dirty else '')

db = json.load(open(os.path.join(r4e, 'bin', 'x64', 'cyberpunk2077_addresses.json')))
manifest = json.load(open(manifest_path))
pins = {}
for m in re.finditer(r'set\(CP2077_(FMT|SPDLOG|YAML_CPP)_(TAG|COMMIT) "([^"]+)"\)', open(deps_cmake).read()):
    pins.setdefault(m.group(1), {})[m.group(2).lower()] = m.group(3)
repos = {'fmt': 'https://github.com/fmtlib/fmt', 'spdlog': 'https://github.com/gabime/spdlog', 'yaml-cpp': 'https://github.com/jbeder/yaml-cpp'}
libs = {}
for k, v in pins.items():
    name = k.lower().replace('_', '-')
    libs[name] = dict(v, repository=repos[name])

subs = {}
for line in git(root, 'submodule', 'status').splitlines():
    parts = line.strip().lstrip('+-U').split()
    subs[parts[1]] = parts[0]

files = {}
for dirpath, _, names in os.walk(r4e):
    for n in sorted(names):
        if n.endswith('.dylib') or n == 'red4ext_plugin_check':
            p = os.path.join(dirpath, n)
            files[os.path.relpath(p, r4e)] = hashlib.sha256(open(p, 'rb').read()).hexdigest()

info = {
    'version': version,
    'date': subprocess.check_output(['date', '-u', '+%Y-%m-%dT%H:%M:%SZ'], text=True).strip(),
    'game_version': '2.5.0',
    'game_uuid': db['uuid'],
    'deployment_target': '15.5',
    'commits': {
        'RED4ext': rev(root),
        'RED4ext.SDK (loader, address database)': rev(sdk),
    },
    'loader_branch': git(root, 'rev-parse', '--abbrev-ref', 'HEAD'),
    'loader_submodules': subs,
    'plugin_branches': {s['name']: s['branch'] for s in manifest['sources']},
    'static_libraries_in_the_plugins': libs,
    'toolchain': manifest.get('toolchain', {}),
    'frameworks_build': os.path.basename(os.path.dirname(os.path.abspath(manifest_path))),
    'binaries_sha256': files,
}
for s in manifest['sources']:
    info['commits'][s['name']] = s['commit'] + ('-dirty' if s.get('dirty') else '')
json.dump(info, open(os.path.join(r4e, 'BUILD_INFO.json'), 'w'), indent=2)
open(os.path.join(r4e, 'BUILD_INFO.json'), 'a').write('\n')
PY
python3 -m json.tool "$R4E/BUILD_INFO.json" >/dev/null

# --- zip ----------------------------------------------------------------------------------------------------------------------------------
(cd "$OUT" && rm -f "$NAME.zip" && ditto -c -k --norsrc --noextattr --noqtn --keepParent "$NAME" "$NAME.zip")
install -m 755 "$ROOT/install.sh" "$OUT/install.sh"
(cd "$OUT" && shasum -a 256 "$NAME.zip" install.sh | tee SHA256SUMS)
echo "[release] wrote $OUT/$NAME.zip, install.sh, SHA256SUMS"
