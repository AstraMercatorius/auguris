#!/bin/bash

app_group_name="market-data"
service_name="feature-engineering"
tag_pattern="${app_group_name}-${service_name}/v*"
last_tag=$(git tag --list "$tag_pattern" | sort -V | tail -n 1)

# Extract and clean the version string
current_version=$(echo "$last_tag" | sed -E "s|${app_group_name}-${service_name}/v||" | tr -d '\r\n[:space:]')

# Split the version
IFS='.' read -r major_v minor_v patch_v <<< "$current_version"

# Clean the patch number and force numeric context
# patch_v=${patch_v:-0}
# patch_v=$((10#$patch_v))   # This removes any leading zeros or invalid numeric formats

# Increment
((patch_v++))

# Output result
echo "New patch version: $major_v.$minor_v.$patch_v"
