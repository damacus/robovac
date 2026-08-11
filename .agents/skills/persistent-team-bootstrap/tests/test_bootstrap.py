"""Deterministic end-to-end contracts for persistent-team-bootstrap."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest import mock

import bootstrap_team as bootstrap


PACKAGE = Path(__file__).resolve().parents[1]
BOOTSTRAP = PACKAGE / "scripts" / "bootstrap_team.py"
VALIDATE = PACKAGE / "scripts" / "validate_bootstrap.py"


def config(**changes):
    value = {
        "human_authority": "Dan Webb",
        "seats": {name: {"display_name": name.title()} for name in ("bucky", "nightingale", "hubble", "scout")},
        "writer_owner_count": 1,
        "active_writer": "nightingale",
        "handoff": {
            "old_writer_status": "idle",
            "summary": "Ownership transfer is recorded.",
            "verification": "Focused checks run before transfer.",
            "new_writer_acknowledgement": "Nightingale accepts sole implementation ownership.",
            "objective": "Install the persistent team.",
            "owned_paths": [".agents/team"],
            "baseline": "Clean bootstrap baseline.",
            "dirty_paths": [],
            "checks": ["python3.11 -m unittest"],
            "findings": "No blocking findings.",
            "next_action": "Validate the bootstrap.",
            "requested_model": "Terra",
            "requested_effort": "high",
            "requested_reason": "Current runtime fallback.",
            "tightly_specified": False,
        },
        "fixed_policy": {
            "one_writer": True,
            "safe_handoff": True,
            "redaction": True,
            "routing": "explicit",
            "sandbox": "fixed",
        },
        "catalog": {"source": "active-runtime:model/list", "pairs": [{"model": "gpt-5.6-sol", "effort": "high"}, {"model": "gpt-5.6-terra", "effort": "high"}, {"model": "gpt-5.6-terra", "effort": "medium"}]},
        "model_selection": {"current": {"model": "gpt-5.6-terra", "effort": "high"}, "recommended": {"model": "gpt-5.6-terra", "effort": "high"}, "luna_status": "not_advertised_in_this_runtime"},
        "verification": {"narrow": ["python3.11 -m unittest"], "broad": ["task test"]},
        "recognition_wording": "Recognize reviewable contributions.",
    }
    value["handoff"]["requested_model"] = "gpt-5.6-terra"
    value.update(changes)
    return value


class BootstrapContract(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = (Path(self.temp.name) / "repo").resolve()
        self.repo.mkdir()
        self.config_path = self.repo / "bootstrap.json"
        self.write_config(config())

    def tearDown(self):
        self.temp.cleanup()

    def write_config(self, value):
        self.config_path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")

    def invoke(self, mode, apply=False, config_path=None):
        command = [sys.executable, str(BOOTSTRAP), "--repo", str(self.repo), "--config", str(config_path or self.config_path), "--mode", mode]
        if apply:
            command.append("--apply")
        completed = subprocess.run(command, text=True, capture_output=True, check=False)
        self.assertEqual(completed.stderr, "", completed.stderr)
        return completed, json.loads(completed.stdout)

    def apply(self):
        completed, payload = self.invoke("new", apply=True)
        self.assertEqual(completed.returncode, 0, payload)
        return payload

    def test_clean_new_dry_run_then_apply_is_idempotent(self):
        dry_run, dry = self.invoke("new")
        self.assertEqual(dry_run.returncode, 0)
        self.assertFalse(dry["apply"])
        self.assertIn("AGENTS.md", dry["created"])
        self.assertFalse((self.repo / "AGENTS.md").exists())
        applied = self.apply()
        self.assertTrue(applied["apply"])
        repeated, again = self.invoke("new", apply=True)
        self.assertEqual(repeated.returncode, 0)
        self.assertEqual(again["created"], [])
        self.assertIn("AGENTS.md", again["unchanged"])

    def test_validate_after_apply_and_wrapper_are_read_only(self):
        self.apply()
        completed, payload = self.invoke("validate")
        self.assertEqual(completed.returncode, 0, payload)
        self.assertEqual(payload["created"], [])
        wrapper = subprocess.run([sys.executable, str(VALIDATE), "--repo", str(self.repo), "--config", str(self.config_path)], text=True, capture_output=True, check=False)
        self.assertEqual(wrapper.returncode, 0, wrapper.stdout + wrapper.stderr)
        self.assertEqual(json.loads(wrapper.stdout)["mode"], "validate")

    def test_adopt_preserves_unrelated_agents_instructions_and_persona(self):
        (self.repo / "AGENTS.md").write_text("Keep project instructions.\n", encoding="utf-8")
        existing = self.repo / ".codex" / "agents"
        existing.mkdir(parents=True)
        (existing / "unrelated.toml").write_text('name = "Elsewhere"\n', encoding="utf-8")
        completed, payload = self.invoke("adopt", apply=True)
        self.assertEqual(completed.returncode, 0, payload)
        self.assertIn("Keep project instructions.", (self.repo / "AGENTS.md").read_text(encoding="utf-8"))
        self.assertTrue((existing / "unrelated.toml").exists())

    def test_collision_refuses_without_writes(self):
        (self.repo / "AGENTS.md").write_text("conflict\n", encoding="utf-8")
        before = (self.repo / "AGENTS.md").read_text(encoding="utf-8")
        completed, payload = self.invoke("new", apply=True)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("AGENTS.md", payload["conflicts"])
        self.assertEqual((self.repo / "AGENTS.md").read_text(encoding="utf-8"), before)
        self.assertFalse((self.repo / ".agents" / "team" / "charter.md").exists())

    def test_refuses_path_and_symlink_escape(self):
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        (self.repo / ".agents").symlink_to(outside, target_is_directory=True)
        completed, payload = self.invoke("new", apply=True)
        self.assertEqual(completed.returncode, 1)
        self.assertTrue(payload["errors"])
        self.assertFalse((outside / "team").exists())

    def test_refuses_malformed_markers_and_persona_pins(self):
        (self.repo / "AGENTS.md").write_text("<!-- persistent-team-bootstrap:start -->\n", encoding="utf-8")
        completed, payload = self.invoke("adopt", apply=True)
        self.assertEqual(completed.returncode, 1)
        self.assertTrue(payload["errors"])
        (self.repo / "AGENTS.md").unlink()
        agents = self.repo / ".codex" / "agents"
        agents.mkdir(parents=True)
        (agents / "nightingale.toml").write_text('name = "Nightingale"\nmodel = "luna"\n', encoding="utf-8")
        completed, payload = self.invoke("adopt", apply=True)
        self.assertEqual(completed.returncode, 1)
        self.assertTrue(payload["errors"])

    def test_rejects_invalid_fixed_policy_and_boolean_writer_count(self):
        invalid = config(fixed_policy={"one_writer": False})
        self.write_config(invalid)
        completed, payload = self.invoke("new", apply=True)
        self.assertEqual(completed.returncode, 1)
        self.assertTrue(payload["errors"])
        self.write_config(config(writer_owner_count=True))
        completed, payload = self.invoke("new", apply=True)
        self.assertEqual(completed.returncode, 1)
        self.assertTrue(payload["errors"])
        self.write_config(config(writer_owner_count=2))
        completed, payload = self.invoke("new", apply=True)
        self.assertEqual(completed.returncode, 1)
        self.assertTrue(payload["errors"])

    def test_transition_requires_zero_then_acknowledged_single_writer(self):
        zero_handoff = config()["handoff"]
        zero_handoff.update({"old_writer_status": "stopped", "summary": "Prior work is handed over.", "verification": "Checks recorded.", "new_writer_acknowledgement": ""})
        zero = config(writer_owner_count=0, active_writer=None, handoff=zero_handoff)
        self.write_config(zero)
        completed, payload = self.invoke("new", apply=True)
        self.assertEqual(completed.returncode, 0, payload)
        self.write_config(config())
        completed, payload = self.invoke("validate")
        self.assertEqual(completed.returncode, 1)
        self.assertIn(".agents/team/team-state.json", payload["conflicts"])
        self.write_config(config())
        completed, payload = self.invoke("adopt", apply=True)
        self.assertEqual(completed.returncode, 0, payload)

    def test_active_writer_moves_through_zero_before_acknowledged_reactivation(self):
        self.apply()
        zero_handoff = config()["handoff"]
        zero_handoff["old_writer_status"] = "stopped"
        zero_handoff["new_writer_acknowledgement"] = ""
        self.write_config(config(writer_owner_count=0, active_writer=None, handoff=zero_handoff))
        stopped, payload = self.invoke("adopt", apply=True)
        self.assertEqual(stopped.returncode, 0, payload)
        self.assertEqual(json.loads((self.repo / ".agents/team/team-state.json").read_text(encoding="utf-8"))["writer_owner_count"], 0)
        self.write_config(config())
        active, payload = self.invoke("adopt", apply=True)
        self.assertEqual(active.returncode, 0, payload)

    def test_transition_refuses_static_charter_collision_without_writes(self):
        self.apply()
        charter = self.repo / ".agents/team/charter.md"
        charter.write_text("user-owned collision\n", encoding="utf-8")
        before = charter.read_bytes()
        zero_handoff = config()["handoff"]; zero_handoff.update({"old_writer_status": "stopped", "new_writer_acknowledgement": ""})
        self.write_config(config(writer_owner_count=0, active_writer=None, handoff=zero_handoff))
        completed, payload = self.invoke("adopt", apply=True)
        self.assertEqual(completed.returncode, 1)
        self.assertIn(".agents/team/charter.md", payload["conflicts"])
        self.assertEqual(charter.read_bytes(), before)

    def test_transition_rejects_invalid_bucky_policy_state(self):
        self.apply()
        state_path = self.repo / ".agents/team/team-state.json"
        state = json.loads(state_path.read_text(encoding="utf-8")); state["bucky_counted"] = True
        state_path.write_text(json.dumps(state), encoding="utf-8")
        zero_handoff = config()["handoff"]; zero_handoff.update({"old_writer_status": "stopped", "new_writer_acknowledgement": ""})
        self.write_config(config(writer_owner_count=0, active_writer=None, handoff=zero_handoff))
        completed, payload = self.invoke("adopt", apply=True)
        self.assertEqual(completed.returncode, 1)
        self.assertTrue(payload["errors"])

    def test_backup_to_install_fault_restores_original_bytes(self):
        self.apply()
        zero_handoff = config()["handoff"]; zero_handoff.update({"old_writer_status": "stopped", "new_writer_acknowledgement": ""})
        self.write_config(config(writer_owner_count=0, active_writer=None, handoff=zero_handoff))
        state_path = self.repo / ".agents/team/team-state.json"; before = state_path.read_bytes()
        completed = subprocess.run([sys.executable, str(BOOTSTRAP), "--repo", str(self.repo), "--config", str(self.config_path), "--mode", "adopt", "--apply"], env=os.environ | {"PERSISTENT_TEAM_BOOTSTRAP_TEST_MODE": "1", "PERSISTENT_TEAM_BOOTSTRAP_FAIL_BETWEEN_BACKUP_AND_INSTALL": "1"}, text=True, capture_output=True, check=False)
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(completed.stderr, "")
        self.assertEqual(state_path.read_bytes(), before)

    def test_model_continuity_and_optional_pulse_do_not_manufacture_work(self):
        self.apply()
        policy = (self.repo / ".agents" / "team" / "model-handoff.md").read_text(encoding="utf-8")
        self.assertIn("gpt-5.6-terra", policy)
        self.assertIn("not_advertised_in_this_runtime", policy)
        pulse = self.repo / ".agents" / "skills" / "team-pulse" / "scripts" / "run_pulse.py"
        completed = subprocess.run([sys.executable, str(pulse), "--repo", str(self.repo), "--dry-run"], text=True, capture_output=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(sorted(payload), ["Boundary", "Experiment", "Friction", "Keep", "State"])
        self.assertEqual(payload["Experiment"], "")
        self.assertFalse((self.repo / ".agents" / "team" / "tasks").exists())

    def test_model_change_requires_a_safe_handoff_and_force_is_not_an_option(self):
        unsafe = config(handoff={"old_writer_status": "active", "summary": "Incomplete boundary.", "verification": "Not enough.", "new_writer_acknowledgement": "Nightingale accepts."})
        self.write_config(unsafe)
        completed, payload = self.invoke("new", apply=True)
        self.assertEqual(completed.returncode, 1)
        self.assertTrue(payload["errors"])
        forced = subprocess.run([sys.executable, str(BOOTSTRAP), "--repo", str(self.repo), "--config", str(self.config_path), "--mode", "new", "--force"], text=True, capture_output=True, check=False)
        self.assertEqual(forced.returncode, 2)

    def test_json_contract_and_argparse_contract(self):
        completed, payload = self.invoke("new")
        self.assertEqual(sorted(payload), ["apply", "conflicts", "created", "errors", "mode", "unchanged"])
        invalid = subprocess.run([sys.executable, str(BOOTSTRAP)], text=True, capture_output=True, check=False)
        self.assertEqual(invalid.returncode, 2)

    def test_portable_persona_and_seat_templates_are_model_neutral(self):
        for seat in ("bucky", "nightingale", "hubble", "scout"):
            template = PACKAGE / "templates" / "personas" / f"{seat}.toml.tmpl"
            contents = template.read_text(encoding="utf-8")
            self.assertIn("developer_instructions", contents)
            self.assertNotIn("model =", contents)
            self.assertNotIn("model_reasoning_effort", contents)
        self.assertTrue((PACKAGE / "templates" / "seat-record.md").is_file())

    def test_generated_personas_have_parsed_sandbox_modes(self):
        self.apply()
        expected = {"bucky": "workspace-write", "nightingale": "workspace-write", "hubble": "read-only", "scout": "read-only"}
        for seat, sandbox in expected.items():
            parsed = tomllib.loads((self.repo / ".codex" / "agents" / f"{seat}.toml").read_text(encoding="utf-8"))
            self.assertEqual(parsed["sandbox_mode"], sandbox)
            self.assertNotIn("model", parsed)
            self.assertNotIn("model_reasoning_effort", parsed)

    def test_adopt_inserts_markers_and_preserves_unrelated_content_idempotently(self):
        original = "# Existing instructions\n\nKeep this exact text.\n"
        (self.repo / "AGENTS.md").write_text(original, encoding="utf-8")
        completed, payload = self.invoke("adopt", apply=True)
        self.assertEqual(completed.returncode, 0, payload)
        installed = (self.repo / "AGENTS.md").read_text(encoding="utf-8")
        self.assertTrue(installed.startswith(original))
        self.assertEqual(installed.count("<!-- persistent-team-bootstrap:start -->"), 1)
        repeated, next_payload = self.invoke("adopt", apply=True)
        self.assertEqual(repeated.returncode, 0, next_payload)
        self.assertEqual((self.repo / "AGENTS.md").read_text(encoding="utf-8"), installed)

    def test_apply_is_atomic_when_publication_is_injected_to_fail(self):
        before = sorted(path.relative_to(self.repo).as_posix() for path in self.repo.rglob("*") if path.is_file())
        environment = os.environ | {"PERSISTENT_TEAM_BOOTSTRAP_TEST_MODE": "1", "PERSISTENT_TEAM_BOOTSTRAP_FAIL_AFTER": "1"}
        completed = subprocess.run([sys.executable, str(BOOTSTRAP), "--repo", str(self.repo), "--config", str(self.config_path), "--mode", "new", "--apply"], text=True, capture_output=True, env=environment, check=False)
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(completed.stderr, "")
        self.assertTrue(json.loads(completed.stdout)["errors"])
        after = sorted(path.relative_to(self.repo).as_posix() for path in self.repo.rglob("*") if path.is_file())
        self.assertEqual(after, before)

    def test_rejects_directory_target_regular_file_ancestor_reversed_markers_and_invalid_utf8(self):
        (self.repo / ".codex").write_text("not a directory", encoding="utf-8")
        completed, payload = self.invoke("new", apply=True)
        self.assertEqual(completed.returncode, 1)
        self.assertTrue(payload["errors"])
        (self.repo / ".codex").unlink()
        (self.repo / "AGENTS.md").write_text("<!-- persistent-team-bootstrap:end -->\n<!-- persistent-team-bootstrap:start -->\n", encoding="utf-8")
        completed, payload = self.invoke("adopt", apply=True)
        self.assertEqual(completed.returncode, 1)
        self.assertTrue(payload["errors"])
        (self.repo / "AGENTS.md").write_bytes(b"\xff\xfe")
        completed, payload = self.invoke("adopt", apply=True)
        self.assertEqual(completed.returncode, 1)
        self.assertTrue(payload["errors"])

    def test_catalog_is_a_provenanced_closed_snapshot_and_derives_the_request(self):
        value = config()
        value["catalog"] = {
            "source": "active-runtime:model/list",
            "pairs": [
                {"model": "gpt-5.6-terra", "effort": effort}
                for effort in ("low", "medium", "high", "xhigh")
            ],
        }
        value["handoff"]["requested_model"] = "gpt-5.6-terra"
        value["handoff"]["requested_effort"] = "xhigh"
        value["handoff"]["tightly_specified"] = False
        value["model_selection"] = {
            "current": {"model": "gpt-5.6-terra", "effort": "xhigh"},
            "recommended": {"model": "gpt-5.6-terra", "effort": "xhigh"},
            "luna_status": "not_advertised_in_this_runtime",
        }
        self.write_config(value)
        completed, payload = self.invoke("new")
        self.assertEqual(completed.returncode, 0, payload)
        for bad_source in ("spawn", "", None):
            value["catalog"]["source"] = bad_source
            self.write_config(value)
            completed, payload = self.invoke("new")
            self.assertEqual(completed.returncode, 1)
            self.assertTrue(payload["errors"])
        value["catalog"]["source"] = "active-runtime:model/list"
        value["catalog"]["pairs"].append({"model": "gpt-5.6-terra", "effort": "xhigh"})
        self.write_config(value)
        completed, payload = self.invoke("new")
        self.assertEqual(completed.returncode, 1)
        self.assertTrue(payload["errors"])

    def test_luna_recommendation_requires_advertised_xhigh_and_true_boolean(self):
        value = config()
        value["catalog"] = {"source": "active-runtime:model/list", "pairs": [
            {"model": "gpt-5.6-luna", "effort": "xhigh"},
            {"model": "gpt-5.6-terra", "effort": "high"},
        ]}
        value["handoff"].update({"requested_model": "gpt-5.6-luna", "requested_effort": "xhigh", "tightly_specified": True})
        value["model_selection"] = {"current": {"model": "gpt-5.6-luna", "effort": "xhigh"}, "recommended": {"model": "gpt-5.6-luna", "effort": "xhigh"}, "luna_status": "advertised"}
        self.write_config(value)
        completed, payload = self.invoke("new")
        self.assertEqual(completed.returncode, 0, payload)
        for not_tight in (False, "not tightly specified", 1):
            value["handoff"]["tightly_specified"] = not_tight
            value["handoff"]["requested_model"] = "gpt-5.6-terra"
            value["handoff"]["requested_effort"] = "high"
            value["model_selection"]["current"] = {"model": "gpt-5.6-terra", "effort": "high"}
            value["model_selection"]["recommended"] = {"model": "gpt-5.6-terra", "effort": "high"}
            self.write_config(value)
            completed, payload = self.invoke("new")
            self.assertEqual(completed.returncode, 0 if type(not_tight) is bool else 1, payload)

    def test_recognition_wording_is_optional_and_toml_and_markdown_inputs_are_safe(self):
        for wording in (None, "A safe custom recognition sentence."):
            value = config(recognition_wording=wording)
            self.write_config(value)
            completed, payload = self.invoke("new")
            self.assertEqual(completed.returncode, 0, payload)
        value = config(); value.pop("recognition_wording")
        self.write_config(value)
        completed, payload = self.invoke("new")
        self.assertEqual(completed.returncode, 0, payload)
        quoted = config()
        quoted["seats"]["nightingale"]["display_name"] = 'Nightingale "\\ reviewer'
        self.write_config(quoted)
        completed, payload = self.invoke("new", apply=True)
        self.assertEqual(completed.returncode, 0, payload)
        self.assertEqual(tomllib.loads((self.repo / ".codex/agents/nightingale.toml").read_text(encoding="utf-8"))["name"], 'Nightingale "\\ reviewer')
        before = sorted((p.relative_to(self.repo).as_posix(), p.read_bytes()) for p in self.repo.rglob("*") if p.is_file() and p != self.config_path)
        unsafe = config(human_authority="Dan\nWebb")
        self.write_config(unsafe)
        completed, payload = self.invoke("new", apply=True)
        self.assertEqual(completed.returncode, 1)
        self.assertTrue(payload["errors"])
        after = sorted((p.relative_to(self.repo).as_posix(), p.read_bytes()) for p in self.repo.rglob("*") if p.is_file() and p != self.config_path)
        self.assertEqual(after, before)

    def test_model_pair_changes_require_zero_then_acknowledged_reactivation_in_both_directions(self):
        self.apply()

        def luna_state(count, current):
            value = config()
            value["catalog"] = {"source": "active-runtime:model/list", "pairs": [
                {"model": "gpt-5.6-luna", "effort": "xhigh"},
                {"model": "gpt-5.6-terra", "effort": "high"},
            ]}
            value["handoff"].update({"requested_model": "gpt-5.6-luna", "requested_effort": "xhigh", "tightly_specified": True, "old_writer_status": "stopped" if count == 0 else "idle", "new_writer_acknowledgement": "" if count == 0 else "Nightingale accepts sole implementation ownership."})
            value["writer_owner_count"] = count
            value["active_writer"] = None if count == 0 else "nightingale"
            value["model_selection"] = {"current": current, "recommended": {"model": "gpt-5.6-luna", "effort": "xhigh"}, "luna_status": "advertised"}
            return value

        self.write_config(luna_state(1, {"model": "gpt-5.6-luna", "effort": "xhigh"}))
        direct, payload = self.invoke("adopt", apply=True)
        self.assertEqual(direct.returncode, 1, payload)
        self.assertIn(".agents/team/team-state.json", payload["conflicts"])
        self.write_config(luna_state(0, {"model": "gpt-5.6-terra", "effort": "high"}))
        stopped, payload = self.invoke("adopt", apply=True)
        self.assertEqual(stopped.returncode, 0, payload)
        self.write_config(luna_state(1, {"model": "gpt-5.6-luna", "effort": "xhigh"}))
        resumed, payload = self.invoke("adopt", apply=True)
        self.assertEqual(resumed.returncode, 0, payload)
        current = json.loads((self.repo / ".agents/team/team-state.json").read_text(encoding="utf-8"))
        self.assertEqual((current["selected_model"], current["selected_effort"]), ("gpt-5.6-luna", "xhigh"))

        terra_zero = config(writer_owner_count=0, active_writer=None)
        terra_zero["handoff"].update({"old_writer_status": "stopped", "new_writer_acknowledgement": ""})
        terra_zero["model_selection"]["current"] = {"model": "gpt-5.6-luna", "effort": "xhigh"}
        self.write_config(terra_zero)
        stopped, payload = self.invoke("adopt", apply=True)
        self.assertEqual(stopped.returncode, 0, payload)
        self.write_config(config())
        resumed, payload = self.invoke("adopt", apply=True)
        self.assertEqual(resumed.returncode, 0, payload)
        current = json.loads((self.repo / ".agents/team/team-state.json").read_text(encoding="utf-8"))
        self.assertEqual((current["selected_model"], current["selected_effort"]), ("gpt-5.6-terra", "high"))

    def test_validate_is_tree_read_only_and_rejects_symlinked_agents_preflight(self):
        self.apply()
        before = sorted((p.relative_to(self.repo).as_posix(), p.read_bytes()) for p in self.repo.rglob("*") if p.is_file())
        completed, payload = self.invoke("validate")
        self.assertEqual(completed.returncode, 0, payload)
        after = sorted((p.relative_to(self.repo).as_posix(), p.read_bytes()) for p in self.repo.rglob("*") if p.is_file())
        self.assertEqual(after, before)
        agents = self.repo / "AGENTS.md"
        agents.unlink()
        outside = Path(self.temp.name) / "outside-agents.md"
        outside.write_text("outside\n", encoding="utf-8")
        agents.symlink_to(outside)
        completed, payload = self.invoke("adopt", apply=True)
        self.assertEqual(completed.returncode, 1)
        self.assertTrue(payload["errors"])

    def test_pulse_contract_marks_each_exact_field_optional_without_side_effects(self):
        contents = (PACKAGE / "templates" / "team-pulse.md").read_text(encoding="utf-8")
        self.assertIn("State, Keep, Friction, Boundary, and Experiment", contents)
        self.assertIn("Each field is optional", contents)
        self.assertIn("read-only", contents)
        self.assertIn("stores no raw responses", contents)
        self.assertIn("cannot change policy", contents)
        self.assertIn("cannot create or manufacture work automatically", contents)

    def test_legacy_active_state_can_only_migrate_through_the_safe_zero_boundary(self):
        self.apply()
        state_path = self.repo / ".agents/team/team-state.json"
        legacy = json.loads(state_path.read_text(encoding="utf-8"))
        legacy.pop("requested_model")
        legacy.pop("requested_effort")
        legacy["handoff"].pop("tightly_specified")
        state_path.write_text(json.dumps(legacy), encoding="utf-8")
        zero = config(writer_owner_count=0, active_writer=None)
        zero["handoff"].update({"old_writer_status": "stopped", "new_writer_acknowledgement": ""})
        self.write_config(zero)
        completed, payload = self.invoke("adopt", apply=True)
        self.assertEqual(completed.returncode, 0, payload)
        persisted = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(persisted["writer_owner_count"], 0)
        self.assertIn("requested_model", persisted)

    def test_only_the_known_prior_generated_pulse_is_a_transition_artifact(self):
        self.apply()
        pulse = self.repo / ".agents/skills/team-pulse/SKILL.md"
        pulse.write_text("---\nname: team-pulse\ndescription: Run an optional read-only five-field pulse that cannot create work.\n---\n\n# Team pulse\n\nUse exactly five fields: State, Keep, Friction, Boundary, and Experiment.\nIt is optional and read-only, stores no raw responses, cannot change policy,\nand cannot create or manufacture work automatically.\n", encoding="utf-8")
        zero = config(writer_owner_count=0, active_writer=None)
        zero["handoff"].update({"old_writer_status": "stopped", "new_writer_acknowledgement": ""})
        self.write_config(zero)
        completed, payload = self.invoke("adopt", apply=True)
        self.assertEqual(completed.returncode, 0, payload)
        self.assertIn("Each field is optional", pulse.read_text(encoding="utf-8"))

    def test_failing_validate_leaves_the_complete_tree_byte_for_byte_unchanged(self):
        self.apply()
        invalid = config(fixed_policy={"one_writer": False})
        self.write_config(invalid)
        before = sorted((p.relative_to(self.repo).as_posix(), p.read_bytes()) for p in self.repo.rglob("*") if p.is_file())
        completed, payload = self.invoke("validate")
        self.assertEqual(completed.returncode, 1, payload)
        self.assertEqual(completed.stderr, "")
        self.assertTrue(payload["errors"])
        after = sorted((p.relative_to(self.repo).as_posix(), p.read_bytes()) for p in self.repo.rglob("*") if p.is_file())
        self.assertEqual(after, before)

    def test_descriptor_walk_refuses_an_ancestor_swapped_to_a_symlink(self):
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        (outside / "team").mkdir()
        outside_target = outside / "team" / "race.txt"
        outside_target.write_text("outside bytes", encoding="utf-8")
        (self.repo / ".agents").mkdir()
        desired = {".agents/team/race.txt": "managed bytes\n"}
        original = bootstrap.replace_relative
        swapped = False

        def swap_before_install(root_fd, source, target, create_target_parent=False):
            nonlocal swapped
            if not swapped and target == ".agents/team/race.txt":
                swapped = True
                (self.repo / ".agents").rename(self.repo / ".agents-original")
                (self.repo / ".agents").symlink_to(outside, target_is_directory=True)
            return original(root_fd, source, target, create_target_parent)

        root_fd = bootstrap.open_repo_fd(self.repo)
        try:
            with mock.patch.object(bootstrap, "replace_relative", side_effect=swap_before_install):
                failure = bootstrap.publish(root_fd, desired, [".agents/team/race.txt"])
        finally:
            os.close(root_fd)
        self.assertIn("publication failed", failure or "")
        self.assertEqual(outside_target.read_text(encoding="utf-8"), "outside bytes")

    def test_failed_restore_keeps_the_original_backup_and_reports_its_path(self):
        self.apply()
        zero_handoff = config()["handoff"]
        zero_handoff.update({"old_writer_status": "stopped", "new_writer_acknowledgement": ""})
        self.write_config(config(writer_owner_count=0, active_writer=None, handoff=zero_handoff))
        original = self.repo / ".agents/team/handoffs/TEMPLATE.md"
        before = original.read_bytes()
        completed = subprocess.run(
            [sys.executable, str(BOOTSTRAP), "--repo", str(self.repo), "--config", str(self.config_path), "--mode", "adopt", "--apply"],
            env=os.environ | {"PERSISTENT_TEAM_BOOTSTRAP_TEST_MODE": "1", "PERSISTENT_TEAM_BOOTSTRAP_FAIL_BETWEEN_BACKUP_AND_INSTALL": "1", "PERSISTENT_TEAM_BOOTSTRAP_FAIL_RESTORE": "1"},
            text=True,
            capture_output=True,
            check=False,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        retained = [path for path in self.repo.iterdir() if path.name.startswith(".persistent-team-stage-")]
        self.assertEqual(len(retained), 1)
        recovery = retained[0] / ".backup/.agents/team/handoffs/TEMPLATE.md"
        self.assertTrue(recovery.is_file(), (payload, [path.relative_to(retained[0]).as_posix() for path in retained[0].rglob("*")]))
        self.assertEqual(recovery.read_bytes(), before)
        self.assertIn(retained[0].name, " ".join(payload["errors"]))

    def test_legacy_state_rejects_boolean_count_and_incomplete_handoff(self):
        self.apply()
        state_path = self.repo / ".agents/team/team-state.json"
        legacy = json.loads(state_path.read_text(encoding="utf-8"))
        legacy.pop("requested_model")
        legacy.pop("requested_effort")
        legacy["handoff"].pop("tightly_specified")
        legacy["writer_owner_count"] = True
        state_path.write_text(json.dumps(legacy), encoding="utf-8")
        zero = config(writer_owner_count=0, active_writer=None)
        zero["handoff"].update({"old_writer_status": "stopped", "new_writer_acknowledgement": ""})
        self.write_config(zero)
        completed, payload = self.invoke("adopt", apply=True)
        self.assertEqual(completed.returncode, 1, payload)
        legacy["writer_owner_count"] = 1
        legacy["handoff"]["summary"] = ""
        state_path.write_text(json.dumps(legacy), encoding="utf-8")
        completed, payload = self.invoke("adopt", apply=True)
        self.assertEqual(completed.returncode, 1, payload)

    def test_rejects_del_and_invalid_rendered_personas_before_success(self):
        self.write_config(config(human_authority="Dan\x7fWebb"))
        completed, payload = self.invoke("new")
        self.assertEqual(completed.returncode, 1, payload)
        self.write_config(config())
        with mock.patch.object(bootstrap, "persona_file", return_value='name = "unterminated'):
            code, payload = bootstrap.run(self.repo, self.config_path, "new", False)
        self.assertEqual(code, 1, payload)
        self.assertTrue(any("rendered persona is invalid TOML" in error for error in payload["errors"]))

    def test_run_refuses_an_intermediate_absolute_repo_ancestor_swap_before_root_open(self):
        holder = Path(self.temp.name) / "holder"
        holder.mkdir()
        self.repo.rename(holder / "repo")
        self.repo = holder / "repo"
        self.config_path = self.repo / "bootstrap.json"
        ancestor = holder
        original_ancestor = Path(self.temp.name) / "holder-original"
        original_repo = original_ancestor / "repo"
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        original_files = sorted((path.relative_to(self.repo).as_posix(), path.read_bytes()) for path in self.repo.rglob("*") if path.is_file())
        original_open = bootstrap.open_repo_fd
        swapped = False

        def swap_before_root_open(repo):
            nonlocal swapped
            if not swapped:
                swapped = True
                ancestor.rename(original_ancestor)
                ancestor.symlink_to(outside, target_is_directory=True)
            return original_open(repo)

        with mock.patch.object(bootstrap, "open_repo_fd", side_effect=swap_before_root_open):
            code, payload = bootstrap.run(self.repo, self.config_path, "new", True)
        self.assertEqual(code, 1, payload)
        self.assertTrue(payload["errors"])
        self.assertFalse((outside / "AGENTS.md").exists())
        self.assertEqual(
            sorted((path.relative_to(original_repo).as_posix(), path.read_bytes()) for path in original_repo.rglob("*") if path.is_file()),
            original_files,
        )

    def test_malformed_catalog_pairs_return_contract_errors_without_tracebacks(self):
        for pairs in (None, 7, {"unexpected": "object"}):
            with self.subTest(pairs=pairs):
                value = config()
                value["catalog"]["pairs"] = pairs
                self.write_config(value)
                completed, payload = self.invoke("new")
                self.assertEqual(completed.returncode, 1, payload)
                self.assertEqual(sorted(payload), ["apply", "conflicts", "created", "errors", "mode", "unchanged"])
                self.assertTrue(payload["errors"])

    def test_invalid_relative_config_paths_return_contract_errors_without_writes(self):
        before = sorted((path.relative_to(self.repo).as_posix(), path.read_bytes()) for path in self.repo.rglob("*") if path.is_file())
        for relative in (".", "", "a/../b"):
            with self.subTest(relative=relative):
                command = [sys.executable, str(BOOTSTRAP), "--repo", str(self.repo), "--config", relative, "--mode", "new", "--apply"]
                completed = subprocess.run(command, text=True, capture_output=True, check=False)
                self.assertEqual(completed.returncode, 1)
                self.assertEqual(completed.stderr, "")
                self.assertTrue(json.loads(completed.stdout)["errors"])
        after = sorted((path.relative_to(self.repo).as_posix(), path.read_bytes()) for path in self.repo.rglob("*") if path.is_file())
        self.assertEqual(after, before)

    def test_validator_resolves_relative_config_inside_repo_when_called_elsewhere(self):
        self.apply()
        completed = subprocess.run(
            [sys.executable, str(VALIDATE), "--repo", str(self.repo), "--config", "bootstrap.json"],
            cwd=self.temp.name,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(completed.stderr, "")

    def test_replace_relative_closes_source_descriptor_when_target_open_fails(self):
        source_fd = os.open(self.repo, os.O_RDONLY)
        with mock.patch.object(bootstrap, "open_parent_fd", side_effect=[(source_fd, "source", []), OSError("target traversal failed")]), mock.patch.object(bootstrap.os, "close", wraps=os.close) as close:
            with self.assertRaisesRegex(OSError, "target traversal failed"):
                bootstrap.replace_relative(source_fd, "source", "target")
        self.assertIn(mock.call(source_fd), close.call_args_list)

    def test_differing_managed_agents_block_is_a_conflict_even_for_safe_transition(self):
        self.apply()
        agents = self.repo / "AGENTS.md"
        before = agents.read_bytes()
        agents.write_text(agents.read_text(encoding="utf-8").replace("Dan Webb", "Different authority"), encoding="utf-8")
        changed = agents.read_bytes()
        zero = config(writer_owner_count=0, active_writer=None)
        zero["handoff"].update({"old_writer_status": "stopped", "new_writer_acknowledgement": ""})
        self.write_config(zero)
        completed, payload = self.invoke("adopt", apply=True)
        self.assertEqual(completed.returncode, 1, payload)
        self.assertIn("AGENTS.md", payload["conflicts"])
        self.assertEqual(agents.read_bytes(), changed)
        self.assertNotEqual(changed, before)

    def test_incomplete_zero_state_is_refused_and_low_effort_beats_ultra(self):
        value = config()
        value["catalog"]["pairs"] = [{"model": "gpt-5.6-terra", "effort": "low"}, {"model": "gpt-5.6-terra", "effort": "ultra"}]
        value["handoff"].update({"requested_model": "gpt-5.6-terra", "requested_effort": "low"})
        value["model_selection"]["current"] = {"model": "gpt-5.6-terra", "effort": "low"}
        value["model_selection"]["recommended"] = {"model": "gpt-5.6-terra", "effort": "low"}
        self.write_config(value)
        completed, payload = self.invoke("new")
        self.assertEqual(completed.returncode, 0, payload)
        self.write_config(config())
        self.apply()
        state_path = self.repo / ".agents/team/team-state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["writer_owner_count"] = 0
        state["active_writer"] = None
        state["handoff"].pop("summary")
        state_path.write_text(json.dumps(state), encoding="utf-8")
        zero = config(writer_owner_count=0, active_writer=None)
        zero["handoff"].update({"old_writer_status": "stopped", "new_writer_acknowledgement": ""})
        self.write_config(zero)
        completed, payload = self.invoke("adopt", apply=True)
        self.assertEqual(completed.returncode, 1, payload)
        self.assertTrue(payload["errors"])

    def test_fault_switches_are_ignored_without_explicit_test_mode(self):
        completed = subprocess.run(
            [sys.executable, str(BOOTSTRAP), "--repo", str(self.repo), "--config", str(self.config_path), "--mode", "new", "--apply"],
            env=os.environ | {"PERSISTENT_TEAM_BOOTSTRAP_FAIL_AFTER": "1"},
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
