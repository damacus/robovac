# Feature Tracking System

This project uses JSON-based feature tracking in the `features/` directory.

## Structure

- `feature_list.json` - Master list of all feature areas
- `features/*.json` - Individual feature files by area

## Updating Feature Status

Use task commands to update feature JSON files:

```fish
# Mark a feature as passing
task jq:update-field FILE=features/vacuum_models.json ID=VAC-001 FIELD=passes VALUE=true

# List failing features in an area
task jq:list-failing FILE=vacuum_models

# See next features to work on
task jq:next-features

# Count remaining failing tests
task jq:count-remaining
```

## Rules

1. **Only modify the `passes` field** - Never edit descriptions, steps, or IDs
2. **Verify with tests first** - Run `task test` before marking as passing
3. **Use task commands** - Don't manually edit JSON files
4. **One feature at a time** - Complete and verify one feature before moving on

## Feature ID Prefixes

- `VAC-` - Vacuum model features
- `CORE-` - Core functionality
- `TEST-` - Testing infrastructure

## For AI Assistants

When working on features:

1. Run `task jq:next-features` to see what to work on
2. Follow TDD - write failing test first
3. Implement the feature
4. Run `task test` to verify
5. Update feature status with `task jq:update-field`
6. Commit with conventional commit message
