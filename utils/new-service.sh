#!/usr/bin/env bash
set -e

function main () {
  local app_group=$1
  local service=$2
  if [ -z "${app_group}" ] || [ -z "${service}" ]; then
    echo "Usage: task new:service -- <app_group> <service>"
    exit 1
  fi

  local template_dir=".templates/microservice"
  local target_dir="packages/${app_group}/${service}"

  if [ -d "$target_dir" ]; then
    echo "Microservice already exists at $target_dir"
    exit 1
  fi

  if [ ! -d "$template_dir" ]; then
    echo "Error: Template directory $template_dir not found!"
    exit 1
  fi

  mkdir -p "$target_dir"
  cp -r "$template_dir/"* "$target_dir/"

  echo "✅ Microservice '${service}' created successfully in packages/${app_group}"
}

main $@
