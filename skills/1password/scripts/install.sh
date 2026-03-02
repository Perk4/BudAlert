#!/bin/bash
# Install 1Password CLI (op)
# Run this once per container start

set -e

OP_VERSION="${OP_VERSION:-2.30.0}"

if command -v op &> /dev/null; then
    echo "✅ op already installed: $(op --version)"
    exit 0
fi

echo "Installing 1Password CLI v${OP_VERSION}..."

cd /tmp
curl -sSfLO "https://cache.agilebits.com/dist/1P/op2/pkg/v${OP_VERSION}/op_linux_amd64_v${OP_VERSION}.zip"
unzip -o "op_linux_amd64_v${OP_VERSION}.zip" -d op_extract
mv op_extract/op /usr/local/bin/
chmod +x /usr/local/bin/op
rm -rf "op_linux_amd64_v${OP_VERSION}.zip" op_extract

echo "✅ op installed: $(op --version)"

# Verify auth
if [ -n "$OP_SERVICE_ACCOUNT_TOKEN" ]; then
    echo "✅ Service account authenticated"
    op vault list --format=json | jq -r '.[].name' | while read vault; do
        echo "   - Vault: $vault"
    done
else
    echo "⚠️  OP_SERVICE_ACCOUNT_TOKEN not set"
fi
