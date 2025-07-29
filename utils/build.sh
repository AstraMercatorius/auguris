#!/usr/bin/env bash
set -e

readonly docker_base="${DOCKER_URL_BASE:-}/"

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

function log() {
  echo -e "${BLUE}[BUILD]${NC} $1"
}

function log_success() {
  echo -e "${GREEN}[SUCCESS]${NC} $1"
}

function log_warning() {
  echo -e "${YELLOW}[WARNING]${NC} $1"
}

function log_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

# Function to build a single service
function build_service() {
  local app_group="$1"
  local service_name="$2"
  local service_path="packages/${app_group}/${service_name}"
  
  log "🔍 Processing: $app_group/$service_name"

  # Check if service directory exists
  if [ ! -d "$service_path" ]; then
    log_error "Service directory $service_path not found"
    return 1
  fi

  # Find the latest tag for this service
  tag_pattern="${app_group}-${service_name}/v*"
  last_tag=$(git tag --list "$tag_pattern" | sort -V | tail -n 1 | sed 's/\// /' | awk '{print $2}')
  
  if [ -z "$last_tag" ]; then
    log_warning "No tag was found for $app_group/$service_name, skipping build"
    return 0
  fi

  log "🪚 Building image for $last_tag"

  # Generate requirements.txt
  pipenv run pipreqs --force --savepath "${service_path}/requirements.txt" "${service_path}"
  log "📦 Generated requirements.txt for $app_group/$service_name:"
  cat "${service_path}/requirements.txt"
  
  # Build and push Docker image
  if docker buildx build \
    --platform linux/amd64,linux/arm64 \
    --build-arg PROJECT_PATH=$service_path \
    --push \
    -t ${docker_base}auguris/$app_group-$service_name:latest \
    -t ${docker_base}auguris/$app_group-$service_name:$last_tag \
    -f infrastructure/docker/Dockerfile.python \
    .; then
    
    log_success "Successfully built and pushed $app_group/$service_name:$last_tag"
  else
    log_error "Failed to build $app_group/$service_name"
    rm -f "${service_path}/requirements.txt"
    return 1
  fi
  
  # Clean up
  rm "${service_path}/requirements.txt"
  return 0
}

# Function to discover all services
function discover_services() {
  local services=()
  
  for app_group in packages/*; do
    [ -d "$app_group" ] || continue
    
    for service in "$app_group"/*; do
      [ -d "$service" ] || continue
      
      app_group_name=$(basename "$app_group")
      service_name=$(basename "$service")
      services+=("$app_group_name:$service_name")
    done
  done
  
  printf '%s\n' "${services[@]}"
}

# Function to build a specific service by name
function build_specific() {
  local target_service="$1"
  
  if [ -z "$target_service" ]; then
    log_error "No service specified"
    return 1
  fi
  
  log "🔍 Looking for service: $target_service"
  
  # Parse the target service - it could be in format "app_group-service_name" or "app_group/service_name"
  local app_group service_name
  
  if [[ "$target_service" == *"/"* ]]; then
    # Format: app_group/service_name
    IFS='/' read -r app_group service_name <<< "$target_service"
  elif [[ "$target_service" == *"-"* ]]; then
    # Format: app_group-service_name (need to be careful here as service names might contain dashes)
    # Try to find the actual service first
    local found=false
    for app_group_dir in packages/*; do
      [ -d "$app_group_dir" ] || continue
      local app_group_name=$(basename "$app_group_dir")
      
      for service_dir in "$app_group_dir"/*; do
        [ -d "$service_dir" ] || continue
        local service_dir_name=$(basename "$service_dir")
        local full_name="${app_group_name}-${service_dir_name}"
        
        if [ "$full_name" = "$target_service" ]; then
          app_group="$app_group_name"
          service_name="$service_dir_name"
          found=true
          break 2
        fi
      done
    done
    
    if [ "$found" = false ]; then
      log_error "Service '$target_service' not found"
      log "Available services:"
      list_services | grep "📦" || true
      return 1
    fi
  else
    log_error "Invalid service format. Use 'app_group/service_name' or 'app_group-service_name'"
    return 1
  fi
  
  local service_path="packages/${app_group}/${service_name}"
  
  if [ ! -d "$service_path" ]; then
    log_error "Service directory $service_path not found"
    log "Available services:"
    list_services | grep "📦" || true
    return 1
  fi
  
  log "✅ Found service: $app_group/$service_name"
  log "📁 Service path: $service_path"
  
  # Build the specific service
  if build_service "$app_group" "$service_name"; then
    log_success "🎉 Successfully built $app_group/$service_name"
    return 0
  else
    log_error "❌ Failed to build $app_group/$service_name"
    return 1
  fi
}

# Function to build services sequentially (original behavior)
function build_sequential() {
  local failed_builds=()
  
  for app_group in packages/*; do
    [ -d "$app_group" ] || continue

    for service in "$app_group"/*; do
      [ -d "$service" ] || continue
      
      app_group_name=$(basename "$app_group")
      service_name=$(basename "$service")
      
      if ! build_service "$app_group_name" "$service_name"; then
        failed_builds+=("$app_group_name/$service_name")
      fi
    done
  done
  
  if [ ${#failed_builds[@]} -eq 0 ]; then
    log_success "🎉 All services built successfully!"
    return 0
  else
    log_error "❌ ${#failed_builds[@]} services failed to build:"
    for failed in "${failed_builds[@]}"; do
      log_error "  - $failed"
    done
    return 1
  fi
}

function show_help() {
  cat << EOF
Usage: $0 [OPTIONS] [SERVICE]

Build microservices in the monorepo.

OPTIONS:
  -l, --list              List all discovered services
  -h, --help              Show this help message

ARGUMENTS:
  SERVICE                 Specific service to build in format:
                         'app_group/service_name' or 'app_group-service_name'
                         If not specified, builds all services sequentially

ENVIRONMENT VARIABLES:
  DOCKER_URL_BASE         Base URL for Docker registry (required for pushing)

EXAMPLES:
  $0                              # Build all services sequentially
  $0 market-data/feature-engineering   # Build specific service (slash format)
  $0 market-data-feature-engineering   # Build specific service (dash format)
  $0 --list                       # List all services without building

EOF
}

function list_services() {
  log "🔍 Discovering services..."
  local services
  mapfile -t services < <(discover_services)
  
  if [ ${#services[@]} -eq 0 ]; then
    log_warning "No services found"
    return 0
  fi
  
  log "Found ${#services[@]} services:"
  for service_spec in "${services[@]}"; do
    IFS=':' read -r app_group service_name <<< "$service_spec"
    echo "  📦 $app_group/$service_name"
  done
}

function main() {
  local target_service=""
  
  while [[ $# -gt 0 ]]; do
    case $1 in
      -l|--list)
        list_services
        return 0
        ;;
      -h|--help)
        show_help
        return 0
        ;;
      -*)
        log_error "Unknown option: $1"
        show_help
        return 1
        ;;
      *)
        if [ -z "$target_service" ]; then
          target_service="$1"
        else
          log_error "Multiple services specified. Please specify only one service."
          show_help
          return 1
        fi
        ;;
    esac
    shift
  done
  
  # Check if we're in the right directory
  if [ ! -d "packages" ]; then
    log_error "packages/ directory not found. Are you in the project root?"
    return 1
  fi
  
  # Check if pipenv is available
  if ! command -v pipenv &> /dev/null; then
    log_error "pipenv not found. Please install pipenv first."
    return 1
  fi
  
  if [ -n "$target_service" ]; then
    log "🎯 Building specific service: $target_service"
    build_specific "$target_service"
  else
    log "🔄 Building all services sequentially"
    build_sequential
  fi
}

main "$@"
