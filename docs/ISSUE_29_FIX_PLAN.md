# Issue #29 Fix Plan: Add Test Coverage for T2268 and T2267

## Objective

Add comprehensive test coverage for T2268 (L60) and T2267 (L60 Hybrid) vacuum models to comply with TDD requirements and complete issue #29 resolution.

## Prerequisites

- ✅ T2268.py model implementation exists
- ✅ T2267.py model implementation exists
- ✅ Both models registered in `vacuums/__init__.py`
- ✅ Reference test pattern available: `test_t2277_command_mappings.py`

## Tasks

### Task 1: Create T2268 Test File

**File:** `tests/test_vacuum/test_t2268_command_mappings.py`

**Test Cases Required:**

1. **Fixture Setup**

   ```python
   @pytest.fixture
   def mock_t2268_robovac() -> RoboVac:
       """Create a mock T2268 RoboVac instance for testing."""
   ```

2. **DPS Code Validation**
   - Test all command-to-DPS code mappings
   - Verify codes: START_PAUSE (2), DIRECTION (3), MODE (5), STATUS (15), RETURN_HOME (101), FAN_SPEED (102), LOCATE (103), BATTERY (104), ERROR (106)

3. **MODE Command Tests**
   - Verify mappings: auto → Auto, small_room → SmallRoom, spot → Spot, edge → Edge, nosweep → Nosweep
   - Test unknown value returns as-is

4. **FAN_SPEED Command Tests**
   - Verify mappings: pure → Pure, standard → Standard, turbo → Turbo, max → Max
   - Test unknown value returns as-is

5. **DIRECTION Command Tests**
   - Verify mappings: forward → forward, back → back, left → left, right → right
   - Test unknown value returns as-is

6. **Edge Cases**
   - Test case-insensitive lookup behavior
   - Test missing command graceful handling

### Task 2: Create T2267 Test File

**File:** `tests/test_vacuum/test_t2267_command_mappings.py`

**Test Cases Required:**

1. Review `T2267.py` implementation
2. Create corresponding tests following same pattern as T2268
3. Verify all commands and DPS codes per T2267 specification

### Task 3: Validation

**Run Tests:**

```bash
task test
```

**Expected Results:**

- All new tests pass
- No regressions in existing tests
- Coverage report shows T2268 and T2267 fully tested

### Task 4: Code Quality

**Linting:**

```bash
task lint
task type-check
```

**Markdown Validation:**

```bash
task markdownlint
```

### Task 5: Documentation Update

Update `CHANGELOG.md` if needed to reference test additions.

## Implementation Template

### T2268 Test Structure

Based on `test_t2277_command_mappings.py` pattern:

```python
"""Tests for T2268 command mappings and DPS codes."""

import pytest
from typing import Any
from unittest.mock import patch

from custom_components.robovac.robovac import RoboVac
from custom_components.robovac.vacuums.base import RobovacCommand


@pytest.fixture
def mock_t2268_robovac() -> RoboVac:
    """Create a mock T2268 RoboVac instance for testing."""
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        robovac = RoboVac(
            model_code="T2268",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )
        return robovac


def test_t2268_dps_codes(mock_t2268_robovac) -> None:
    """Test that T2268 has the correct DPS codes."""
    dps_codes = mock_t2268_robovac.getDpsCodes()
    
    # Verify all DPS code mappings from T2268.py
    assert dps_codes["START_PAUSE"] == "2"
    assert dps_codes["DIRECTION"] == "3"
    assert dps_codes["MODE"] == "5"
    assert dps_codes["STATUS"] == "15"
    assert dps_codes["RETURN_HOME"] == "101"
    assert dps_codes["FAN_SPEED"] == "102"
    assert dps_codes["LOCATE"] == "103"
    assert dps_codes["BATTERY_LEVEL"] == "104"
    assert dps_codes["ERROR"] == "106"


def test_t2268_mode_command_values(mock_t2268_robovac) -> None:
    """Test T2268 MODE command value mappings."""
    assert mock_t2268_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "auto") == "Auto"
    assert mock_t2268_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "small_room") == "SmallRoom"
    assert mock_t2268_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "spot") == "Spot"
    assert mock_t2268_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "edge") == "Edge"
    assert mock_t2268_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "nosweep") == "Nosweep"
    
    # Unknown returns as-is
    assert mock_t2268_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "unknown") == "unknown"


def test_t2268_fan_speed_command_values(mock_t2268_robovac) -> None:
    """Test T2268 FAN_SPEED command value mappings."""
    assert mock_t2268_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "pure") == "Pure"
    assert mock_t2268_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "standard") == "Standard"
    assert mock_t2268_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "turbo") == "Turbo"
    assert mock_t2268_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "max") == "Max"
    
    # Unknown returns as-is
    assert mock_t2268_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "unknown") == "unknown"


def test_t2268_direction_command_values(mock_t2268_robovac) -> None:
    """Test T2268 DIRECTION command value mappings."""
    assert mock_t2268_robovac.getRoboVacCommandValue(RobovacCommand.DIRECTION, "forward") == "forward"
    assert mock_t2268_robovac.getRoboVacCommandValue(RobovacCommand.DIRECTION, "back") == "back"
    assert mock_t2268_robovac.getRoboVacCommandValue(RobovacCommand.DIRECTION, "left") == "left"
    assert mock_t2268_robovac.getRoboVacCommandValue(RobovacCommand.DIRECTION, "right") == "right"
    
    # Unknown returns as-is
    assert mock_t2268_robovac.getRoboVacCommandValue(RobovacCommand.DIRECTION, "unknown") == "unknown"
```

## Acceptance Criteria

- [ ] `test_t2268_command_mappings.py` created with all required tests
- [ ] `test_t2267_command_mappings.py` created with all required tests
- [ ] All tests pass (`task test`)
- [ ] No linting errors (`task lint`)
- [ ] No type checking errors (`task type-check`)
- [ ] Markdown files pass validation (`task markdownlint`)
- [ ] Test coverage includes all T2268 and T2267 commands
- [ ] Unknown value fallback behavior tested
- [ ] No test regressions

## Post-Implementation

1. Run full test suite to verify no regressions
2. Update issue #29 with test results
3. Close issue #29 as resolved
4. Consider if similar missing tests exist for other models

## Notes

- Follow existing test patterns from `test_t2277_command_mappings.py`
- Do not test uncertain return values (per global rules)
- Use type hints for all test functions
- Keep tests focused and isolated
- Each test should verify one specific behavior

## Estimated Effort

- T2268 tests: ~30 minutes
- T2267 tests: ~30 minutes  
- Validation and cleanup: ~15 minutes
- **Total: ~1.25 hours**

## References

- **Template:** `tests/test_vacuum/test_t2277_command_mappings.py`
- **Model Impl:** `custom_components/robovac/vacuums/T2268.py`
- **Model Impl:** `custom_components/robovac/vacuums/T2267.py`
- **Issue:** <https://github.com/damacus/robovac/issues/29>
- **PR #81:** Original T2267/T2268 implementation
