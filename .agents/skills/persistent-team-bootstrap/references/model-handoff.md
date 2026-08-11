# Model Handoff

Discover model and effort pairs only from the closed `active-runtime:model/list`
snapshot. Use `gpt-5.6-luna` at `xhigh` only for tightly specified coding when
that exact pair is advertised; otherwise select `gpt-5.6-terra` at an
advertised effort. Do not change the Nightingale seat, human authority,
sandbox, approvals, or writer ownership because of a model choice.

Terra prefers `xhigh`, `high`, `medium`, then `low`; `max` and `ultra` are
last-resort capability tiers used only when no normal effort is advertised.

Safe boundary state machine:

```text
idle (writer count 0)
  -> old writer stopped or idle, summary and verification complete
  -> new writer acknowledgement
  -> active (writer count exactly 1)
```

A failed spawn is not evidence of global model unavailability. Record only the
runtime catalog status: `not_assessed`, `advertised`, or
`not_advertised_in_this_runtime`. A direct active-to-active model change is a
conflict: move safely from active one writer to zero, then acknowledge the new
active writer and move back to one.
