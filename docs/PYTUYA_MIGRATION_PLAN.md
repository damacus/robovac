# PyTuya Migration Plan

## Goal

Replace custom `tuyalocalapi.py` implementation with LocalTuya's battle-tested `pytuya` module to support Tuya protocol versions 3.1-3.5.

## Why Migrate?

- **T2276 (X8 Pro SES) requires protocol 3.5** - current implementation only supports 3.1
- **Future-proof** - supports all protocol versions as Tuya evolves
- **Community maintained** - actively developed by LocalTuya team
- **Production proven** - used by thousands of users
- **Better maintenance** - we don't have to maintain protocol implementation

## Source

LocalTuya PyTuya: <https://github.com/rospogrigio/localtuya/tree/master/custom_components/localtuya/pytuya>

## Migration Steps

### Phase 1: Integration (Low Risk)

1. **Download PyTuya module**
   - Copy `pytuya/__init__.py` from LocalTuya
   - Place in `custom_components/robovac/pytuya/`
   - Maintain as separate module initially

2. **Update dependencies**
   - Already have `cryptography` - no new dependencies needed
   - Verify version compatibility

3. **Create wrapper/adapter layer**
   - Map our API to PyTuya API
   - Minimize changes to existing code initially

### Phase 2: Gradual Migration (Medium Risk)

1. **Update `robovac.py`**
   - Replace `TuyaDevice` imports with PyTuya
   - Update initialization to use PyTuya API
   - Set protocol version per model

2. **Update model configurations**
   - Add `protocol_version` attribute to models
   - Default to 3.1 for existing models
   - Set 3.5 for T2276

3. **Update `vacuum.py`**
   - Adjust for any API differences
   - Update status polling logic
   - Update command sending logic

### Phase 3: Testing (Critical)

1. **Test T2276 specifically**
   - Verify protocol 3.5 communication works
   - Confirm "Incomplete read" errors are resolved
   - Test all commands (start, stop, return home, etc.)

2. **Regression test existing models**
   - Test at least 3 different model types
   - Verify protocol 3.1 still works
   - Ensure no breaking changes

3. **Run full test suite**
   - All 196 tests must pass
   - Add new tests for protocol version selection
   - Test error handling

### Phase 4: Cleanup (Low Risk)

1. **Remove old implementation**
   - Delete `tuyalocalapi.py` if fully replaced
   - Or keep as fallback initially
   - Clean up unused code

2. **Update documentation**
   - Update README with PyTuya attribution
   - Update DEVELOPMENT.md
   - Document protocol version configuration

3. **Final verification**
   - Lint and type-check pass
   - All tests pass
   - Documentation complete

## API Mapping

### Current API (TuyaDevice)

```python
device = TuyaDevice(dev_id, address, local_key, version=3.1)
await device.status()
await device.set_dp(value, dp_index)
```

### PyTuya API

```python
device = TuyaInterface(dev_id, address, local_key)
device.set_version(3.5)  # New capability!
status = await device.status()
await device.set_dp(value, dp_index)
```

## Key Differences

1. **Protocol version setting**:
   - Old: Fixed at initialization
   - New: Can be set with `set_version()`

2. **Error handling**:
   - PyTuya has more detailed error codes
   - Need to map to our error handling

3. **Async handling**:
   - PyTuya is fully async
   - Should integrate smoothly with our async code

## Rollback Plan

If migration fails:

1. Revert to previous commit
2. Keep T2276 marked as unsupported
3. Document issues encountered
4. Consider hybrid approach (PyTuya only for T2276)

## Success Criteria

- ✅ T2276 works without "Incomplete read" errors
- ✅ All existing models continue working
- ✅ All 196 tests pass
- ✅ No regressions in functionality
- ✅ Code quality maintained (lint, type-check)

## Timeline

- **Phase 1**: 2-3 hours (integration)
- **Phase 2**: 3-4 hours (migration)
- **Phase 3**: 2-3 hours (testing)
- **Phase 4**: 1-2 hours (cleanup)

**Total**: 8-12 hours of work

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Breaking existing models | Medium | High | Thorough testing, gradual rollout |
| API incompatibility | Low | Medium | Adapter layer, careful mapping |
| Performance issues | Low | Low | PyTuya is proven in production |
| New bugs | Medium | Medium | Comprehensive test coverage |

## Notes

- Keep existing implementation initially as fallback
- Test with real devices if possible (ask users)
- Monitor GitHub issues for similar migrations
- Consider releasing as beta first

## References

- LocalTuya: <https://github.com/rospogrigio/localtuya>
- PyTuya module: <https://github.com/rospogrigio/localtuya/tree/master/custom_components/localtuya/pytuya>
- Kevin's fork (working T2276): <https://github.com/kevinbird15/robovac-ha-integration/blob/purgatory>
- Issue #42: <https://github.com/damacus/robovac/issues/42>
