#!/usr/bin/env python3
import os
import re
import sys
from pathlib import Path

REGO_EXT = ".rego"

INJECTED_LIBRARY = """
# --- INJECTED LIBRARY CODE ---
flag_contains_string(cmds, key, value) {
    some i
    contains(cmds[i], key)
    contains(cmds[i], value)
}
contains_element(list, element) {
    list[_] == element
}
"""

TEMPLATE_HEADER = """apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: {template_name}
spec:
  crd:
    spec:
      names:
        kind: {kind}
      validation:
        openAPIV3Schema:
          type: object
          properties:
            key:
              type: string
            requiredValue:
              type: string
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
{rego_code}
"""

CONSTRAINT_HEADER = """apiVersion: constraints.gatekeeper.sh/v1beta1
kind: {kind}
metadata:
  name: {constraint_name}
spec:
  parameters:
    key: "{key}"
    requiredValue: "{requiredValue}"
  match:
    kinds:
      - apiGroups: ["*"]
        kinds: ["*"]
"""

def extract_default_params(rego_code):
    match = re.search(r'default_parameters\s*=\s*{([^}]*)}', rego_code, re.DOTALL)
    defaults = {"key": "", "requiredValue": ""}
    if match:
        params_content = match.group(1)
        k_match = re.search(r'"key"\s*:\s*"([^"]+)"', params_content)
        if k_match: defaults["key"] = k_match.group(1)
        v_match = re.search(r'"(requiredValue|includeValue)"\s*:\s*"([^"]+)"', params_content)
        if v_match: defaults["requiredValue"] = v_match.group(2)
    return defaults

def clean_name(name):
    return re.sub(r'[^a-zA-Z0-9]', '', name).lower()

def transform_rego_code(rego_code):
    lines = rego_code.splitlines()
    new_lines = []

    # Lista regexów dla różnych zasobów
    mappings = [
        (re.compile(r'kubernetes\.pods\[\s*(\w+)\s*\]'), "input.review.object"),
        (re.compile(r'kubernetes\.clusterroles\[\s*(\w+)\s*\]'), "input.review.object"),
        (re.compile(r'kubernetes\.roles\[\s*(\w+)\s*\]'), "input.review.object"),
        (re.compile(r'kubernetes\.serviceaccounts\[\s*(\w+)\s*\]'), "input.review.object"),
        # NOWE: Obsługa RoleBinding i ClusterRoleBinding (Naprawa błędu cis511)
        (re.compile(r'kubernetes\.rolebindings\[\s*(\w+)\s*\]'), "input.review.object"),
        (re.compile(r'kubernetes\.clusterrolebindings\[\s*(\w+)\s*\]'), "input.review.object"),
    ]

    re_container = re.compile(r'kubernetes\.(?:apiserver|containers)\[\s*(\w+)\s*\]')

    for line in lines:
        if "import data.lib.kubernetes" in line: continue
        if "kind =" in line and "input.review" in line: continue
        if "name =" in line and "input.review" in line: continue

        # Jeśli linia zawiera definicję msg, usuwamy ją (zastąpimy bezpieczną na końcu)
        if "msg =" in line or "msg :=" in line:
            continue

        # Sprawdzamy mapowania zasobów
        matched = False
        for pattern, replacement in mappings:
            m = pattern.search(line)
            if m:
                var_name = m.group(1)
                new_lines.append(f"        {var_name} := {replacement}")
                matched = True
                break
        if matched: continue

        # Mapowanie kontenerów
        m = re_container.search(line)
        if m:
            var_name = m.group(1)
            new_lines.append(f"        {var_name} := input.review.object.spec.containers[_]")
            new_lines.append(f"        commands := object.get({var_name}, \"command\", [])")
            continue

        # Zamiany funkcji i zmiennych
        line = line.replace("kubernetes.flag_contains_string", "flag_contains_string")
        line = line.replace("kubernetes.contains_element", "contains_element")
        line = re.sub(r'\w+\.command', 'commands', line)

        if "object.union(default_parameters, kubernetes.parameters)" in line:
            line = "    params := object.union(default_parameters, input.parameters)"

        new_lines.append(line)

    # Dodajemy bezpieczne msg na końcu reguły
    final_lines = []
    for line in new_lines:
        if line.strip() == "}":
            final_lines.append('        msg := sprintf("CIS Violation: Resource <%v> violates policy", [input.review.object.metadata.name])')
            final_lines.append("}")
        else:
            final_lines.append(line)

    return "\n".join(final_lines) + "\n" + INJECTED_LIBRARY

def rego_to_template_and_constraint(rego_path, output_dir):
    try:
        raw_rego = Path(rego_path).read_text(encoding='utf-8')
        base_clean = clean_name(Path(rego_path).stem)
        if "test" in base_clean: return

        template_name = base_clean
        kind = base_clean.capitalize()
        if kind.lower() != template_name: kind = template_name.upper()

        final_rego = transform_rego_code(raw_rego)
        params = extract_default_params(raw_rego)

        indented_lines = ["        " + line if line.strip() else "" for line in final_rego.splitlines()]
        rego_code_indented = "\n".join(indented_lines)

        template_yaml = TEMPLATE_HEADER.format(template_name=template_name, kind=kind, rego_code=rego_code_indented)
        constraint_yaml = CONSTRAINT_HEADER.format(kind=kind, constraint_name=f"{template_name}-example", key=params["key"], requiredValue=params["requiredValue"])

        (output_dir / f"{template_name}-template.yaml").write_text(template_yaml, encoding='utf-8')
        (output_dir / f"{template_name}-constraint.yaml").write_text(constraint_yaml, encoding='utf-8')
        print(f"✅ OK: {kind}")

    except Exception as e:
        print(f"❌ BŁĄD {rego_path}: {e}")

def main():
    src_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    output_dir = src_dir / "converted-policies-v7"
    output_dir.mkdir(exist_ok=True)
    print(f"🚀 Generowanie V7 (RBAC Fix) z: {src_dir}")
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith(REGO_EXT):
                rego_to_template_and_constraint(Path(root)/file, output_dir)
    print(f"\n✨ Gotowe! Folder: {output_dir}")

if __name__ == "__main__":
    main()