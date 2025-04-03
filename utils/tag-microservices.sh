#!/bin/bash
set -e

readonly tmp="/tmp/auguris"

rm -Rf $tmp && mkdir -p $tmp


for app_group in packages/*; do
    [ -d "$app_group" ] || continue

    for service in "$app_group"/*; do
        [ -d "$service" ] || continue

        app_group_name=$(basename "$app_group")
        service_name=$(basename "$service")

        echo "🔍 Processing: $app_group_name/$service_name"

        tag_pattern="${app_group_name}-${service_name}/v*"

        last_tag=$(git tag --list "$tag_pattern" | sort -V | tail -n 1)

        if [ -z "$last_tag" ]; then
            echo "🆕 No previous tag found for $app_group_name/$service_name. Starting from first commit..."
            commit_range="--all"
        else
            commit_range="${last_tag}..HEAD"
        fi

        commits=$(git log --pretty=format:"%H %s" $commit_range -- "packages/$app_group_name/$service_name/")
        if [ -z "$commits" ]; then
            echo "⚠️  No new commits for $app_group_name/$service_name. Skipping version bump."
            continue
        fi

        major=false
        minor=false
        patch=false

        while IFS= read -r line; do
            commit_hash=$(echo "$line" | awk '{print $1}')
            commit_msg=$(echo "$line" | cut -d' ' -f2-)

            if [[ "$commit_msg" =~ ^(feat|fix)(\(.+\))?! ]]; then
                major=true
            elif [[ "$commit_msg" =~ ^feat ]]; then
                minor=true
            elif [[ "$commit_msg" =~ ^fix ]]; then
                patch=true
            fi

            commit_body=$(git show -s --format=%b "$commit_hash")
            if echo "$commit_body" | grep -q "BREAKING CHANGE:"; then
                major=true
            fi
        done <<< "$commits"

        if ! $major && ! $minor && ! $patch; then
            echo "⚠️  No fix:, feat:, or BREAKING CHANGE commits. Skipping version bump for $app_group_name/$service_name."
            continue
        fi

        if [ -z "$last_tag" ]; then
            new_version="v0.1.0"
        else
            current_version=$(echo "$last_tag" | sed -E "s|${app_group_name}-${service_name}/v||")
            IFS='.' read -r major_v minor_v patch_v <<< "$current_version"

            if $major; then
                ((major_v++))
                minor_v=0
                patch_v=0
            elif $minor; then
                ((minor_v++))
                patch_v=0
            elif $patch; then
                ((patch_v++))
            fi

            new_version="v${major_v}.${minor_v}.${patch_v}"
        fi

        new_tag="${app_group_name}-${service_name}/${new_version}"
        git tag "$new_tag"
        echo "✅ Created new tag: $new_tag"

        mkdir -p "$tmp/$service"
        changelog_file="$service/CHANGELOG.md"
        echo -e "## ${new_version}\n" >> "$changelog_file"

        while IFS= read -r line; do
            commit_hash=$(echo "$line" | awk '{print $1}')
            commit_msg=$(echo "$line" | cut -d' ' -f2-)
            echo "- ${commit_msg} (${commit_hash:0:7})" >> "$changelog_file"
        done <<< "$commits"

        git add "$changelog_file"
        git commit -m "docs: update changelog for ${new_version}"

        echo "🚀 Version bump completed for $app_group_name/$service_name!"
    done
done
