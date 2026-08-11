# SDD Compatibility

Repositories that ignore `.superpowers/sdd/*` keep durable planning under
`docs/superpowers/plans/` and durable execution reports under
`.agents/team/reports/`. The bootstrap does not create product work, edit a
deployment, or infer a task from a pulse.

Use one active implementation owner per tranche. Bucky integrates rather than
implements; Hubble and Scout remain read-only. A plan identifies the owner,
the verification boundary, and explicit routing before a tranche begins.
