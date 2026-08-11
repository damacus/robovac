# Verification

- `PYTHONPATH=.agents/skills/persistent-team-bootstrap/scripts python3.11 -m unittest discover -s .agents/skills/persistent-team-bootstrap/tests -p 'test_*.py'`
- `python3.11 .agents/skills/persistent-team-bootstrap/scripts/validate_bootstrap.py --repo . --config .agents/team/bootstrap.json`
- `python3.11 .agents/skills/team-improvement-loop/scripts/validate_team_setup.py`
- `python3.11 .agents/skills/team-improvement-loop/scripts/run_routing_evals.py --repo . --dry-run`
- `task lint`
- `task type-check`
- `task test`
