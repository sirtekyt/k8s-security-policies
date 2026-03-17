#!/bin/bash

if [ -z "$1" ]; then
  echo "Error: Please provide directory path."
  exit 1
fi

TARGET_DIR="$1"
if [ ! -d "$TARGET_DIR" ]; then
  echo "Error: Directory '$TARGET_DIR' does not exist."
  exit 1
fi

cd "$TARGET_DIR" || exit 1

if [ -f "kubernetes-template.yaml" ]; then
    echo "Library..."
    kubectl apply -f kubernetes-template.yaml
    sleep 1
fi

echo "📄 Templates..."
shopt -s nullglob
templates=(*-template.yaml template_*.yaml)

if [ ${#templates[@]} -gt 0 ]; then
    for file in "${templates[@]}"; do
        [ "$file" == "kubernetes-template.yaml" ] && continue
        echo "   -> $file"
        kubectl apply -f "$file"
    done
fi

echo "Pause (2s) for CRD registration..."
sleep 2

echo "Constraints..."
constraints=(*-constraint.yaml constraint_*.yaml)

if [ ${#constraints[@]} -gt 0 ]; then
    for file in "${constraints[@]}"; do
        echo "   -> $file"
        if ! kubectl apply -f "$file"; then
            echo "Retry (1s)..."
            sleep 1
            kubectl apply -f "$file"
        fi
    done
fi

shopt -u nullglob
echo "✅ Done."
