# Persistent Team Bootstrap

## Decision

Install the reusable bootstrap package in Robovac, generate a persistent
four-seat team, and publish the same package from the authored skills source.
No Robovac product, dependency, manifest, or Home Assistant deployment file is
in scope.

## Safe boundary model handoff

```text
idle (count 0)
  -> old writer stopped or idle; summary and verification complete
  -> new writer acknowledgement
  -> active Nightingale writer (count exactly 1)
```

Model selection is discovered from the active runtime catalog. Luna at xhigh is
preferred only for tightly specified coding when advertised; otherwise Terra
is the fallback. A model shift cannot alter authority, seat, sandbox,
approvals, or ownership.

## Verification

Run the focused Python contracts, inspect the `new` dry-run JSON, apply once,
validate, apply again for idempotence, then run the read-only routing and
optional pulse pilots. Store bounded, redacted results under
`.agents/team/reports/`.
