#!/bin/bash

# 1. Sprawdzenie parametrów
if [ -z "$1" ]; then
  echo "❌ Błąd: Podaj ścieżkę do folderu."
  exit 1
fi

TARGET_DIR="$1"
if [ ! -d "$TARGET_DIR" ]; then
  echo "❌ Błąd: Folder '$TARGET_DIR' nie istnieje."
  exit 1
fi

cd "$TARGET_DIR" || exit 1
echo "🚀 Szybkie wdrażanie z: $TARGET_DIR"

# --- KROK A: Biblioteka ---
if [ -f "kubernetes-template.yaml" ]; then
    echo "📦 Biblioteka..."
    kubectl apply -f kubernetes-template.yaml
    # Czekamy tylko 1s
    sleep 1
fi

# --- KROK B: Szablony (Templates) ---
echo "📄 Szablony..."
shopt -s nullglob
templates=(*-template.yaml template_*.yaml)

if [ ${#templates[@]} -gt 0 ]; then
    for file in "${templates[@]}"; do
        [ "$file" == "kubernetes-template.yaml" ] && continue
        echo "   -> $file"
        kubectl apply -f "$file"
    done
fi

# --- KROK C: Minimalna pauza ---
echo "⏳ Szybka pauza (2s) na rejestrację CRD..."
sleep 2

# --- KROK D: Ograniczenia (Constraints) ---
echo "🔒 Ograniczenia..."
constraints=(*-constraint.yaml constraint_*.yaml)

if [ ${#constraints[@]} -gt 0 ]; then
    for file in "${constraints[@]}"; do
        echo "   -> $file"
        if ! kubectl apply -f "$file"; then
            echo "   ⚠️ Retry (1s)..."
            sleep 1
            kubectl apply -f "$file"
        fi
    done
fi

shopt -u nullglob
echo "✅ Gotowe."