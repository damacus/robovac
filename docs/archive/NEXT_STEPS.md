# Quick Reference: Next Steps for more-mappings-work

## TL;DR

The branch needs test coverage for modified models, removal of duplicate mappings, and consistent conventions.

## Immediate Actions

### 1. Remove Duplicate Bidirectional Mappings (30 min)

**Why:** Case-insensitive matching makes them redundant
**Files:** T2250.py, T2252.py, T2253.py, T2254.py, T2255.py, T2259.py, T2262.py

```python
# Remove this:
"Auto": "Auto",        # Bidirectional duplicate
"SmallRoom": "SmallRoom",

# Keep this:
"auto": "Auto",
"small_room": "SmallRoom",
```

### 2. Create Missing Tests (4 hours)

**Critical Gap:** No tests for 8 modified models

Create these files following `test_t2277_command_mappings.py` pattern:

- `test_t2250_command_mappings.py`
- `test_t2251_command_mappings.py`
- `test_t2252_command_mappings.py`
- `test_t2253_command_mappings.py`
- `test_t2254_command_mappings.py`
- `test_t2255_command_mappings.py`
- `test_t2259_command_mappings.py`
- `test_t2262_command_mappings.py`

Each test must cover:

- Error code mapping (0 → "No error")
- MODE command values
- Case-insensitive matching
- FAN_SPEED mappings

### 3. Standardize Value Conventions (1 hour)

**Problem:** T2250 uses `"auto"`, T2252 uses `"Auto"`

**Solution:** All keys lowercase snake_case, all values PascalCase

## Running Tests

```bash
task test           # Run all tests
task lint           # Check code style
task type-check     # Verify type hints
```

## Files Changed in Branch

| File | Change | Tests Needed |
| ---- | ------ | ------------ |
| `robovac.py` | Case-insensitive matching | ✅ Done |
| `vacuum.py` | Error check includes "No error" | ⚠️ Integration test needed |
| `T2250.py` - `T2262.py` (8 files) | Error mappings + bidirectional | ❌ No tests |

## Priority Order

1. **HIGH:** Create test files (violates TDD)
2. **HIGH:** Remove duplicate mappings (code smell)
3. **MEDIUM:** Standardize conventions (maintainability)
4. **LOW:** Enhanced error codes (user experience)

## Success Checklist

- [ ] `task test` passes
- [ ] 8 new test files created
- [ ] No "Bidirectional mappings" comments remain
- [ ] All mapping keys use lowercase snake_case
- [ ] Test coverage ≥ previous level

## See Also

- `IMPROVEMENT_PLAN.md` - Complete analysis and strategy
- `tests/test_vacuum/test_t2277_command_mappings.py` - Test template
- User rules require TDD: write tests first!

---

**Estimated Time:** 6 hours total
**Risk:** Low (backward compatible changes)
**Blocks:** None
