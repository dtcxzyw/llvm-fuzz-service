#!/bin/bash
set -euo pipefail
shopt -s inherit_errexit

echo "LLVM_REVISION=$(git -C llvm-project rev-parse HEAD)" >> $GITHUB_ENV

COMMIT_URL=$GITHUB_PATCH_ID
PATCH_URL=$GITHUB_PATCH_ID.diff

echo "Downloading patch $PATCH_URL..."
wget $PATCH_URL -O patch.diff
git -C llvm-project apply --exclude=*/test/* ../patch.diff
PATCH_SHA256=$(sha256sum patch.diff | sed 's/\|/ /'|awk '{print $1}')
echo "COMMIT_URL=$COMMIT_URL" >> $GITHUB_ENV
echo "PATCH_SHA256=$PATCH_SHA256" >> $GITHUB_ENV
