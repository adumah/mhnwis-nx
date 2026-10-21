#!/usr/bin/env bash
# Installs Microsoft's DirectX Shader Compiler (official Linux release, checksum-pinned) where Renut's build looks for
# it: <sa2-nx>/app/thirdparty/reblue-XenosRecomp/thirdparty/dxc-bin/{bin,lib}/x64. The sa2-nx tree ships only DXC's
# headers there. Run once after cloning sa2-nx (tools/build_sdk.sh does not need it; tools/build_pc.sh does).
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
sa2="${SA2_NX:-$root/../sa2-nx}"
dest="$sa2/app/thirdparty/reblue-XenosRecomp/thirdparty/dxc-bin"
url="https://github.com/microsoft/DirectXShaderCompiler/releases/download/v1.9.2609/linux_dxc_2026_09_28.x86_x64.tar.gz"
sha256="96faadc7f5c282d2ffda49804beb4c3ee38127bc252b723234e3c5cdf7aa39a1"
[[ -d "$dest" ]] || { echo "sa2-nx not found at $sa2 (no $dest): clone it there or set SA2_NX" >&2; exit 1; }
if [[ -x "$dest/bin/x64/dxc-linux" ]]; then
  echo "DXC already installed in $dest"
  exit 0
fi
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
curl -fsSL -o "$work/dxc.tar.gz" "$url"
echo "$sha256  $work/dxc.tar.gz" | sha256sum -c --quiet
mkdir -p "$work/x" "$dest/bin/x64" "$dest/lib/x64"
tar -xzf "$work/dxc.tar.gz" -C "$work/x"
cp "$work/x/bin/dxc" "$dest/bin/x64/dxc-linux"
cp "$work/x/lib/libdxcompiler.so" "$work/x/lib/libdxil.so" "$dest/lib/x64/"
cp "$work/x/LICENSE-MS.txt" "$work/x/LICENSE-LLVM.txt" "$dest/"
LD_LIBRARY_PATH="$dest/lib/x64" "$dest/bin/x64/dxc-linux" --version
echo "DXC installed in $dest"
