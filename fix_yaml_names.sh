#!/bin/bash
# Skrypt masowo poprawiający kind i name w plikach YAML wygenerowanych przez konstraint
# Zamienia kropki na podkreślenia, ustawia wielkość liter: kind wielkie (tylko dla constraintów i spec.crd.spec.names.kind), name małe

for file in converted-policies/*.yaml; do
  # Pobierz oryginalną wartość name
  orig_name=$(grep '^  name:' "$file" | awk '{print $2}')
  # Zamień kropki na podkreślenia, małe litery
  new_name=$(echo "$orig_name" | tr '.' '_' | tr '[:upper:]' '[:lower:]')
  # Zamień w pliku
  sed -i "s/^  name: .*/  name: $new_name/" "$file"

  # Jeśli to constraint (nie template), zmień kind na wielkie litery i podkreślenia
  if grep -q '^kind:' "$file" && ! grep -q '^kind: ConstraintTemplate' "$file"; then
    orig_kind=$(grep '^kind:' "$file" | awk '{print $2}')
    new_kind=$(echo "$orig_kind" | tr '.' '_' | tr '[:lower:]' '[:upper:]')
    sed -i "s/^kind: .*/kind: $new_kind/" "$file"
  fi

  # Jeśli to template, popraw tylko spec.crd.spec.names.kind
  if grep -q '^kind: ConstraintTemplate' "$file"; then
    orig_spec_kind=$(grep '        kind:' "$file" | awk '{print $2}')
    if [ -n "$orig_spec_kind" ]; then
      new_spec_kind=$(echo "$orig_spec_kind" | tr '.' '_' | tr '[:lower:]' '[:upper:]')
      sed -i "s/        kind: .*/        kind: $new_spec_kind/" "$file"
    fi
  fi

done
