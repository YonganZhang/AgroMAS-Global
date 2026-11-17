#!/usr/bin/env bash
set -euo pipefail
project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -d "$project_root/NUE_PCSE-Gym" || -d "$project_root/pcse" ]]; then
  echo 'Refusing to replace existing source directories; use an empty project copy.' >&2
  exit 1
fi
bash "$project_root/scripts/recreate-sources.sh"
git -C "$project_root/NUE_PCSE-Gym" apply --check "$project_root/reports/phase2-source.patch"
git -C "$project_root/NUE_PCSE-Gym" apply "$project_root/reports/phase2-source.patch"
echo 'Phase2 source patch applied; recreate-env.sh installs the pinned environment.'
