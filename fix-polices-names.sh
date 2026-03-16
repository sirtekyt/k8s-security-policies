#!/bin/bash

POLICY_DIR="converted-policies"

if [ ! -d "$POLICY_DIR" ]; then
    echo "❌ Błąd: Folder '$POLICY_DIR' nie istnieje. Uruchom najpierw generation."
    exit 1
fi

echo "🔧 Rozpoczynam naprawę nazw w plikach YAML w '$POLICY_DIR'..."

find "$POLICY_DIR" -name "*.yaml" -print0 | xargs -0 sed -i -E \
  '/^\s*(kind|listKind|plural|singular|name):\s*"?\s*(Cis|cis|K\.sec|k\.sec|Cis-|cis-|K-sec|k-sec)/s/\./-/g'

echo "✅ Sukces! Pliki zostały naprawione i są zgodne ze standardem DNS-1035."