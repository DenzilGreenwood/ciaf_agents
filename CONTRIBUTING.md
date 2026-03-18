# Contributing to CIAF-LCM Agentic Execution Boundaries

Thank you for your interest in contributing to the CIAF-LCM Agentic Execution Boundaries project! We welcome contributions from the community and appreciate your help in making this project better.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Making Changes](#making-changes)
5. [Testing](#testing)
6. [Code Standards](#code-standards)
7. [Documentation](#documentation)
8. [Submitting Changes](#submitting-changes)
9. [Reporting Issues](#reporting-issues)
10. [License](#license)

## Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please be respectful, professional, and constructive in all interactions.

- Be inclusive and respectful of different backgrounds and experiences
- Focus on what is best for the community and project
- Show empathy towards other community members
- Report inappropriate behavior to the project maintainers

## Getting Started

### Prerequisites

- Python 3.9 or higher
- git
- pip (Python package manager)

### Initial Setup

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/ciaf_agents.git
   cd ciaf_agents
   ```
3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/DenzilGreenwood/ciaf_agents.git
   ```

## Development Setup

### Create a Virtual Environment

```bash
# Using venv
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Install Dependencies

```bash
# Navigate to the project directory
cd ciaf_agents

# Install the package in editable mode with development dependencies
pip install -e ".[dev]"
```

### Verify Installation

```bash
# Run the verification script
python verify_installation.py

# Or run the basic tests
pytest tests/ -v
```

## Making Changes

### Create a Feature Branch

```bash
# Fetch the latest changes from upstream
git fetch upstream

# Create a new branch from main
git checkout -b feature/your-feature-name upstream/main
```

**Branch naming conventions:**
- `feature/description` — for new features
- `fix/description` — for bug fixes
- `docs/description` — for documentation improvements
- `test/description` — for test improvements
- `refactor/description` — for code refactoring

### Making Your Changes

1. Make your changes in focused, logical commits
2. Keep commits small and well-described
3. Reference issues when applicable in commit messages

**Example commit message:**
```
Add support for custom policy conditions

- Implement ConditionEvaluator interface
- Add tests for condition evaluation
- Update documentation with examples

Fixes #123
```

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run tests with coverage report
pytest tests/ --cov=src/ciaf_agents --cov-report=html

# Run specific test file
pytest tests/test_policy.py -v

# Run specific test function
pytest tests/test_policy.py::test_policy_evaluation -v
```

### Coverage Requirements

- Aim for at least 80% code coverage for new features
- All public APIs should be tested
- Test both success and failure paths

### Writing Tests

- Place tests in the `tests/` directory mirroring the source structure
- Use descriptive test names: `test_<function>_<scenario>_<expected_result>`
- Use fixtures for common setup (see `tests/conftest.py`)
- Mock external dependencies appropriately

Example test structure:
```python
def test_identity_creation_with_valid_data():
    """Test creating a valid identity."""
    identity = Identity(
        principal_id="agent-001",
        principal_type="agent",
        roles={"viewer"}
    )
    assert identity.principal_id == "agent-001"
    assert "viewer" in identity.roles
```

## Code Standards

### Python Style Guide

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) and enforce it with automated tools.

### Code Quality Tools

All code must pass the following checks:

#### Black (Code Formatting)

```bash
# Format all Python files
black src/ tests/

# Check formatting without modifying
black --check src/ tests/
```

#### isort (Import Sorting)

```bash
# Sort imports
isort src/ tests/

# Check import sorting
isort --check-only src/ tests/
```

#### Flake8 (Linting)

```bash
# Check code style
flake8 src/ tests/
```

#### mypy (Type Checking)

```bash
# Run type checker
mypy src/
```

### Type Hints

- Add type hints to all function signatures
- Use descriptive type hints (avoid `Any` when possible)
- Include return type hints

Example:
```python
def evaluate_policy(
    request: ActionRequest,
    iam_store: IAMStore
) -> PolicyDecision:
    """Evaluate a request against IAM policies."""
    ...
```

### Documentation Strings

- Use docstrings for all public classes and functions
- Follow Google-style docstring format

Example:
```python
def execute_action(
    request: ActionRequest,
    vault: EvidenceVault
) -> ExecutionResult:
    """Execute an authorized action and record evidence.

    Args:
        request: The action request to execute.
        vault: The evidence vault for recording outcomes.

    Returns:
        ExecutionResult containing decision and reason.

    Raises:
        AuthorizationError: If action is not authorized.
        ValueError: If request parameters are invalid.
    """
```

## Documentation

### Updating Documentation

- Keep documentation in sync with code changes
- Update relevant docs when modifying features
- Add examples for new public APIs
- Update the changelog for significant changes

### Documentation Standards

- Use clear, concise language
- Include code examples where helpful
- Link to related documentation
- Keep README.md up to date with major changes

### Changelog

Update [CHANGELOG.md](CHANGELOG.md) with:
- New features
- Bug fixes
- Breaking changes
- Deprecations

Format:
```markdown
## [Unreleased]

### Added
- New feature description

### Fixed
- Bug fix description

### Changed
- Breaking change description
```

## Submitting Changes

### Before You Submit

1. **Sync with upstream:**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run all tests locally:**
   ```bash
   pytest tests/ -v
   ```

3. **Check code quality:**
   ```bash
   black --check src/ tests/
   isort --check-only src/ tests/
   flake8 src/ tests/
   mypy src/
   ```

4. **Verify coverage:**
   ```bash
   pytest tests/ --cov=src/ciaf_agents
   ```

### Creating a Pull Request

1. Push your branch to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. Open a Pull Request on GitHub with:
   - Clear title describing the change
   - Description of what was changed and why
   - Reference to related issues (use `Fixes #123`)
   - Any relevant testing notes

3. **PR Title Format:**
   ```
   [Type] Short description
   ```
   Examples: `[Feature] Add custom policy conditions`, `[Fix] Resolve evidence chain validation bug`

4. **PR Description Template:**
   ```markdown
   ## Description
   Brief description of changes.

   ## Related Issues
   Fixes #123

   ## Changes Made
   - Change 1
   - Change 2

   ## Testing
   - How did you test this?
   - New test coverage?

   ## Checklist
   - [ ] Tests pass locally
   - [ ] Code follows style guidelines
   - [ ] Documentation updated
   - [ ] Changelog updated
   - [ ] No breaking changes (or documented)
   ```

### Review Process

- At least one maintainer review required
- All CI checks must pass
- Discussions and requested changes will be addressed
- Once approved, the PR will be merged

## Reporting Issues

### Bug Reports

When reporting a bug, please include:

1. **Description:** What is the issue?
2. **Steps to reproduce:** How can we reproduce it?
3. **Expected behavior:** What should happen?
4. **Actual behavior:** What actually happens?
5. **Environment:** Python version, OS, relevant dependencies
6. **Minimal example:** Code snippet that demonstrates the issue

Example:
```markdown
## Description
The evidence chain verification fails when a receipt is modified.

## Steps to Reproduce
1. Create an evidence vault
2. Record a receipt
3. Modify the receipt JSON
4. Call verify_chain()

## Expected Behavior
verify_chain() should detect the modification and return False.

## Actual Behavior
verify_chain() returns True despite the modification.

## Environment
- Python 3.11
- ciaf-agents 1.0.0
- macOS 13.0
```

### Feature Requests

When requesting a feature, please:

1. **Use the title:** `[Feature Request] Brief description`
2. **Describe the use case:** Why is this needed?
3. **Provide examples:** How would it be used?
4. **Suggest implementation:** How might it be implemented?

## Security Considerations

### Security Issues

**Do not** open a public issue for security vulnerabilities. Please report security issues responsibly by:

1. Emailing security details to the project maintainers
2. Include a description of the vulnerability
3. Include potential impact
4. Avoid public disclosure until a fix is available

### Security Review

When submitting cryptographic or security-related code:

- Use well-established libraries (e.g., `hmac`, `hashlib`)
- Avoid implementing custom crypto
- Include security reviews in the PR description
- Reference security considerations in comments

## License

By contributing to this project, you agree that your contributions will be licensed under the same BUSL-1.1 license as the project.

Please review [LICENSE.md](LICENSE.md) for complete license details.

## Questions?

If you have questions:

1. Check the [API Reference](docs/API_REFERENCE.md)
2. Review [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
3. Open an issue with your question
4. Check existing discussions and issues

## Additional Resources

- [Whitepaper: Agentic Execution Boundaries](docs/whitepaper_agentic_execution_boundaries.md)
- [Architecture Documentation](docs/architecture.md)
- [Implementation Guide](docs/implementation_guide.md)
- [API Reference](docs/API_REFERENCE.md)
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md)

Thank you for contributing! 🎉
