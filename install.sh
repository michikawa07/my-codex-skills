#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: ./install.sh [--legacy-codex] [--hooks] [--replace] [--target PATH]

Options:
  --legacy-codex  Also link ~/.codex/skills for older Codex installations.
  --hooks          Link shared hooks into ~/.codex.
  --replace       Move an existing non-symlink target to <target>.bak.<timestamp>.
  --target PATH   Link an explicit skills target instead of ~/.agents/skills.
  -h, --help      Show this help.
USAGE
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skills_src="$script_dir/skills"
hooks_src="$script_dir/hooks"
replace=false
install_hooks=false
targets=("$HOME/.agents/skills")

while [[ $# -gt 0 ]]; do
  case "$1" in
    --legacy-codex)
      targets+=("$HOME/.codex/skills")
      shift
      ;;
    --hooks)
      install_hooks=true
      shift
      ;;
    --replace)
      replace=true
      shift
      ;;
    --target)
      if [[ $# -lt 2 ]]; then
        echo "error: --target requires a path" >&2
        exit 2
      fi
      targets=("$2")
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ ! -d "$skills_src" ]]; then
  echo "error: skills directory not found: $skills_src" >&2
  exit 1
fi

link_target() {
  local source="$1"
  local target="$2"
  local parent
  parent="$(dirname "$target")"
  mkdir -p "$parent"

  if [[ -L "$target" ]]; then
    ln -sfn "$source" "$target"
    echo "updated symlink: $target -> $source"
    return
  fi

  if [[ ! -e "$target" ]]; then
    ln -s "$source" "$target"
    echo "created symlink: $target -> $source"
    return
  fi

  if [[ "$replace" == true ]]; then
    local backup="${target}.bak.$(date +%Y%m%d%H%M%S)"
    mv "$target" "$backup"
    ln -s "$source" "$target"
    echo "moved existing target to: $backup"
    echo "created symlink: $target -> $source"
    return
  fi

  echo "error: target already exists and is not a symlink: $target" >&2
  echo "       rerun with --replace to back it up and create the symlink" >&2
  exit 1
}

check_target() {
  local target="$1"
  if [[ -L "$target" || ! -e "$target" || "$replace" == true ]]; then
    return
  fi
  echo "error: target already exists and is not a symlink: $target" >&2
  echo "       rerun with --replace to back it up and create the symlink" >&2
  exit 1
}

if [[ "$install_hooks" == true ]]; then
  if [[ ! -d "$hooks_src" || ! -f "$hooks_src/hooks.json" ]]; then
    echo "error: hooks not found under: $hooks_src" >&2
    exit 1
  fi
  # Avoid installing only half of the paired hooks links.
  check_target "$HOME/.codex/hooks"
  check_target "$HOME/.codex/hooks.json"
fi

for target in "${targets[@]}"; do
  link_target "$skills_src" "$target"
done

if [[ "$install_hooks" == true ]]; then
  link_target "$hooks_src" "$HOME/.codex/hooks"
  link_target "$hooks_src/hooks.json" "$HOME/.codex/hooks.json"
fi

echo "Restart Codex to pick up skill and hook changes."
