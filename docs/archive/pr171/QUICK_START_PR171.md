# Quick Start Guide: Implementing PR #171 Features

## Overview

This guide provides a quick reference for implementing the features from PR #171 on your current branch.

**Full details:** See `IMPLEMENTATION_PLAN_PR171.md`

---

## What You're Building

1. **Battery Deprecation** - Remove deprecated battery feature from 35+ vacuum models
2. **Error Context** - Enhanced error messages with troubleshooting guidance
3. **Model Validator** - Library for validating and suggesting model compatibility
4. **CLI Tool** - Standalone tool for users to check model support

---

## Quick Start

### Step 1: Read the Plans

```bash
# Review summary
cat PR171_REVIEW_SUMMARY.md

# Read full implementation plan
cat IMPLEMENTATION_PLAN_PR171.md
```

### Step 2: Start Phase 1

```bash
# Create test file
touch tests/test_vacuum/test_battery_feature_removal.py

# Write failing tests first (see plan for test cases)
# Then implement changes
```

### Step 3: Follow TDD Cycle

For each phase:

1. ✍️ Write failing tests
2. ✅ Run tests (should fail)
3. 🔧 Implement minimal code
4. ✅ Run tests (should pass)
5. 🔄 Refactor if needed
6. 📝 Commit changes

### Step 4: Quality Checks

After each phase:

```bash
task lint
task type-check
task test
```

---

## Phase Overview

| Phase | Task | Time | Status |
|-------|------|------|--------|
| 1 | Battery Deprecation | 2-3h | ⬜ Not Started |
| 2 | Error Messages | 2-3h | ⬜ Not Started |
| 3 | Model Validator | 3-4h | ⬜ Not Started |
| 4 | CLI Tool | 2-3h | ⬜ Not Started |
| 5 | Integration & Docs | 2-3h | ⬜ Not Started |
| 6 | Review & Cleanup | 1-2h | ⬜ Not Started |

**Total:** 12-18 hours

---

## Testing Commands

```bash
# Run specific test file
task test tests/test_errors.py

# Run specific test
task test tests/test_errors.py::test_laser_sensor_typo_fixed

# Run all tests
task test

# Run with coverage
task test --cov
```

---

## Commit Message Template

```text
<type>: <short description>

<detailed description>

- Bullet point 1
- Bullet point 2

Refs: #171
```

**Types:** `feat`, `fix`, `refactor`, `test`, `docs`, `chore`

---

## Key Files

### To Create

- `custom_components/robovac/model_validator.py`
- `custom_components/robovac/model_validator_cli.py`
- `tests/test_battery_feature_removal.py`
- `tests/test_errors.py`
- `tests/test_model_validator.py`
- `tests/test_model_validator_cli.py`
- `tests/test_integration_pr171.py`

### To Modify

- All 35 vacuum models (`custom_components/robovac/vacuums/T2*.py`)
- `custom_components/robovac/vacuum.py`
- `custom_components/robovac/errors.py`
- `README.md`
- `DEVELOPMENT.md`
- `CHANGELOG.md`

---

## Rules to Remember

### Code Quality

- ✅ Type hints on all functions
- ✅ Google-style docstrings
- ✅ No flake8 violations
- ✅ Pass type checking
- ✅ Pass all tests

### Testing

- ✅ Write tests BEFORE implementation
- ✅ Test edge cases
- ✅ Test error handling
- ✅ Use existing test patterns
- ✅ Run `task test` not `pytest`

### Commits

- ✅ Small, focused commits
- ✅ Conventional commit messages
- ✅ One feature per commit
- ✅ Reference issue (#171)

---

## Progress Tracking

Mark each step as complete:

### Phase 1: Battery Deprecation

- [ ] Step 1.1: Write failing tests
- [ ] Step 1.2: Remove battery feature (35 files)
- [ ] Step 1.3: Remove _attr_battery_level
- [ ] Step 1.4: Commit

### Phase 2: Error Messages

- [ ] Step 2.1: Write failing tests
- [ ] Step 2.2: Fix typo
- [ ] Step 2.3: Implement getErrorMessageWithContext()
- [ ] Step 2.4: Add type hints
- [ ] Step 2.5: Commit

### Phase 3: Model Validator

- [ ] Step 3.1: Write failing tests
- [ ] Step 3.2: Create module
- [ ] Step 3.3: Quality checks
- [ ] Step 3.4: Commit

### Phase 4: CLI Tool

- [ ] Step 4.1: Write tests
- [ ] Step 4.2: Create CLI
- [ ] Step 4.3: Documentation
- [ ] Step 4.4: Commit

### Phase 5: Integration

- [ ] Step 5.1: Integration tests
- [ ] Step 5.2: Update docs
- [ ] Step 5.3: Full test suite
- [ ] Step 5.4: Commit

### Phase 6: Review

- [ ] Step 6.1: Code review checklist
- [ ] Step 6.2: Summary document
- [ ] Step 6.3: Final validation

---

## Getting Help

- 📖 Full plan: `IMPLEMENTATION_PLAN_PR171.md`
- 📋 Review summary: `PR171_REVIEW_SUMMARY.md`
- 🔗 Original PR: <https://github.com/damacus/robovac/pull/171>
- 📚 Coding standards: `.windsurf/rules/`
- 🧪 Test patterns: `tests/test_vacuum/test_t2278_command_mappings.py`

---

## Quick Validation

Before committing any phase:

```bash
# Check linting
task lint

# Check types
task type-check

# Run tests
task test

# Check markdown
npx markdownlint-cli2 "**/*.md"
```

All should pass! ✅

---

## Success Checklist

At the end, verify:

- [ ] All 35 vacuum models updated
- [ ] Error typo fixed
- [ ] getErrorMessageWithContext() works
- [ ] model_validator.py works
- [ ] model_validator_cli.py works
- [ ] All tests pass (task test)
- [ ] No lint errors (task lint)
- [ ] No type errors (task type-check)
- [ ] Docs updated
- [ ] No markdown lint errors

---

## Ready to Start?

```bash
# Ensure you're on the right branch
git status

# Start Phase 1, Step 1.1
# Open: tests/test_vacuum/test_battery_feature_removal.py
```

Good luck! Follow the detailed plan and you'll have all features implemented with full test coverage. 🚀
