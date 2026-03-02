#!/bin/bash
# Get a secret from 1Password
# Usage: ./get.sh <item> [field] [vault]
#
# Examples:
#   ./get.sh Brave                    # Auto-finds api-key field
#   ./get.sh GitHub api-key           # Specific field
#   ./get.sh Discord-Breth api-key    # Bot token
#   ./get.sh Convex api-key prtl      # Specify vault

ITEM="$1"
FIELD="${2:-}"
VAULT="${3:-prtl}"

if [ -z "$ITEM" ]; then
    echo "Usage: ./get.sh <item> [field] [vault]" >&2
    echo "Examples:" >&2
    echo "  ./get.sh Brave" >&2
    echo "  ./get.sh GitHub api-key" >&2
    echo "  ./get.sh Discord-Breth" >&2
    exit 1
fi

if ! command -v op &> /dev/null; then
    echo "Error: op not installed. Run ./install.sh first" >&2
    exit 1
fi

# If field specified, try it directly
if [ -n "$FIELD" ]; then
    SECRET=$(op read "op://${VAULT}/${ITEM}/${FIELD}" 2>/dev/null)
    if [ -n "$SECRET" ]; then
        echo "$SECRET"
        exit 0
    fi
fi

# Try common field names
for field in api-key credential token password api_key apikey key secret; do
    SECRET=$(op read "op://${VAULT}/${ITEM}/${field}" 2>/dev/null)
    if [ -n "$SECRET" ]; then
        echo "$SECRET"
        exit 0
    fi
done

# Failed - show available fields
echo "Error: Could not find secret in item '${ITEM}'" >&2
echo "Available fields:" >&2
op item get "$ITEM" --vault "$VAULT" --format=json 2>/dev/null | jq -r '.fields[]?.label // empty' | head -10 >&2
exit 1
