---
name: persistent-team-bootstrap
description: >-
  Bootstrap, adopt, and validate a safe persistent Codex team with one writer,
  explicit routing, safe model handoffs, and durable redacted team records.
---

# Persistent Team Bootstrap

Use this skill to create or adopt a repository-local persistent team without
overwriting managed files. It is deliberately model-neutral: seat files never
pin a model or reasoning effort.

Run the deterministic contract before applying state:

```sh
PYTHONPATH=.agents/skills/persistent-team-bootstrap/scripts \
  python3.11 -m unittest \
  discover \
  -s .agents/skills/persistent-team-bootstrap/tests -p 'test_*.py'
python3.11 .agents/skills/persistent-team-bootstrap/scripts/bootstrap_team.py \
  --repo . --config .agents/team/bootstrap.json --mode new
```

Inspect the JSON dry-run result, then apply only when it has no conflicts or
errors. Re-run the same command with `--apply`; a repeat is idempotent.

```sh
python3.11 .agents/skills/persistent-team-bootstrap/scripts/bootstrap_team.py \
  --repo . --config .agents/team/bootstrap.json \
  --mode new --apply
python3.11 \
  .agents/skills/persistent-team-bootstrap/scripts/validate_bootstrap.py \
  --repo . --config .agents/team/bootstrap.json
```

`adopt` is the only mode that can add the managed AGENTS section beside
unrelated instructions. It preserves unrelated personas, but refuses a
different managed file, malformed markers, path escape, symlink, fixed-policy
change, or persona model/effort pin. There is intentionally no force option.

Read [configuration](references/configuration.md),
[SDD compatibility](references/sdd-compatibility.md), and
[model handoff](references/model-handoff.md) before changing policy.

Generated helper scripts are data files installed with ordinary file modes;
invoke them through `python3.11` as shown above rather than relying on direct
executable permissions.
