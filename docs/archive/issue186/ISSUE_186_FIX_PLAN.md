# Fix Plan for Issue #186: T2262 Missing STATUS Value Mappings

## Issue Summary

**Title:** T2262: Missing command mapping for status value "Charging"

**Problem:** T2262 vacuum model has STATUS command defined (code 15) but lacks value mappings. When the device sends status updates like "Charging", "Sleeping", or "completed", they cannot be translated to human-readable values, resulting in debug logs and potentially confusing status displays.

**Affected Users:** Multiple users (SGXander, JBenson74, dxmnkd316) reported this issue.

**Related Models:** T2253 also has the same issue (STATUS code 15, no values defined).

## Current State Analysis

### What We Know

1. **T2262 Current Implementation** (`custom_components/robovac/vacuums/T2262.py`):

   ```python
   RobovacCommand.STATUS: {
       "code": 15,
   },
   ```

   - Has STATUS command defined
   - Code is 15
   - No `values` dict defined

2. **Missing Status Values (reported by users):**
   - "Charging"
   - "Sleeping"
   - "completed"
   - Error value "0" (already handled in ERROR command)

3. **Similar Working Model (T2277)** - Uses different code (153):

   ```python
   RobovacCommand.STATUS: {
       "code": 153,
       "values": {
           "Charging": "BBADGgA=",
           "Sleeping": "AhAB",
           "completed": "BhADGgIIAQ==",
           "Standby": "AA==",
           "Paused": "CAoAEAUyAggB",
           # ... bidirectional mappings
       },
   }
   ```

4. **Current Behavior:**
   - When device sends unmapped status, `getRoboVacHumanReadableValue()` returns the original value
   - Logs debug message (changed from WARNING in previous fix)
   - Status may display as raw value instead of human-readable string

### What We Don't Know

**CRITICAL:** We lack actual T2262 device data showing:

- What exact values the device sends for STATUS code 15
- Whether values are base64-encoded strings or plain text
- Bidirectional mapping requirements

**Why This Matters:** STATUS code 15 (T2262) likely uses different encoding than code 153 (T2277). Cannot safely copy mappings between models.

## Solution Strategy

### Phase 1: Data Collection (PREREQUISITE)

**Objective:** Gather actual T2262 device data from users.

**Action Items:**

1. **Contact affected users** via GitHub issue #186
2. **Request device data collection** using Home Assistant debug logs:

   ```yaml
   logger:
     default: info
     logs:
       custom_components.robovac: debug
   ```

3. **Data needed for each status:**
   - Raw value received from device
   - What Eufy app displayed at that time
   - Example statuses: Charging, Sleeping, Completed, Standby, Paused, Cleaning, etc.

4. **Document findings** in issue comments before proceeding to implementation.

### Phase 2: Implementation (TDD Approach)

**Prerequisites:**

- ✅ Phase 1 data collection complete
- ✅ Verify at least 5-7 status mappings available
- ✅ Confirm with user that test data matches their observations

#### Step 1: Write Failing Tests FIRST

**File:** `tests/test_vacuum/test_t2262_command_mappings.py`

Add comprehensive STATUS value tests:

```python
def test_t2262_status_human_readable_values(mock_t2262_robovac) -> None:
    """Test T2262 STATUS command translates device values to human-readable strings."""
    # TODO: Replace with ACTUAL device values from Phase 1
    # Example structure (DO NOT USE without real data):
    # assert mock_t2262_robovac.getRoboVacHumanReadableValue(
    #     RobovacCommand.STATUS, "DEVICE_VALUE_HERE"
    # ) == "Charging"
    
    # Add tests for ALL collected status values:
    # - Charging
    # - Sleeping
    # - Completed
    # - Standby
    # - Paused
    # - Cleaning/Auto
    # - Returning home
    # - etc.
    pass  # Remove after adding real tests


def test_t2262_status_case_insensitive(mock_t2262_robovac) -> None:
    """Test T2262 STATUS values work with case-insensitive lookup."""
    # Test that case variations of device values still match
    pass  # Implement with real data


def test_t2262_status_bidirectional_mapping(mock_t2262_robovac) -> None:
    """Test T2262 STATUS supports bidirectional lookups if needed."""
    # Only if device uses bidirectional mapping (check T2277 pattern)
    pass  # Implement if needed
```

**Run tests to verify they fail:**

```bash
task test
```

Expected: New tests fail because T2262.py lacks STATUS values.

#### Step 2: Implement Status Values

**File:** `custom_components/robovac/vacuums/T2262.py`

Update STATUS command with collected data:

```python
RobovacCommand.STATUS: {
    "code": 15,
    "values": {
        # TODO: Add mappings from Phase 1 data collection
        # Follow this pattern based on actual device data:
        # "device_value": "HumanReadable",
        # "HumanReadable": "device_value",  # If bidirectional needed
        
        # EXAMPLE ONLY - Replace with real data:
        # "charging": "Charging",
        # "Charging": "charging",
        # "sleeping": "Sleeping", 
        # "Sleeping": "sleeping",
        # "completed": "Completed",
        # etc.
    },
},
```

**Important Notes:**

- Maintain consistency with existing models' capitalization patterns
- Add bidirectional mappings if device requires reverse lookups
- Include comments noting source of mappings (user data, firmware version, etc.)

#### Step 3: Verify Tests Pass

```bash
task test
```

Expected: All new STATUS tests pass.

#### Step 4: Run Full Test Suite

```bash
task test
```

Expected: All existing tests still pass (no regressions).

#### Step 5: Code Quality Checks

```bash
task lint
task type-check
```

Expected: No linting or type errors.

### Phase 3: Documentation & Validation

#### Update Documentation

1. **Add comment in T2262.py** noting data source:

   ```python
   RobovacCommand.STATUS: {
       "code": 15,
       # Mappings confirmed by users: @SGXander, @dxmnkd316
       # Firmware version: [if known]
       # Date verified: 2025-10-22
       "values": {
           # ...
       },
   },
   ```

2. **Update DEVELOPMENT.md** if new patterns introduced

3. **Add to CODE_COVERAGE_TODO.md** if other models need similar fixes

#### User Validation

1. **Create test branch** with changes
2. **Share with affected users** via GitHub issue
3. **Request testing** on actual devices
4. **Gather feedback** before merging

### Phase 4: Related Models (Optional)

**Check if other models need similar fixes:**

Models with STATUS code 15 and no values:

- T2253 (mentioned in issue comments)
- T2250, T2251, T2252, T2254, T2255, T2259, T2268, T2270, T2272, T2273

**Decision:** Fix T2262 first, then evaluate if pattern applies to others.

## Testing Strategy

### Test Coverage Requirements

All tests must pass before merging:

1. ✅ STATUS value translations work
2. ✅ Case-insensitive lookup works
3. ✅ Bidirectional mapping works (if applicable)
4. ✅ Unknown values return as-is (existing behavior)
5. ✅ No regressions in other commands
6. ✅ Full test suite passes
7. ✅ Linting passes
8. ✅ Type checking passes

### Manual Testing Checklist

Before marking issue as resolved:

- [ ] User confirms status displays correctly in Home Assistant
- [ ] "Charging" shows as "Charging" (not raw value)
- [ ] "Sleeping" shows correctly
- [ ] "Completed" shows correctly
- [ ] No debug logs for mapped values
- [ ] Device commands still work
- [ ] State transitions work correctly

## Implementation Notes for LLM

### DO NOT Proceed Without Data

**STOP if:**

- Phase 1 data collection incomplete
- User data not available
- Uncertain about mappings

**ASK for:**

- Actual device logs
- User confirmation
- Additional test cases

### TDD Discipline

**ALWAYS:**

1. Write test first
2. Verify it fails
3. Implement feature
4. Verify test passes
5. Run full suite
6. Refactor if needed

**NEVER:**

- Skip tests
- Implement without failing test
- Guess at device values
- Copy mappings from different model codes

### Code Standards

**Follow existing patterns:**

- Use lowercase snake_case for keys (e.g., "charging")
- Use PascalCase for values (e.g., "Charging")
- Maintain bidirectional mappings if model requires it
- Add type hints
- Include docstrings for new functions

### Git Workflow

**Conventional Commits:**

```bash
# After Phase 1
git checkout -b fix/issue-186-t2262-status-mappings

# After implementation
git add tests/test_vacuum/test_t2262_command_mappings.py
git commit -m "test: add T2262 STATUS value mapping tests"

git add custom_components/robovac/vacuums/T2262.py
git commit -m "fix(T2262): add STATUS command value mappings

- Add Charging, Sleeping, completed status values
- Fixes #186
- Confirmed with users @SGXander @dxmnkd316"

# After validation
git push origin fix/issue-186-t2262-status-mappings
```

**PR Description Template:**

```markdown
## Fixes #186

### Changes
- Added STATUS value mappings for T2262 model
- Added comprehensive test coverage for STATUS values

### Testing
- ✅ All tests pass
- ✅ Lint/type checks pass
- ✅ User validation: @username confirmed working

### Data Source
Status mappings provided by users:
- @SGXander
- @dxmnkd316

### Notes
[Any important context about the mappings]
```

## Risk Assessment

### Low Risk ✅

- Adding value mappings to existing command
- Following established patterns
- Comprehensive test coverage

### Medium Risk ⚠️

- Status values might change with firmware updates
- Users on different firmware versions may see different values

### Mitigation

- Document firmware version in comments
- Add fallback behavior (return raw value if unmapped)
- Monitor issue for additional reports

## Success Criteria

Issue can be closed when:

1. ✅ T2262 has STATUS values mapped
2. ✅ All tests pass
3. ✅ Users confirm fix works on real devices
4. ✅ No debug logs for mapped status values
5. ✅ Documentation updated
6. ✅ Code merged to main branch

## Questions for User (if blocked)

If you need clarification:

1. "Can you enable debug logging and share the exact raw values your T2262 sends for STATUS code 15?"
2. "What does the Eufy app show when you see the 'Charging' debug message?"
3. "Can you test this branch and confirm the status displays correctly?"
4. "What firmware version is your T2262 running?"

## Estimated Effort

- Phase 1 (Data Collection): 2-5 days (waiting on users)
- Phase 2 (Implementation): 30-60 minutes (with data)
- Phase 3 (Documentation): 15 minutes
- Phase 4 (User Validation): 1-3 days

**Total:** ~3-8 days (mostly waiting for user feedback)

## References

- Issue: <https://github.com/damacus/robovac/issues/186>
- Related PR (T2277 model): Check for STATUS implementation pattern
- Test pattern: `tests/test_vacuum/test_t2278_command_mappings.py`
- Similar fix: T2252 (see previous memory about mapping fixes)

---

**Last Updated:** 2025-10-22
**Status:** Ready for data collection
**Assigned To:** [LLM or developer name]
