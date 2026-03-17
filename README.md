# Kubernetes Security Policies (OPA Gatekeeper)

This repository manages security policies for Kubernetes using **OPA Gatekeeper**. It allows for the generation, validation, 
and deployment of Rego-based policies as ConstraintTemplates and Constraints.

This project is a fork of [raspbernetes/k8s-security-policies](https://github.com/raspbernetes/k8s-security-policies).

## Prerequisites

Before using this repository, ensure you have the following installed:

*   **Kubernetes Cluster** with [OPA Gatekeeper](https://open-policy-agent.github.io/gatekeeper/website/docs/install/) installed.
*   `kubectl` configured to talk to your cluster.

## Repository Structure
*   `policies/`: Contains the source Rego policy files.
*   `converted-policies/`: Destination folder for generated Kubernetes YAML manifests (ConstraintTemplates and Constraints).
*   `konstraint`: Local binary of the konstraint tool (optional if installed globally).
*   `*.sh`: Helper scripts for normalization and deployment.

## Workflow

Follow these steps to generate and deploy policies to your cluster.

### 1. Develop or Update Policies
Add your new `.rego` files or update existing ones in the `policies/` directory.

### 2. Generate Manifests
Use `konstraint` to convert the Rego policies into Kubernetes Custom Resource Definitions (ConstraintTemplates and Constraints).

```bash
# Assuming the binary is in the root folder, otherwise use 'konstraint'
./konstraint create . --output converted-policies
```

### 3. Normalize Naming Conventions
The raw output from `konstraint` may contain naming conventions (like dots in names) that cause issues or violate specific validation rules. 
Run the fix script to replace dots with underscores and adjust usage of capitalization.

```bash
chmod +x fix_yaml_names.sh
./fix_yaml_names.sh
```

### 4. Deploy to Cluster
Use the deployment script to apply the policies. This script handles the order of operations:
1. It applies the **Templates** (CRDs) first.
2. It waits for the CRDs to be registered.
3. It applies the **Constraints** to enforce the policies.

```bash
chmod +x deploy-polices.sh
./deploy-polices.sh converted-policies
```

## Scripts Description

*   `fix_yaml_names.sh`: Iterates through generated YAMLs to sanitize `metadata.name` and `kind` fields (e.g., changing `Cis.1.2.1` to `cis_1_2_1`), ensuring compatibility with Kubernetes resource naming limits.
*   `deploy-polices.sh`: A wrapper around `kubectl apply` that ensures ConstraintTemplates are established before Constraints are applied, preventing "resource not found" errors.

