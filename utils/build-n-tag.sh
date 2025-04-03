#!/usr/bin/env bash
set -e

readonly docker_base="${DOCKER_URL_BASE}/"

function main() {
  for app_group in packages/*; do
    [ -d "$app_group" ] || continue

    for service in "$app_group"/*; do
      [ -d "$service" ] || continue
      
      app_group_name=$(basename "$app_group")
      service_name=$(basename "$service")
      
      echo "🔍 Processing: $app_group_name/$service_name"

      tag_pattern="${app_group_name}-${service_name}/v*"

      last_tag=$(git tag --list "$tag_pattern" | sort -V | tail -n 1 | sed 's/\// /' | awk '{print $2}')
      
      if [ -z "$last_tag" ]; then
        echo "🟠 No tag was found for $app_group_name/$service_name"
        continue
      fi

      echo "🪚 Building image for $last_tag"

      pipreqs --force --savepath "${service}/requirements.txt" "${service}"
      
      docker build \
        --build-arg PROJECT_PATH=$service \
        --push \
        -t ${docker_base}$app_group_name-$service_name:latest \
        -t ${docker_base}$app_group_name-$service_name:$last_tag \
        -f infrastructure/docker/Dockerfile.python \
        .
      rm "${service}/requirements.txt"
    done
  done
  return 0
}

main $@
