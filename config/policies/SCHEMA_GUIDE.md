# Policy Configuration Schema Guide

## Overview

This directory contains JSON Schema definitions for CIAF-LCM policy configuration files. Schemas provide:

- **Type Safety**: Validation ensures YAML files conform to expected structure
- **IDE Support**: Autocomplete, error checking, and documentation in VS Code
- **Documentation**: Clear reference of all valid properties and their constraints
- **Prevents Linting Confusion**: Distinguishes CIAF policy files from other formats (e.g., Aerleon)

## Files

### `schema.json`
Schema for `default_policies.yaml`. Defines structure for:
- Tenant isolation policy
- Department isolation policy
- Environment access controls
- Data classification levels
- Business hours policy
- Payment thresholds
- Email domain allowlists
- Rate limiting
- Change management
- Audit and compliance settings

### `sensitive_actions_schema.json`
Schema for `sensitive_actions.yaml`. Defines structure for:
- Sensitive action definitions with risk levels
- PAM elevation requirements
- Approval workflows
- Action categorization
- Risk level defaults

## Using Schemas

### In VS Code

The `.vscode/settings.json` file automatically associates these schemas with their YAML files. When you open a policy file, VS Code will:

1. **Validate** the YAML structure against the schema
2. **Highlight errors** for invalid properties or values
3. **Provide autocomplete** for valid keys and values
4. **Show documentation** for each field

### Command Line Validation

Validate a policy file using `ajv-cli`:

```bash
npm install -g ajv-cli

# Validate default policies
ajv validate -s ciaf_agents/config/policies/schema.json -d ciaf_agents/config/policies/default_policies.yaml

# Validate sensitive actions
ajv validate -s ciaf_agents/config/policies/sensitive_actions_schema.json -d ciaf_agents/config/policies/sensitive_actions.yaml
```

Or using Python:

```python
import json
import yaml
from jsonschema import validate, ValidationError

# Load schema and data
with open('ciaf_agents/config/policies/schema.json') as f:
    schema = json.load(f)

with open('ciaf_agents/config/policies/default_policies.yaml') as f:
    data = yaml.safe_load(f)

# Validate
try:
    validate(instance=data, schema=schema)
    print("✓ Validation successful")
except ValidationError as e:
    print(f"✗ Validation error: {e.message}")
```

### In CI/CD Pipeline

Add validation to your pipeline:

```yaml
# .github/workflows/validate-policies.yml
name: Validate Policies

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install validation tools
        run: pip install jsonschema pyyaml
      
      - name: Validate default policies
        run: |
          python -c "
          import json
          import yaml
          from jsonschema import validate
          
          with open('ciaf_agents/config/policies/schema.json') as f:
              schema = json.load(f)
          with open('ciaf_agents/config/policies/default_policies.yaml') as f:
              data = yaml.safe_load(f)
          
          validate(instance=data, schema=schema)
          print('✓ default_policies.yaml is valid')
          "
      
      - name: Validate sensitive actions
        run: |
          python -c "
          import json
          import yaml
          from jsonschema import validate
          
          with open('ciaf_agents/config/policies/sensitive_actions_schema.json') as f:
              schema = json.load(f)
          with open('ciaf_agents/config/policies/sensitive_actions.yaml') as f:
              data = yaml.safe_load(f)
          
          validate(instance=data, schema=schema)
          print('✓ sensitive_actions.yaml is valid')
          "
```

## Schema Concepts

### Policy Objects

Each policy is a top-level object with:
- **enabled**: (boolean) Whether the policy is active
- **description**: (string) Human-readable description
- Policy-specific properties as needed

Example:
```yaml
tenant_isolation:
  enabled: true
  description: "Prevent cross-tenant data access"
  enforcement: hard
  exceptions: []
```

### Enumerations

Some fields have restricted values (enums):
- `enforcement`: Must be "hard", "soft", or "audit"
- `risk_level`: Must be "low", "medium", "high", or "critical"
- Days of week: "monday" through "sunday"

### Nested Structures

Complex policies use nested objects:
```yaml
data_classification:
  enabled: true
  levels:
    public:
      clearance_required: 0
    confidential:
      clearance_required: 2
      require_elevation: true
```

### Arrays

Lists of items use YAML array syntax:
```yaml
sensitive_actions:
  - action: approve_payment
    risk_level: high
    require_elevation: true
  - action: delete_record
    risk_level: critical
    require_dual_approval: true
```

## Extending Schemas

To add a new policy:

1. **Define the schema** in `schema.json`:
   ```json
   "new_policy": {
     "type": "object",
     "description": "Description of the policy",
     "properties": {
       "enabled": { "type": "boolean" },
       ...
     },
     "required": ["enabled"]
   }
   ```

2. **Add to additionalProperties** list in the main schema

3. **Document** the new policy in this guide

4. **Test** validation with sample configuration

## Benefits for System Design

### 1. **Clear Contracts**
The schema acts as a contract between configuration producers and consumers. Everyone knows the expected structure.

### 2. **IDE Integration**
Developers get immediate feedback while editing, reducing errors before deployment.

### 3. **Automated Validation**
Configuration can be validated in CI/CD, preventing invalid configs from reaching production.

### 4. **Self-Documenting**
The schema is a machine-readable specification that serves as API documentation.

### 5. **Type Safety**
Python code can be generated from schemas, providing typed configuration objects.

### 6. **Version Control**
Schema changes can be reviewed and tracked alongside configuration changes.

## Related Concepts

- **OpenAPI Schema**: Similar pattern used in REST APIs
- **JSON Schema**: The standard used here (draft-07)
- **Configuration as Code**: Treating configuration like source code with validation
- **Infrastructure as Code (IaC)**: Similar validation patterns used in Terraform, CloudFormation

## References

- [JSON Schema Official Documentation](https://json-schema.org/)
- [JSON Schema Validation Tools](https://json-schema.org/tools.html)
- [VS Code YAML Extension](https://marketplace.visualstudio.com/items?itemName=redhat.vscode-yaml)
- [AJV JSON Schema Validator](https://ajv.js.org/)
