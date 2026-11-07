#!/usr/bin/env bash
# Add a release tag to the reviewed commit, without moving main or any old tag.
set -euo pipefail

if [[ $# -ne 2 || ! "$1" =~ ^beta-[0-9]+\.[0-9]+\.[0-9]+$ || ! "$2" =~ ^[0-9a-f]{40}$ ]]; then
    echo 'usage: tag-beta-once.sh beta-X.Y.Z <40-character-commit>' >&2
    exit 2
fi

tag="$1"
target="$2"
ref="refs/tags/$tag"

# The tagging workflow must be the only commit after the reviewed baseline.
[[ "$(git rev-parse --verify HEAD^)" == "$target" ]] || {
    echo 'Refusing: the reviewed baseline is not the parent commit' >&2
    exit 1
}
[[ "$(git cat-file -t "$target")" == commit ]] || {
    echo 'Refusing: the target is not a commit' >&2
    exit 1
}
[[ -z "$(git status --porcelain)" ]] || {
    echo 'Refusing: the checkout has local changes' >&2
    exit 1
}
remote_main="$(git ls-remote origin refs/heads/main | cut -f1)"
[[ -n "$remote_main" && "$remote_main" == "$(git rev-parse HEAD)" ]] || {
    echo 'Refusing: origin/main moved' >&2
    exit 1
}

remote_tag="$(git ls-remote --tags --refs origin "$ref" | cut -f1)"
if [[ -n "$remote_tag" ]]; then
    # An annotated tag has a different object ID from its target commit.
    peeled="$(git ls-remote --tags origin "${ref}^{}" | cut -f1)"
    [[ -n "$peeled" ]] || peeled="$remote_tag"
    [[ "$peeled" == "$target" ]] || {
        echo "Refusing: $tag already points to a different commit" >&2
        exit 1
    }
    echo "$tag already marks $target"
    exit 0
fi

# No forced updates. If somebody creates the tag first, the push will fail.
git -c user.name='github-actions[bot]' \
    -c user.email='41898282+github-actions[bot]@users.noreply.github.com' \
    tag -a "$tag" "$target" -m "ZX-UX $tag: verified distribution baseline $target"
git push origin "$ref:$ref"

peeled="$(git ls-remote --tags origin "${ref}^{}" | cut -f1)"
[[ "$peeled" == "$target" ]] || {
    echo "Refusing: $tag did not reach the expected commit" >&2
    exit 1
}
echo "$tag -> $target"
