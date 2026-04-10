# GitHub Labels System

This document describes the label system used in the damacus/robovac repository to organize and track issues.

## Label Categories

### Priority Labels

Indicate the urgency and importance of an issue.

- **`priority: critical`** - Breaking issues, security vulnerabilities, data loss
- **`priority: high`** - Major features, common bugs affecting many users
- **`priority: medium`** - Minor features, uncommon bugs
- **`priority: low`** - Nice-to-have features, cosmetic issues

### Type Labels

Classify the nature of the issue.

- **`bug`** - Something isn't working correctly
- **`enhancement`** - New feature or improvement request
- **`documentation`** - Documentation improvements or additions
- **`maintenance`** - Code refactoring, deprecations, technical debt
- **`question`** - User questions or clarifications needed

### Status Labels

Track the current state of an issue.

- **`status: needs-info`** - Waiting for additional information from reporter
- **`status: blocked`** - Blocked by external dependency or other issue
- **`status: in-progress`** - Actively being worked on
- **`status: ready`** - Ready for implementation, all info available

### Model Labels

Identify which vacuum model series the issue relates to.

- **`model: T21xx`** - T2100-T2199 series models
- **`model: T22xx`** - T2200-T2299 series models
- **`model: T23xx`** - T2300-T2399 series models
- **`model: unsupported`** - New model support requests

### Feature Labels

Tag specific functional areas.

- **`feature: battery`** - Battery-related functionality
- **`feature: mapping`** - Command/DPS mapping issues
- **`homeassistant`** - Home Assistant integration specific

### Special Labels

- **`help wanted`** - Community contributions welcome
- **`good first issue`** - Good for newcomers to the project
- **`duplicate`** - Duplicate of another issue
- **`wontfix`** - Will not be implemented
- **`dependencies`** - Dependency updates (Renovate, etc.)

## Usage Guidelines

### When Creating Issues

1. **Always add a type label**: `bug`, `enhancement`, `question`, etc.
2. **Add priority if known**: Helps maintainers triage
3. **Add model label if applicable**: Helps track model-specific issues
4. **Add feature label if relevant**: Groups related functionality

### Example Combinations

- Bug in T2251 mapping: `bug`, `model: T22xx`, `feature: mapping`, `priority: high`
- New model request: `enhancement`, `model: unsupported`, `help wanted`
- Battery deprecation work: `maintenance`, `feature: battery`, `homeassistant`, `priority: high`
- Documentation update: `documentation`, `good first issue`, `priority: low`

## Label Colors

- **Priority**: Red gradient (critical → low)
- **Type**: Standard GitHub defaults
- **Status**: Yellow/Orange tones
- **Model**: Blue tones
- **Feature**: Green tones
- **Special**: Purple/Gray tones

## Maintenance

Labels are created automatically when first applied via the GitHub API. To create labels manually:

1. Go to repository Settings → Labels
2. Click "New label"
3. Follow the naming convention from this document
4. Choose appropriate color based on category

## Notes

- Labels can be combined - use multiple labels to fully categorize issues
- Keep label names consistent with the patterns above
- Update this document when adding new label categories
