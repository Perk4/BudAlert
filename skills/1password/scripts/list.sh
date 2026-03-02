#!/bin/bash
# List items in a 1Password vault
# Usage: ./list.sh [vault]

VAULT="${1:-prtl}"

if ! command -v op &> /dev/null; then
    echo "Error: op not installed. Run ./install.sh first" >&2
    exit 1
fi

op item list --vault "$VAULT" --format=json | jq -r '.[] | "\(.title) (\(.category))"'
