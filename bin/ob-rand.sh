#!/usr/bin/env bash

if [ -z "${DEBUG:-}" ]; then
  exec >> "meta/,rand.md"
fi

echo "## $(date)"
echo
echo "Generated on [[$(date +'%Y-%m-%d')]]"
echo
echo "### Permanet"
echo

(
rg -l '#zettel/(literature|permanent|index)'
fd '♯ *'
) | sort -R | head -10 | sed -e 's;.*/\(.*\)\.md;- [ ] [[\1]];'

echo

echo "### Fleeting"
echo

rg -l '#zettel/fleeting' |\
  sort -R | head -10 | sed -e 's;.*/\(.*\)\.md;- [ ] [[\1]];'

echo
