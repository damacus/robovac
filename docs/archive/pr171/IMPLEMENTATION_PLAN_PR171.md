# Implementation Plan: PR #171 - Battery Deprecation & Model Validation

## PR Review Summary

### Changes from PR #171

1. **Battery Deprecation Fixes** (HA 2026.8 compatibility)
   - Remove `VacuumEntityFeature.BATTERY` from 35+ vacuum models
   - Remove deprecated `_attr_battery_level` from vacuum.py entity
   - Maintain existing battery sensor functionality (no breaking changes)

2. **Error Handling Improvements**
   - Fix typo: "Laser sesor stuck" → "Laser sensor stuck"
   - Add `getErrorMessageWithContext()` function with actionable troubleshooting
   - Enhanced error messages with user guidance

3. **Model Validation Tools**
   - `model_validator.py`: Library module with series detection (C, G, L, X series)
   - `model_validator_cli.py`: Standalone CLI tool for users
   - Automatic unsupported model suggestions
   - Series-specific troubleshooting guides

### Code Review Findings

**Style Issues:**

- Generally clean, follows Python conventions
- Some flake8 violations were fixed in PR (whitespace, line breaks)
- Type hints need to be added for new functions

**Conciseness:**

- Model validator has good abstraction with series detection
- Error context function could be more modular
- CLI tool has appropriate separation from library

**Readability:**

- Clear function names and structure
- Some functions are long and could benefit from decomposition
- Documentation is comprehensive

**Maintainability:**

- Series detection makes adding new models easier
- Model list is centralized (good)
- CLI tool has fallback for standalone usage (good)
- Tests needed for all new functionality

---

## Implementation Plan

### Phase 1: Battery Deprecation (Test-First)

#### Step 1.1: Write Failing Tests for Battery Feature Removal

**Task:** Create test file for battery feature validation

**File:** `tests/test_vacuum/test_battery_feature_removal.py`

**Test Cases:**

```python
# Test 1: Verify VacuumEntityFeature.BATTERY is NOT in homeassistant_features for all models
# Test 2: Verify battery command mappings still exist (backward compatibility)
# Test 3: Verify battery level property is removed from vacuum entity
# Test 4: Verify battery sensor still works independently
```

**Implementation Details:**

- Import all vacuum models from `custom_components/robovac/vacuums`
- Iterate through all T* models
- Assert `VacuumEntityFeature.BATTERY` not in `homeassistant_features`
- Assert `RobovacCommand.BATTERY` still exists in commands
- Verify vacuum entity does not have `_attr_battery_level` attribute

**Run tests (should fail):**

```bash
task test tests/test_vacuum/test_battery_feature_removal.py
```

#### Step 1.2: Remove Battery Feature from Vacuum Models

**Task:** Remove `VacuumEntityFeature.BATTERY` from all 35 vacuum model files

**Files to modify:** All vacuum models in `custom_components/robovac/vacuums/T2*.py`

**Pattern to apply:**

```python
# BEFORE:
homeassistant_features = (
    VacuumEntityFeature.BATTERY
    | VacuumEntityFeature.FAN_SPEED
    | ...
)

# AFTER:
homeassistant_features = (
    VacuumEntityFeature.FAN_SPEED
    | ...
)
```

**Models to update:** (35 files)

- T2080, T2103, T2117, T2118, T2119, T2120, T2123, T2128, T2130, T2132
- T2150, T2181, T2190, T2192, T2193, T2194, T2250, T2251, T2252, T2253
- T2254, T2255, T2259, T2261, T2262, T2267, T2268, T2270, T2272, T2273
- T2275, T2276, T2277, T2278, T2320

**Implementation:**

- Use multi_edit tool for batch updates
- Preserve all other features and command mappings
- Maintain code formatting and structure

**Run tests (should pass):**

```bash
task test tests/test_vacuum/test_battery_feature_removal.py
```

#### Step 1.3: Remove _attr_battery_level from VacuumEntity

**Task:** Remove deprecated battery level attribute from vacuum.py

**File:** `custom_components/robovac/vacuum.py`

**Search for:**

- `_attr_battery_level` declarations
- `battery_level` property
- Any references to battery level in entity

**Modification:**

- Remove attribute declaration (if exists)
- Remove property (if exists)
- Ensure battery sensor component handles battery reporting independently

**Validation:**

- Check that battery sensor in sensor.py is unaffected
- Run full test suite
- Verify no regressions

**Run tests:**

```bash
task test
```

#### Step 1.4: Commit Changes

**Commit message:**

```text
fix: remove deprecated battery feature from vacuum models

Remove VacuumEntityFeature.BATTERY from all 35 vacuum models
to prepare for Home Assistant 2026.8 compatibility.

- Remove battery feature flag from homeassistant_features
- Maintain battery command mappings for backward compatibility
- Battery reporting continues via dedicated battery sensor
- No breaking changes for existing users

Refs: #171
```

---

### Phase 2: Error Message Improvements (Test-First)

#### Step 2.1: Write Failing Tests for Error Messages

**Task:** Create test file for error message enhancements

**File:** `tests/test_errors.py`

**Test Cases:**

```python
# Test 1: Verify typo fix - "Laser sensor stuck" not "Laser sesor stuck"
# Test 2: Test getErrorMessage() returns correct messages
# Test 3: Test getErrorMessageWithContext() returns message + context
# Test 4: Test context includes troubleshooting steps
# Test 5: Test context includes series-specific guidance
# Test 6: Test unknown error codes return gracefully
```

**Implementation Details:**

- Test error code 19 returns "Laser sensor stuck"
- Test getErrorMessageWithContext(19) returns dict with 'message', 'troubleshooting', 'common_causes'
- Test contextual information is helpful and actionable
- Test function handles None, str, and int error codes

**Run tests (should fail):**

```bash
task test tests/test_errors.py
```

#### Step 2.2: Fix Typo in ERROR_MESSAGES

**Task:** Fix "sesor" → "sensor" typo

**File:** `custom_components/robovac/errors.py`

**Change:**

```python
# Line 20
# BEFORE:
19: "Laser sesor stuck",

# AFTER:
19: "Laser sensor stuck",
```

**Run tests (should pass typo test):**

```bash
task test tests/test_errors.py::test_laser_sensor_typo_fixed
```

#### Step 2.3: Implement getErrorMessageWithContext()

**Task:** Add enhanced error messaging function

**File:** `custom_components/robovac/errors.py`

**Function signature:**

```python
def getErrorMessageWithContext(
    code: str | int,
    model_code: str | None = None
) -> dict[str, str | list[str]]:
    """Get error message with troubleshooting context.
    
    Args:
        code: The error code to look up
        model_code: Optional model code for model-specific guidance
        
    Returns:
        Dictionary containing:
        - message: The error message
        - troubleshooting: List of troubleshooting steps
        - common_causes: List of common causes
        - series_info: Model series-specific information (if applicable)
    """
```

**Implementation Details:**

- Build on existing ERROR_MESSAGES dict
- Add TROUBLESHOOTING_CONTEXT dict with error-specific guidance
- Detect model series (C, G, L, X) from model_code if provided
- Return structured dict with actionable information
- Handle missing/unknown codes gracefully

**Error context examples:**

```python
TROUBLESHOOTING_CONTEXT = {
    1: {  # Front bumper stuck
        "troubleshooting": [
            "Check front bumper for obstructions",
            "Clean bumper sensors",
            "Ensure bumper moves freely"
        ],
        "common_causes": [
            "Hair or debris blocking bumper",
            "Damaged bumper spring",
            "Sensor misalignment"
        ]
    },
    19: {  # Laser sensor stuck
        "troubleshooting": [
            "Remove any stickers or tape from laser sensor",
            "Clean laser sensor cover",
            "Check for physical damage to sensor",
            "Restart vacuum"
        ],
        "common_causes": [
            "Protective film not removed",
            "Dust or debris on sensor",
            "Physical damage to sensor cover"
        ]
    },
    # ... add for other common errors
}
```

**Run tests (should pass):**

```bash
task test tests/test_errors.py
```

#### Step 2.4: Add Type Hints and Documentation

**Task:** Ensure all error functions have proper typing

**Files:**

- `custom_components/robovac/errors.py`

**Requirements:**

- Add type hints to all functions
- Add comprehensive docstrings (Google style)
- Document return types clearly
- Add examples in docstrings

**Run type check:**

```bash
task type-check
```

#### Step 2.5: Commit Changes

**Commit message:**

```text
feat: enhance error messages with troubleshooting context

Add getErrorMessageWithContext() function to provide users with
actionable troubleshooting steps and common causes for error codes.

- Fix typo: "Laser sesor stuck" → "Laser sensor stuck"
- Add TROUBLESHOOTING_CONTEXT with detailed guidance
- Support model series-specific troubleshooting
- Maintain backward compatibility with getErrorMessage()

Refs: #171
```

---

### Phase 3: Model Validator Library (Test-First)

#### Step 3.1: Write Failing Tests for Model Validator

**Task:** Create comprehensive test file for model validator

**File:** `tests/test_model_validator.py`

**Test Cases:**

```python
# Series Detection Tests
# Test 1: Detect C series (RoboVac C models)
# Test 2: Detect G series (RoboVac G series)
# Test 3: Detect L series (Clean L series)
# Test 4: Detect X series (RoboVac X series)
# Test 5: Handle unknown series
# Test 6: Handle None/invalid model codes

# Model Validation Tests
# Test 7: Validate supported models return True
# Test 8: Validate unsupported models return False
# Test 9: Get model list
# Test 10: Get supported model for device code (T2278 → T2278)

# Suggestion Tests
# Test 11: Suggest similar models for unsupported model
# Test 12: Suggest series alternatives
# Test 13: Handle edge cases (empty suggestions)

# Troubleshooting Tests
# Test 14: Get series-specific troubleshooting guide
# Test 15: Get general troubleshooting guide
# Test 16: Validate troubleshooting content is helpful
```

**Implementation Details:**

- Test all public functions
- Test edge cases and error handling
- Mock ROBOVAC_MODELS import
- Verify series detection logic
- Validate suggestion algorithm

**Run tests (should fail):**

```bash
task test tests/test_model_validator.py
```

#### Step 3.2: Create Model Validator Module

**Task:** Implement model validator library

**File:** `custom_components/robovac/model_validator.py`

**Module structure:**

```python
"""Model validation and series detection for RoboVac devices.

This module provides utilities for validating RoboVac model codes,
detecting model series (C, G, L, X), and providing troubleshooting
guidance for unsupported models.
"""

from typing import Dict, List, Optional, Tuple
import re

# Series detection patterns
SERIES_PATTERNS = {
    'C': r'^T2(103|123)$',  # RoboVac C series
    'G': r'^T2(150|261)$',  # RoboVac G series
    'L': r'^T2(2[67][0-9]|278|320)$',  # Clean L series
    'X': r'^T2(080|117|118|119|120|128|130|132|181|190|192|193|194|25[0-9]|262)$',  # RoboVac X series
}

def detect_series(model_code: str) -> Optional[str]:
    """Detect the series of a RoboVac model."""
    
def is_supported_model(model_code: str) -> bool:
    """Check if a model code is supported."""
    
def get_supported_models() -> List[str]:
    """Get list of all supported model codes."""
    
def suggest_similar_models(model_code: str, max_suggestions: int = 5) -> List[Tuple[str, str]]:
    """Suggest similar supported models for an unsupported model."""
    
def get_troubleshooting_guide(model_code: str) -> Dict[str, str | List[str]]:
    """Get series-specific troubleshooting guide."""
```

**Implementation Requirements:**

- Import ROBOVAC_MODELS from vacuums.**init**
- Use regex for series detection
- Implement similarity algorithm for suggestions
- Provide comprehensive troubleshooting guides per series
- Handle import failures gracefully (for standalone usage)
- Add full type hints
- Add comprehensive docstrings

**Run tests (should pass):**

```bash
task test tests/test_model_validator.py
```

#### Step 3.3: Add Type Hints and Linting

**Task:** Ensure code quality standards

**Files:**

- `custom_components/robovac/model_validator.py`

**Requirements:**

- Run task lint
- Run task type-check
- Fix any violations
- Ensure all functions have type hints
- Ensure all functions have docstrings

**Run quality checks:**

```bash
task lint
task type-check
```

#### Step 3.4: Commit Changes

**Commit message:**

```text
feat: add model validator library with series detection

Add model_validator.py module to provide:
- Automatic model series identification (C, G, L, X)
- Model validation against supported models
- Smart suggestions for unsupported models
- Series-specific troubleshooting guides

Refs: #171
```

---

### Phase 4: Model Validator CLI Tool (Test-First)

#### Step 4.1: Write Tests for CLI Tool

**Task:** Create test file for CLI functionality

**File:** `tests/test_model_validator_cli.py`

**Test Cases:**

```python
# Argument Parsing Tests
# Test 1: Parse model code argument
# Test 2: Parse --list flag
# Test 3: Parse --help flag
# Test 4: Handle missing arguments

# Output Tests
# Test 5: Supported model shows success message
# Test 6: Unsupported model shows suggestions
# Test 7: List mode shows all models
# Test 8: Output format is user-friendly

# Integration Tests
# Test 9: Standalone mode works without imports
# Test 10: Integrated mode uses actual ROBOVAC_MODELS
```

**Implementation Details:**

- Use unittest.mock for subprocess testing
- Mock sys.argv for argument testing
- Capture stdout/stderr
- Test CLI exit codes (0 = success, 1 = error)

**Run tests (should fail):**

```bash
task test tests/test_model_validator_cli.py
```

#### Step 4.2: Create CLI Tool

**Task:** Implement standalone CLI tool

**File:** `custom_components/robovac/model_validator_cli.py`

**Module structure:**

```python
#!/usr/bin/env python3
"""Standalone CLI tool for RoboVac model validation.

This tool can be used independently to validate RoboVac model compatibility
and get suggestions for unsupported models.

Usage:
    python model_validator_cli.py T2278
    python model_validator_cli.py --list
"""

import argparse
import sys
from typing import Optional

try:
    from .model_validator import (
        is_supported_model,
        get_supported_models,
        suggest_similar_models,
        get_troubleshooting_guide,
        detect_series
    )
    STANDALONE = False
except ImportError:
    # Fallback for standalone usage
    STANDALONE = True
    # Minimal implementation with hardcoded model list
    
def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Validate RoboVac model compatibility"
    )
    parser.add_argument(
        "model",
        nargs="?",
        help="Model code to validate (e.g., T2278)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all supported models"
    )
    args = parser.parse_args()
    
    # Implementation
    
if __name__ == "__main__":
    sys.exit(main())
```

**Implementation Requirements:**

- Use argparse for CLI arguments
- Provide clean, user-friendly output
- Use colors if terminal supports (optional)
- Handle errors gracefully
- Support standalone mode (fallback if module import fails)
- Make executable with shebang
- Exit with appropriate codes (0 = success, 1 = error, 2 = validation failure)

**Run tests (should pass):**

```bash
task test tests/test_model_validator_cli.py
```

#### Step 4.3: Add Documentation and Make Executable

**Task:** Finalize CLI tool

**Files:**

- `custom_components/robovac/model_validator_cli.py`
- `README.md` (add usage documentation)

**Requirements:**

- Add comprehensive --help text
- Add usage examples in docstring
- Update README.md with CLI tool section
- Test manually: `python custom_components/robovac/model_validator_cli.py T2278`

**Run lint:**

```bash
task lint
```

#### Step 4.4: Commit Changes

**Commit message:**

```text
feat: add standalone CLI tool for model validation

Add model_validator_cli.py tool for users to validate
RoboVac model compatibility before setting up integration.

- Supports standalone usage without integration installed
- Shows model validation status
- Suggests similar models for unsupported devices
- Lists all supported models with --list flag
- Provides troubleshooting guidance

Usage: python model_validator_cli.py T2278

Refs: #171
```

---

### Phase 5: Integration and Documentation

#### Step 5.1: Integration Tests

**Task:** Create end-to-end integration tests

**File:** `tests/test_integration_pr171.py`

**Test Cases:**

```python
# Test 1: Vacuum entity initializes without battery feature
# Test 2: Battery sensor still reports battery level
# Test 3: Error messages include context when displayed
# Test 4: Model validator works with actual vacuum models
# Test 5: CLI tool works with integration
```

**Run tests:**

```bash
task test tests/test_integration_pr171.py
```

#### Step 5.2: Update Documentation

**Task:** Update project documentation

**Files to update:**

- `README.md`: Add model validator CLI usage
- `DEVELOPMENT.md`: Document error context system
- `CHANGELOG.md`: Add entry for this feature set

**README.md additions:**

```markdown
## Model Validation

Before setting up the integration, you can validate if your RoboVac model is supported:

```bash
python custom_components/robovac/model_validator_cli.py T2278
```

To see all supported models:

```bash
python custom_components/robovac/model_validator_cli.py --list
```

**Run markdown lint:**

```bash
npx markdownlint-cli2 "**/*.md"
```

#### Step 5.3: Full Test Suite

**Task:** Run complete test suite

**Commands:**

```bash
task lint
task type-check
task test
```

**Validation:**

- All tests pass
- No linting errors
- No type checking errors
- No markdown lint errors
- Test coverage maintained or improved

#### Step 5.4: Final Commit

**Commit message:**

```text
docs: update documentation for PR #171 features

Add documentation for:
- Model validator CLI tool usage
- Error message improvements
- Battery deprecation changes
- Integration guide updates

Refs: #171
```

---

### Phase 6: Review and Cleanup

#### Step 6.1: Code Review Checklist

- [ ] All tests pass
- [ ] Type hints on all new functions
- [ ] Docstrings follow Google style
- [ ] No flake8 violations
- [ ] No markdown lint errors
- [ ] Follows existing code patterns
- [ ] No code duplication
- [ ] Error handling comprehensive
- [ ] Backward compatibility maintained
- [ ] No breaking changes

#### Step 6.2: Create Summary Document

**Task:** Create summary of changes for review

**File:** `IMPLEMENTATION_SUMMARY_PR171.md`

**Contents:**

- List of all files modified/created
- Test coverage report
- Key design decisions
- Migration guide (if needed)
- Known limitations
- Future improvements

#### Step 6.3: Final Validation

**Task:** Run full validation suite

```bash
# Run all tests
task test

# Check code quality
task lint
task type-check

# Verify documentation
npx markdownlint-cli2 "**/*.md"

# Manual testing
python custom_components/robovac/model_validator_cli.py T2278
python custom_components/robovac/model_validator_cli.py T9999
python custom_components/robovac/model_validator_cli.py --list
```

---

## Execution Notes for LLM

### TDD Workflow

1. **Always write tests first** - Tests define expected behavior
2. **Run tests (should fail)** - Confirms tests are actually testing something
3. **Implement minimal code** - Just enough to pass tests
4. **Run tests (should pass)** - Confirms implementation works
5. **Refactor if needed** - Improve code while keeping tests green
6. **Commit** - Small, focused commits with conventional commit messages

### Code Quality Standards

- **Type hints:** Required on all function parameters and returns
- **Docstrings:** Google style, required on all public functions
- **Linting:** Run `task lint` before committing
- **Type checking:** Run `task type-check` before committing
- **Testing:** Run `task test` after each phase

### Testing Commands

```bash
# Run specific test file
task test tests/test_model_validator.py

# Run specific test function
task test tests/test_model_validator.py::test_detect_c_series

# Run all tests
task test

# Run with coverage
```bash
task test --cov
```

### Commit Message Format

```text
<type>: <description>

<body>

Refs: #171
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`

### File Modification Strategy

1. Read file first to understand structure
2. Make minimal changes
3. Preserve existing formatting
4. Use multi_edit for batch updates
5. Run tests after each file modification

### Error Handling

- Always handle None/null cases
- Provide meaningful error messages
- Don't crash on unexpected input
- Log errors appropriately (DEBUG level for expected errors)

### Dependencies

- Don't add new external dependencies without explicit approval
- Use stdlib where possible
- Leverage existing project utilities

---

## Success Criteria

### Must Have

- [ ] All 35 vacuum models have battery feature removed
- [ ] Error message typo fixed
- [ ] getErrorMessageWithContext() implemented and tested
- [ ] model_validator.py implemented and tested
- [ ] model_validator_cli.py implemented and tested
- [ ] All tests pass
- [ ] No linting errors
- [ ] No type checking errors
- [ ] Documentation updated

### Should Have

- [ ] Integration tests pass
- [ ] Test coverage ≥ 90% for new code
- [ ] CLI tool tested manually
- [ ] README examples work
- [ ] Backward compatibility verified

### Nice to Have

- [ ] Performance benchmarks
- [ ] User testimonials
- [ ] Video demo of CLI tool
- [ ] Blog post about features

---

## Timeline Estimate

- **Phase 1:** Battery Deprecation - 2-3 hours
- **Phase 2:** Error Messages - 2-3 hours
- **Phase 3:** Model Validator Library - 3-4 hours
- **Phase 4:** CLI Tool - 2-3 hours
- **Phase 5:** Integration & Docs - 2-3 hours
- **Phase 6:** Review & Cleanup - 1-2 hours

**Total:** 12-18 hours of focused development

---

## Questions/Clarifications Needed

1. Should model_validator.py be exposed as a public API?
2. Should CLI tool be installed system-wide or just in project?
3. Any specific Home Assistant version requirements?
4. Should we add warnings for deprecated battery feature in logs?
5. Performance requirements for model suggestion algorithm?

---

## References

- PR #171: [https://github.com/damacus/robovac/pull/171](https://github.com/damacus/robovac/pull/171)
- Home Assistant 2026.8 Deprecations
- Project coding standards: `.windsurf/rules/`
- Test patterns: `tests/test_vacuum/test_t2278_command_mappings.py`
