#!/usr/bin/env bash
set -e

readonly docker_base="${DOCKER_URL_BASE}/"

function build() {
  local app_group=$1
  local service_name=$2
  local tag_pattern="${app_group}-${service_name}/v*"
  local project_path="packages/${app_group}/${service_name}"
  local last_tag=$(git tag --list "${tag_pattern}" | sort -V | tail -n 1 | sed 's/\// /' | awk '{print $2}')

  echo "🔎 Processing ${app_group}/${service_name}:${last_tag}"
  
  if [ -z "$last_tag" ]; then
    echo "🟠 No tag was found for $app_group/$service_name"
    return
  fi

  echo "🪚 Building image for $last_tag"

  pipenv run pipreqs --force --savepath "${project_path}/requirements.txt" "${project_path}"
  cat "${project_path}/requirements.txt"

  docker build \
    --build-arg PROJECT_PATH=$project_path \
    --push \
    -t ${docker_base}auguris/$app_group-$service_name:latest \
    -t ${docker_base}auguris/$app_group-$service_name:$last_tag \
    -f infrastructure/docker/Dockerfile.python \
    .
  rm "${service}/requirements.txt"

  return 0
}

build $@
