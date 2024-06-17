#!/bin/sh

PREV_VERSION=$(changie latest | cut -c 2-)
NEW_VERSION=$(changie next auto | cut -c 2-)

NO_RELEASE=$(echo "$NEW_VERSION" | grep "unreleased changes found")
if [ "$NO_RELEASE" != "" ]; then
  echo "Nothing to release."
  exit 1
fi

echo "Upgrading from $PREV_VERSION to $NEW_VERSION."

changie merge
hatch version "$NEW_VERSION"

CHANGES_TEXT=$(cat ".changes/$NEW_VERSION.md")
COMMIT_MSG="version: $NEW_VERSION\n\n$CHANGES_TEXT"

git add .changes CHANGELOG.md
echo "$COMMIT_MSG" | git commit --file -

