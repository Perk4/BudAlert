# 1Password Skill

Read secrets from 1Password vaults using the `op` CLI.

## What is `op`?

`op` is the 1Password command-line tool. It lets you read/write secrets from your 1Password vaults programmatically - like `curl` for your password manager.

## Prerequisites

- `OP_SERVICE_ACCOUNT_TOKEN` env var set (configured in OpenClaw config)
- Service account must have access to the target vault

## Quick Start

```bash
# Install op CLI (run once per container start)
./scripts/install.sh

# List items in vault
op item list --vault prtl

# Read a specific secret
op read "op://prtl/Brave/api-key"

# Get full item as JSON
op item get "GitHub" --vault prtl --format json
```

## Secret Reference Format

1Password uses URI format: `op://vault/item/field`

Examples:
```bash
op read "op://prtl/GitHub/api-key"         # API key field
op read "op://prtl/Discord-Breth/api-key"  # Bot token
op read "op://prtl/Convex/api-key"         # Access token
```

## Helper Scripts

### Install (run on container start)
```bash
./scripts/install.sh
```

### List all items
```bash
./scripts/list.sh [vault]
# Default vault: prtl
```

### Get a secret
```bash
./scripts/get.sh <item> [field] [vault]
# Examples:
./scripts/get.sh Brave           # Auto-finds api-key field
./scripts/get.sh GitHub api-key
./scripts/get.sh Discord-Breth
```

## Available Secrets (prtl vault)

| Item | Description |
|------|-------------|
| GitHub | GitHub PAT |
| Brave | Brave Search API key |
| Convex | Convex access token |
| AgentMail | AgentMail API key |
| Discord-Breth | Discord bot token |
| Discord-Lega | Discord bot token |

## Environment Variable Injection

To use 1Password secrets as env vars at runtime:

```bash
# Single secret
export GITHUB_TOKEN=$(op read "op://prtl/GitHub/api-key")

# Or use op's built-in env injection
op run --env-file=.env.1p -- your-command
```

## Troubleshooting

**"op: not found"** → Run `./scripts/install.sh`

**"could not resolve vault"** → Check service account has vault access in 1Password dashboard

**"could not resolve item"** → Item name is case-sensitive, check with `op item list`

## Notes

- The `op` CLI binary lives in `/usr/local/bin/op`
- Container restarts wipe it (ephemeral filesystem)
- Token is persisted in OpenClaw config (`env.OP_SERVICE_ACCOUNT_TOKEN`)
