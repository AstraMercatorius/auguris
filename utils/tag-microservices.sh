#!/usr/bin/env bash
set -Eeuo pipefail

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
readonly TMP_DIR="/tmp/auguris"

# -----------------------------------------------------------------------------
# Logging helpers
# -----------------------------------------------------------------------------
log()   { echo -e "$@"; }
debug() {
  if [[ "${DEBUG:-false}" == "true" ]]; then
    echo "[DEBUG] $@"
  fi
  return 0
}

# -----------------------------------------------------------------------------
# Version parsing & bumping
# -----------------------------------------------------------------------------
sanitize_version() {
  # Strip CR, LF, spaces
  echo "$1" | tr -d '\r\n[:space:]'
}

parse_version() {
  # Splits $1 into v_major, v_minor, v_patch
  IFS='.' read -r v_major v_minor v_patch <<< "$1"
  v_major=${v_major:-0}
  v_minor=${v_minor:-0}
  v_patch=${v_patch:-0}
  # Force base-10 numeric
  v_major=$((10#$v_major))
  v_minor=$((10#$v_minor))
  v_patch=$((10#$v_patch))
  debug "Parsed version → ${v_major}.${v_minor}.${v_patch}"
}

bump_version() {
  # Uses global v_major, v_minor, v_patch and flags MAJOR, MINOR, PATCH
  if   $MAJOR; then ((v_major++)); v_minor=0; v_patch=0
  elif $MINOR; then ((v_minor++)); v_patch=0
  elif $PATCH; then ((v_patch++))
  fi
  printf "v%d.%d.%d" "$v_major" "$v_minor" "$v_patch"
}

# -----------------------------------------------------------------------------
# Git/tag helpers
# -----------------------------------------------------------------------------
get_last_tag() {
  local pattern=$1
  git tag --list "$pattern" | sort -V | tail -n1 || true
}

get_commit_range() {
  local last_tag=$1
  [[ -z "$last_tag" ]] && echo "--all" || echo "${last_tag}..HEAD"
}

collect_commits() {
  # $1 = range, $2 = path
  git log --pretty=format:"%H %s" "$1" -- "$2" || true
}

determine_bump_flags() {
  # $1 = all commits as lines
  MAJOR=false; MINOR=false; PATCH=false
  while IFS= read -r line; do
    local hash=${line%% *}
    local msg=${line#* }
    debug "Commit message: $msg"
    if [[ "$msg" =~ ^(feat|fix)(\(.+\))?! ]]; then
      MAJOR=true
    elif [[ "$msg" =~ ^feat ]]; then
      MINOR=true
    elif [[ "$msg" =~ ^fix ]]; then
      PATCH=true
    fi
    # check body for BREAKING CHANGE:
    if git show -s --format=%b "$hash" | grep -q "BREAKING CHANGE:"; then
      MAJOR=true
    fi
  done <<< "$1"
}

# -----------------------------------------------------------------------------
# Changelog generation
# -----------------------------------------------------------------------------
update_changelog() {
  local service_dir=$1
  local version=$2
  local commits=$3
  local changelog="$service_dir/CHANGELOG.md"

  mkdir -p "$(dirname "$changelog")"
  echo -e "## ${version}\n" >> "$changelog"

  while IFS= read -r line; do
    local h=${line%% *}
    local m=${line#* }
    printf "- %s (%s)\n" "$m" "${h:0:7}" >> "$changelog"
  done <<< "$commits"
}

# -----------------------------------------------------------------------------
# Process one service
# -----------------------------------------------------------------------------
process_service() {
  local app_group=$1
  local service=$2

  local agn=$(basename "$app_group")
  local sn=$(basename "$service")
  local tag_pattern="${agn}-${sn}/v*"
  local svc_path="packages/${agn}/${sn}"

  log "====================================================================="
  log "🔍 Processing ${agn}/${sn}"

  # 1) Find last tag
  local last_tag
  last_tag=$(get_last_tag "$tag_pattern")
  log "🏷️ Last tag: ${last_tag:-<none>}"

  # 2) Collect commits
  local range commits
  range=$(get_commit_range "$last_tag")
  debug "Commit range: $range"
  commits=$(collect_commits "$range" "$svc_path")
  if [[ -z "$commits" ]]; then
    log "⚠️  No new commits — skipping."
    return
  fi

  # 3) Determine bump flags
  log "📝 Found commits; analyzing for bump type…"
  determine_bump_flags "$commits"
  if ! $MAJOR && ! $MINOR && ! $PATCH; then
    log "⚠️  No feat:/fix:/BREAKING CHANGE — skipping."
    return
  fi

  # 4) Calculate new version
  local new_version
  if [[ -z "$last_tag" ]]; then
    new_version="v0.1.0"
  else
    local raw=${last_tag#${agn}-${sn}/v}
    raw=$(sanitize_version "$raw")
    debug "Raw version: [$raw]"
    parse_version "$raw"
    new_version=$(bump_version)
  fi

  # 5) Tag it
  local new_tag="${agn}-${sn}/${new_version}"
  git tag "$new_tag"
  log "✅ Created new tag: $new_tag"

  # 6) Update changelog & commit
  update_changelog "$svc_path" "$new_version" "$commits"
  git add "$svc_path/CHANGELOG.md"
  git commit -m "docs: update changelog for ${new_version}"

  log "🚀 Version bump completed for ${agn}/${sn}!"
}

# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------
main() {
  # prepare temp dir
  rm -rf "$TMP_DIR"
  mkdir -p "$TMP_DIR"

  # loop groups & services
  for app_group in packages/*; do
    [[ -d "$app_group" ]] || continue
    for service in "$app_group"/*; do
      [[ -d "$service" ]] || continue
      process_service "$app_group" "$service"
    done
  done
}

main "$@"
