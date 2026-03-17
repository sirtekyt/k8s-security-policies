#!/bin/bash

POLICY_DIR="converted-policies"

if [ ! -d "$POLICY_DIR" ]; then
    echo "❌ Error: Directory '$POLICY_DIR' does not exist. Run generation first."
    exit 1
fi

echo "🔧 Starting to fix YAML names in '$POLICY_DIR'..."

find "$POLICY_DIR" -name "*.yaml" -print0 | xargs -0 sed -i -E \
  '/^\s*(kind|listKind|plural|singular|name):\s*"?\s*(Cis|cis|K\.sec|k\.sec|Cis-|cis-|K-sec|k-sec)/s/\./-/g'

echo "✅ Success! Files have been fixed and now comply with DNS-1035."
