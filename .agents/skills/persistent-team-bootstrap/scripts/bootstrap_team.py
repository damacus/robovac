#!/usr/bin/env python3
"""Create, adopt, or validate a transactional persistent Codex team."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import stat
import tomllib
from typing import Any
import uuid


START = "<!-- persistent-team-bootstrap:start -->"
END = "<!-- persistent-team-bootstrap:end -->"
SEATS = ("bucky", "nightingale", "hubble", "scout")
FIXED_POLICY = {"one_writer": True, "safe_handoff": True, "redaction": True, "routing": "explicit", "sandbox": "fixed"}
TOP_LEVEL = {"human_authority", "seats", "writer_owner_count", "active_writer", "handoff", "fixed_policy", "catalog", "model_selection", "verification"}
HANDOFF = {"objective", "owned_paths", "baseline", "dirty_paths", "checks", "findings", "next_action", "requested_model", "requested_effort", "requested_reason", "tightly_specified", "old_writer_status", "new_writer_acknowledgement", "summary", "verification"}
SELECTION = {"current", "recommended", "luna_status"}
PAIR = {"model", "effort"}
PERSISTED_STATE = {"active_writer", "bucky_counted", "writer_owner_count", "selected_model", "selected_effort", "requested_model", "requested_effort", "handoff"}
PRIOR_PULSE_SKILL = """---
name: team-pulse
description: Run an optional read-only five-field pulse that cannot create work.
---

# Team pulse

Use exactly five fields: State, Keep, Friction, Boundary, and Experiment.
It is optional and read-only, stores no raw responses, cannot change policy,
and cannot create or manufacture work automatically.
"""
RESULT_KEYS = ("mode", "apply", "created", "unchanged", "conflicts", "errors")
PACKAGE = Path(__file__).resolve().parents[1]


def result(mode: str, apply: bool) -> dict[str, Any]:
    return {"mode": mode, "apply": apply, "created": [], "unchanged": [], "conflicts": [], "errors": []}


def add(out: dict[str, Any], key: str, value: str) -> None:
    if value not in out[key]: out[key].append(value)


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def template(name: str) -> str:
    return text(PACKAGE / "templates" / name)


def render(name: str, values: dict[str, str]) -> str:
    output = template(name)
    for key, value in values.items(): output = output.replace("{{ " + key + " }}", value)
    return output


def is_within(repo: Path, path: Path) -> bool:
    try: path.relative_to(repo); path.resolve(strict=False).relative_to(repo.resolve(strict=True)); return True
    except (OSError, ValueError): return False

def repo_path_is_safe(repo: Path) -> bool:
    current = Path(repo.anchor)
    try:
        for part in repo.parts[1:]:
            current = current / part
            if current.is_symlink() and current != Path("/var"): return False
    except OSError: return False
    return True


def preflight_path(repo: Path, path: Path, target: bool = True) -> str | None:
    if not is_within(repo, path): return "path escape"
    current = repo
    try:
        if current.is_symlink() or not current.is_dir(): return "repo is not a real directory"
        parts = path.relative_to(repo).parts
        for index, part in enumerate(parts):
            current = current / part
            if not current.exists() and not current.is_symlink(): continue
            stat = current.lstat()
            if current.is_symlink(): return "symlink path component"
            if index < len(parts) - 1 and not current.is_dir(): return "regular-file ancestor"
            if index == len(parts) - 1 and target and current.is_dir(): return "directory target"
    except OSError: return "unreadable path"
    return None

DIR_FLAGS = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)


def relative_parts(rel: str) -> tuple[str, ...]:
    """Reject anything other than a repository-relative destination."""
    parts = Path(rel).parts
    if not parts or Path(rel).is_absolute() or any(part in ("", ".", "..") for part in parts):
        raise OSError("unsafe relative destination")
    return parts


def open_repo_fd(repo: Path) -> int:
    """Hold one no-follow descriptor for the repository for the whole publish."""
    if not repo.is_absolute():
        raise OSError("repository path must be absolute")
    fd = os.open(repo.anchor, DIR_FLAGS)
    try:
        for component in repo.parts[1:]:
            next_fd = os.open(component, DIR_FLAGS, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        return fd
    except BaseException:
        os.close(fd)
        raise


def open_parent_fd(root_fd: int, rel: str, create: bool = False) -> tuple[int, str, list[str]]:
    """Walk a relative path with openat semantics; never follow an ancestor."""
    parts = relative_parts(rel)
    fd = os.dup(root_fd)
    created: list[str] = []
    prefix: list[str] = []
    try:
        for part in parts[:-1]:
            prefix.append(part)
            try:
                next_fd = os.open(part, DIR_FLAGS, dir_fd=fd)
            except FileNotFoundError:
                if not create:
                    raise
                os.mkdir(part, dir_fd=fd)
                created.append("/".join(prefix))
                next_fd = os.open(part, DIR_FLAGS, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        return fd, parts[-1], created
    except BaseException:
        os.close(fd)
        raise


def exists_at(parent_fd: int, name: str) -> bool:
    try:
        os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        return True
    except FileNotFoundError:
        return False


def entry_at(root_fd: int, rel: str) -> os.stat_result | None:
    try:
        parent_fd, name, _ = open_parent_fd(root_fd, rel)
    except FileNotFoundError:
        return None
    try:
        try:
            return os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            return None
    finally:
        os.close(parent_fd)


def read_relative(root_fd: int, rel: str) -> str:
    parent_fd, name, _ = open_parent_fd(root_fd, rel)
    try:
        fd = os.open(name, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=parent_fd)
        try:
            chunks: list[bytes] = []
            while True:
                chunk = os.read(fd, 65536)
                if not chunk:
                    break
                chunks.append(chunk)
            return b"".join(chunks).decode("utf-8")
        finally:
            os.close(fd)
    finally:
        os.close(parent_fd)


def replace_relative(root_fd: int, source: str, target: str, create_target_parent: bool = False) -> list[str]:
    """Rename only basename entries beneath retained verified directory fds."""
    source_fd, source_name, _ = open_parent_fd(root_fd, source)
    try:
        target_fd, target_name, created = open_parent_fd(root_fd, target, create=create_target_parent)
    except BaseException:
        os.close(source_fd)
        raise
    try:
        os.replace(source_name, target_name, src_dir_fd=source_fd, dst_dir_fd=target_fd)
        return created
    finally:
        os.close(source_fd)
        os.close(target_fd)


def unlink_relative(root_fd: int, rel: str) -> None:
    parent_fd, name, _ = open_parent_fd(root_fd, rel)
    try:
        os.unlink(name, dir_fd=parent_fd)
    finally:
        os.close(parent_fd)


def rmdir_relative(root_fd: int, rel: str) -> None:
    parent_fd, name, _ = open_parent_fd(root_fd, rel)
    try:
        os.rmdir(name, dir_fd=parent_fd)
    finally:
        os.close(parent_fd)


def write_relative(root_fd: int, rel: str, content: str) -> list[str]:
    parent_fd, name, created = open_parent_fd(root_fd, rel, create=True)
    try:
        fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600, dir_fd=parent_fd)
        try:
            data = content.encode("utf-8")
            while data:
                data = data[os.write(fd, data):]
        finally:
            os.close(fd)
        return created
    finally:
        os.close(parent_fd)


def remove_tree_relative(root_fd: int, rel: str) -> None:
    """Remove our private stage through descriptors only; never follow a swap."""
    parent_fd, name, _ = open_parent_fd(root_fd, rel)
    try:
        child_fd = os.open(name, DIR_FLAGS, dir_fd=parent_fd)
        try:
            for entry in os.listdir(child_fd):
                entry_stat = os.stat(entry, dir_fd=child_fd, follow_symlinks=False)
                if stat.S_ISDIR(entry_stat.st_mode):
                    remove_tree_relative(child_fd, entry)
                else:
                    os.unlink(entry, dir_fd=child_fd)
        finally:
            os.close(child_fd)
        os.rmdir(name, dir_fd=parent_fd)
    finally:
        os.close(parent_fd)


def load_config(root_fd: int, config_rel: str, out: dict[str, Any]) -> dict[str, Any] | None:
    try:
        current = entry_at(root_fd, config_rel)
    except OSError:
        add(out, "errors", "config has an unsafe path component"); return None
    if current is None or stat.S_ISLNK(current.st_mode) or not stat.S_ISREG(current.st_mode):
        add(out, "errors", "config must be a readable regular file"); return None
    try:
        value = json.loads(read_relative(root_fd, config_rel))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        add(out, "errors", "config must be readable UTF-8 JSON"); return None
    if not isinstance(value, dict): add(out, "errors", "config must be an object"); return None
    return value


def string(value: Any) -> bool: return isinstance(value, str) and bool(value.strip()) and not any(ord(char) < 32 or ord(char) == 127 for char in value)
def string_list(value: Any) -> bool: return isinstance(value, list) and all(string(item) for item in value)
def safe_scalar(value: Any) -> bool: return string(value) and START not in value and END not in value
def toml_literal(value: str) -> str: return json.dumps(value, ensure_ascii=False)


def advertised(config: dict[str, Any]) -> set[tuple[str, str]]:
    catalog = config.get("catalog", {}).get("pairs", []) if isinstance(config.get("catalog"), dict) else []
    if not isinstance(catalog, list):
        return set()
    return {(entry["model"], entry["effort"]) for entry in catalog if isinstance(entry, dict) and set(entry) == PAIR and string(entry.get("model")) and string(entry.get("effort"))}


def selected_pair(config: dict[str, Any]) -> tuple[str, str] | None:
    pairs = advertised(config); handoff = config.get("handoff", {})
    if ("gpt-5.6-luna", "xhigh") in pairs and handoff.get("tightly_specified") is True: return ("gpt-5.6-luna", "xhigh")
    # Prefer normal tightly-bounded efforts; max/ultra are last-resort capability tiers.
    for effort in ("xhigh", "high", "medium", "low", "max", "ultra"):
        if ("gpt-5.6-terra", effort) in pairs: return ("gpt-5.6-terra", effort)
    return None


def exact_pair(value: Any) -> tuple[str, str] | None:
    if not isinstance(value, dict) or set(value) != PAIR or not string(value.get("model")) or not string(value.get("effort")):
        return None
    return value["model"], value["effort"]


def legacy_active_state(value: Any) -> bool:
    """Recognize only the previous generated active state for a one-way zero migration."""
    legacy_keys = {"active_writer", "bucky_counted", "writer_owner_count", "selected_model", "selected_effort", "handoff"}
    legacy_handoff = HANDOFF - {"tightly_specified"}
    handoff = value.get("handoff") if isinstance(value, dict) else None
    return (
        isinstance(value, dict)
        and set(value) == legacy_keys
        and value.get("active_writer") == "nightingale"
        and value.get("bucky_counted") is False
        and type(value.get("writer_owner_count")) is int
        and value.get("writer_owner_count") == 1
        and string(value.get("selected_model"))
        and string(value.get("selected_effort"))
        and isinstance(handoff, dict)
        and set(handoff) == legacy_handoff
        and all(string(handoff.get(key)) for key in legacy_handoff - {"owned_paths", "dirty_paths", "checks", "new_writer_acknowledgement"})
        and all(string_list(handoff.get(key)) for key in ("owned_paths", "dirty_paths", "checks"))
        and handoff.get("old_writer_status") in ("stopped", "idle")
        and string(handoff.get("new_writer_acknowledgement"))
    )


def validate_config(config: dict[str, Any], out: dict[str, Any]) -> None:
    if set(config) not in (TOP_LEVEL, TOP_LEVEL | {"recognition_wording"}): add(out, "errors", "config has unknown or missing top-level keys")
    if not safe_scalar(config.get("human_authority")) or ("recognition_wording" in config and config["recognition_wording"] is not None and not safe_scalar(config["recognition_wording"])): add(out, "errors", "authority and recognition wording must be safe strings")
    seats = config.get("seats")
    if not isinstance(seats, dict) or set(seats) != set(SEATS) or any(not isinstance(seats.get(seat), dict) or set(seats[seat]) != {"display_name"} or not safe_scalar(seats[seat].get("display_name")) for seat in SEATS): add(out, "errors", "seats must contain only safe display names")
    if config.get("fixed_policy") != FIXED_POLICY: add(out, "errors", "fixed policy cannot be overridden")
    count = config.get("writer_owner_count")
    if isinstance(count, bool) or not isinstance(count, int) or count not in (0, 1): add(out, "errors", "writer_owner_count must be integer 0 or 1; Bucky is never counted")
    handoff = config.get("handoff")
    if not isinstance(handoff, dict) or set(handoff) != HANDOFF:
        add(out, "errors", "handoff must contain the complete closed schema"); return
    for key in HANDOFF - {"owned_paths", "dirty_paths", "checks", "new_writer_acknowledgement", "tightly_specified"}:
        if not string(handoff.get(key)): add(out, "errors", "handoff field " + key + " must be nonempty")
    for key in ("owned_paths", "dirty_paths", "checks"):
        if not string_list(handoff.get(key)): add(out, "errors", "handoff field " + key + " must be a string list")
    if handoff.get("old_writer_status") not in ("stopped", "idle"): add(out, "errors", "old writer must be stopped or idle")
    if type(handoff.get("tightly_specified")) is not bool: add(out, "errors", "tightly_specified must be an explicit boolean")
    if count == 0 and config.get("active_writer") is not None: add(out, "errors", "zero writer state cannot name an active writer")
    if count == 1 and config.get("active_writer") != "nightingale": add(out, "errors", "Nightingale is the sole active implementation owner")
    if count == 1 and not string(handoff.get("new_writer_acknowledgement")): add(out, "errors", "new writer acknowledgement is required")
    if count == 0 and handoff.get("new_writer_acknowledgement") not in ("", None): add(out, "errors", "zero writer state cannot acknowledge a new writer")
    catalog = config.get("catalog")
    if not isinstance(catalog, dict) or set(catalog) != {"source", "pairs"} or catalog.get("source") != "active-runtime:model/list" or not isinstance(catalog.get("pairs"), list) or not catalog["pairs"] or len(advertised(config)) != len(catalog["pairs"]): add(out, "errors", "catalog must be a unique active-runtime model/list snapshot")
    requested = handoff.get("requested_model"), handoff.get("requested_effort")
    if requested not in advertised(config): add(out, "errors", "requested model/effort is not advertised by the active catalog")
    selection = config.get("model_selection")
    pair = selected_pair(config)
    current = exact_pair(selection.get("current")) if isinstance(selection, dict) else None
    recommended = exact_pair(selection.get("recommended")) if isinstance(selection, dict) else None
    if not isinstance(selection, dict) or set(selection) != SELECTION or not pair or recommended != pair or requested != pair or current is None or selection.get("luna_status") not in ("advertised", "not_assessed", "not_advertised_in_this_runtime"):
        add(out, "errors", "model selection must derive from advertised catalog evidence")
    elif count == 1 and current != requested:
        add(out, "errors", "active writer must use the requested derived model/effort")
    verification = config.get("verification")
    if not isinstance(verification, dict) or set(verification) != {"narrow", "broad"} or not string_list(verification.get("narrow")) or not string_list(verification.get("broad")): add(out, "errors", "verification commands must be nonempty string lists")


def marker_state(existing: str) -> tuple[str, str | None]:
    starts = [i for i in range(len(existing)) if existing.startswith(START, i)]
    ends = [i for i in range(len(existing)) if existing.startswith(END, i)]
    if not starts and not ends: return "none", None
    if len(starts) != 1 or len(ends) != 1 or starts[0] > ends[0]: return "malformed", None
    return "valid", existing[starts[0]:ends[0] + len(END)]


def managed_block(config: dict[str, Any]) -> str:
    return render("AGENTS.managed.md", {"human_authority": config["human_authority"]}).replace("<!-- markdownlint-disable-file MD041 -->\n\n", "", 1).rstrip() + "\n"


def agents_file(root_fd: int, config: dict[str, Any], mode: str, out: dict[str, Any]) -> str:
    try:
        current = entry_at(root_fd, "AGENTS.md")
    except OSError:
        add(out, "errors", "AGENTS.md has an unsafe path component"); return ""
    if current is None: return "# Repository agent instructions\n\n" + managed_block(config)
    if stat.S_ISLNK(current.st_mode) or not stat.S_ISREG(current.st_mode):
        add(out, "errors", "AGENTS.md must be a readable regular file"); return ""
    try: existing = read_relative(root_fd, "AGENTS.md")
    except (OSError, UnicodeDecodeError): add(out, "errors", "AGENTS.md must be readable UTF-8"); return ""
    state, block = marker_state(existing)
    if state == "malformed": add(out, "errors", "AGENTS.md has malformed persistent-team-bootstrap markers"); return ""
    expected = managed_block(config).rstrip()
    if state == "valid":
        if block != expected:
            add(out, "conflicts", "AGENTS.md")
        return existing
    if mode == "new": add(out, "conflicts", "AGENTS.md"); return existing
    return existing.rstrip() + "\n\n" + managed_block(config)


def persona_file(seat: str, display_name: str) -> str:
    sandbox = "workspace-write" if seat in ("bucky", "nightingale") else "read-only"
    return render("personas/" + seat + ".toml.tmpl", {"display_name": toml_literal(display_name), "sandbox_mode": sandbox})


def files(config: dict[str, Any], agents: str) -> dict[str, str]:
    seats = config["seats"]; handoff = config["handoff"]; pair = selected_pair(config) or ("", ""); current = exact_pair(config["model_selection"]["current"]) or ("", "")
    commands = "\n".join("- `" + command + "`" for command in config["verification"]["narrow"] + config["verification"]["broad"])
    values = {"human_authority": config["human_authority"], "recognition_wording": config.get("recognition_wording") or "Recognition remains empty until a human records a reviewable contribution.", "verification_commands": commands, "selected_model": pair[0], "selected_effort": pair[1], "handoff_json": json.dumps(handoff, indent=2, sort_keys=True)}
    output = {
        "AGENTS.md": agents,
        ".agents/team/charter.md": render("charter.md", values),
        ".agents/team/handoffs/TEMPLATE.md": render("handoff.md", values),
        ".agents/team/handoffs/current.json": json.dumps(handoff, indent=2, sort_keys=True) + "\n",
        ".agents/team/team-state.json": json.dumps({"active_writer": config["active_writer"], "bucky_counted": False, "writer_owner_count": config["writer_owner_count"], "selected_model": current[0], "selected_effort": current[1], "requested_model": pair[0], "requested_effort": pair[1], "handoff": handoff}, indent=2, sort_keys=True) + "\n",
        ".agents/team/model-handoff.md": "# Model handoff\n\nCatalog provenance is the closed read-only `active-runtime:model/list` snapshot captured from the runtime model/list response. Catalog model values are portable advertised family/ID strings. Current selected pair: " + current[0] + " at " + current[1] + ". Requested derived pair: " + pair[0] + " at " + pair[1] + ". Luna status: " + config["model_selection"]["luna_status"] + ". Luna is selected only when gpt-5.6-luna xhigh is advertised and tightly_specified is exactly true; otherwise gpt-5.6-terra uses an advertised effort. A spawn result never proves global availability.\n",
        ".agents/team/verification.md": "# Verification\n\n" + commands + "\n",
        ".agents/team/recognition.json": render("recognition.json", values),
        ".agents/team/recognition-guidance.md": "# Recognition guidance\n\n" + values["recognition_wording"] + "\n",
        ".agents/team/routing-cases.md": render("routing-cases.md", values),
        ".agents/team/reports/README.md": "# Team reports\n\nDurable reports are bounded and redacted; no raw prompts, responses, or secrets.\n",
        ".agents/team/reports/TEMPLATE.md": render("report.md", values),
    }
    workflow_templates = {"team-planning": "team-planning.md", "team-tranche-development": "team-tranche-development.md", "team-improvement-loop": "team-improvement-loop.md", "team-pulse": "team-pulse.md"}
    for skill, source in workflow_templates.items(): output[".agents/skills/" + skill + "/SKILL.md"] = render(source, values)
    output[".agents/skills/team-improvement-loop/scripts/validate_team_setup.py"] = "#!/usr/bin/env python3\nfrom pathlib import Path\nimport sys\nr=Path.cwd(); sys.exit(0 if (r/'.agents/team/charter.md').is_file() and (r/'.agents/team/reports/TEMPLATE.md').is_file() else 1)\n"
    output[".agents/skills/team-improvement-loop/scripts/run_routing_evals.py"] = "#!/usr/bin/env python3\nimport argparse,json\np=argparse.ArgumentParser();p.add_argument('--repo',required=True);p.add_argument('--dry-run',action='store_true');a=p.parse_args();print(json.dumps({'dry_run':a.dry_run,'route':'read-only','work_created':False},sort_keys=True))\n"
    output[".agents/skills/team-pulse/scripts/run_pulse.py"] = "#!/usr/bin/env python3\nimport argparse,json\np=argparse.ArgumentParser();p.add_argument('--repo',required=True);p.add_argument('--dry-run',action='store_true');p.parse_args();print(json.dumps({'Boundary':'','Experiment':'','Friction':'','Keep':'','State':''},sort_keys=True))\n"
    for seat in SEATS:
        output[".codex/agents/" + seat + ".toml"] = persona_file(seat, seats[seat]["display_name"])
        output[".agents/team/seats/" + seat + ".md"] = render("seat-record.md", {"seat": seat, "display_name": seats[seat]["display_name"], "access": "workspace-write" if seat in ("bucky", "nightingale") else "read-only", "boundary": "integration-only" if seat == "bucky" else "sole implementation owner" if seat == "nightingale" else "read-only", "writer_owner_counted": "false" if seat == "bucky" else "true" if seat == "nightingale" else "false"})
    return output


def validate_rendered_personas(desired: dict[str, str], out: dict[str, Any]) -> None:
    """Parse every generated persona before either a dry-run or a write succeeds."""
    for seat in SEATS:
        rel = ".codex/agents/" + seat + ".toml"
        try:
            parsed = tomllib.loads(desired[rel])
        except (KeyError, tomllib.TOMLDecodeError):
            add(out, "errors", "rendered persona is invalid TOML: " + rel)
            continue
        if set(parsed) != {"name", "sandbox_mode", "developer_instructions"}:
            add(out, "errors", "rendered persona fields are invalid: " + rel)
        if "model" in parsed or "model_reasoning_effort" in parsed:
            add(out, "errors", "rendered persona pins a model: " + rel)


def inspect(root_fd: int, desired: dict[str, str], mode: str, out: dict[str, Any]) -> None:
    for rel, content in sorted(desired.items()):
        try:
            entry = entry_at(root_fd, rel)
        except OSError:
            add(out, "errors", "unsafe managed path: " + rel); continue
        if entry is None: add(out, "created", rel); continue
        if stat.S_ISLNK(entry.st_mode): add(out, "errors", "symlink path component: " + rel); continue
        if stat.S_ISDIR(entry.st_mode): add(out, "errors", "directory target: " + rel); continue
        if not stat.S_ISREG(entry.st_mode): add(out, "errors", "managed target must be a regular file: " + rel); continue
        try: current = read_relative(root_fd, rel)
        except (OSError, UnicodeDecodeError): add(out, "errors", "managed target must be readable UTF-8: " + rel); continue
        if rel == ".agents/team/team-state.json":
            try: persisted = json.loads(current)
            except json.JSONDecodeError: add(out, "errors", "invalid persisted state"); continue
            if not isinstance(persisted, dict) or set(persisted) != PERSISTED_STATE:
                if mode == "adopt" and legacy_active_state(persisted) and safe_transition(root_fd, desired[".agents/team/team-state.json"]):
                    add(out, "created", rel)
                else:
                    add(out, "errors", "persisted state must use the closed schema")
                continue
            if isinstance(persisted.get("writer_owner_count"), bool) or persisted.get("writer_owner_count") not in (0, 1): add(out, "errors", "persisted writer count must be integer 0 or 1"); continue
            if persisted.get("bucky_counted") is not False: add(out, "errors", "persisted Bucky policy is invalid"); continue
            if not all(string(persisted.get(key)) for key in ("selected_model", "selected_effort", "requested_model", "requested_effort")): add(out, "errors", "persisted model state is invalid"); continue
            persisted_handoff = persisted.get("handoff")
            if not isinstance(persisted_handoff, dict) or set(persisted_handoff) != HANDOFF or any(not string(persisted_handoff.get(key)) for key in HANDOFF - {"owned_paths", "dirty_paths", "checks", "new_writer_acknowledgement", "tightly_specified"}) or any(not string_list(persisted_handoff.get(key)) for key in ("owned_paths", "dirty_paths", "checks")) or persisted_handoff.get("old_writer_status") not in ("stopped", "idle") or type(persisted_handoff.get("tightly_specified")) is not bool:
                add(out, "errors", "persisted handoff state is invalid"); continue
        if rel.startswith(".codex/agents/"):
            try:
                parsed, expected = tomllib.loads(current), tomllib.loads(content)
            except tomllib.TOMLDecodeError: add(out, "errors", "invalid persona TOML: " + rel); continue
            if set(parsed) != {"name", "sandbox_mode", "developer_instructions"} or parsed != expected:
                add(out, "errors", "invalid persona fields: " + rel); continue
        if current == content: add(out, "unchanged", rel)
        elif mode == "adopt" and rel == "AGENTS.md" and marker_state(current)[0] == "none": add(out, "created", rel)
        elif mode == "adopt" and rel == ".agents/skills/team-pulse/SKILL.md" and current == PRIOR_PULSE_SKILL and safe_transition(root_fd, desired[".agents/team/team-state.json"]):
            add(out, "created", rel)
        elif mode == "adopt" and rel in {".agents/team/team-state.json", ".agents/team/handoffs/current.json", ".agents/team/handoffs/TEMPLATE.md", ".agents/team/model-handoff.md"} and safe_transition(root_fd, desired[".agents/team/team-state.json"]):
            add(out, "created", rel)
        else: add(out, "conflicts", rel)


def safe_transition(root_fd: int, desired_state: str) -> bool:
    try:
        old = json.loads(read_relative(root_fd, ".agents/team/team-state.json"))
        target = json.loads(desired_state)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError): return False
    if not isinstance(target, dict) or set(target) != PERSISTED_STATE: return False
    if legacy_active_state(old):
        return target.get("writer_owner_count") == 0 and target.get("active_writer") is None
    if set(old) != PERSISTED_STATE: return False
    if old.get("bucky_counted") is not False or not isinstance(old.get("handoff"), dict) or set(old["handoff"]) != HANDOFF: return False
    if any(not string(old["handoff"].get(key)) for key in HANDOFF - {"owned_paths", "dirty_paths", "checks", "new_writer_acknowledgement", "tightly_specified"}): return False
    if any(not string_list(old["handoff"].get(key)) for key in ("owned_paths", "dirty_paths", "checks")): return False
    if old["handoff"].get("old_writer_status") not in ("stopped", "idle"): return False
    if type(old["handoff"].get("tightly_specified")) is not bool: return False
    if not all(string(old.get(key)) for key in ("selected_model", "selected_effort", "requested_model", "requested_effort")): return False
    old_count, target_count = old.get("writer_owner_count"), target.get("writer_owner_count")
    if isinstance(old_count, bool) or isinstance(target_count, bool): return False
    return (
        (old_count == 1 and old.get("active_writer") == "nightingale" and old.get("selected_model") == old.get("requested_model") and old.get("selected_effort") == old.get("requested_effort") and target_count == 0 and target.get("active_writer") is None)
        or (old_count == 0 and old.get("active_writer") is None and target_count == 1 and target.get("active_writer") == "nightingale" and target.get("selected_model") == target.get("requested_model") and target.get("selected_effort") == target.get("requested_effort"))
    )


def publish(root_fd: int, desired: dict[str, str], changes: list[str]) -> str | None:
    stage_rel: str | None = None
    backups: list[tuple[str, str | None]] = []
    made: list[str] = []
    preserve_recovery = False
    try:
        stage_rel = ".persistent-team-stage-" + uuid.uuid4().hex
        os.mkdir(stage_rel, dir_fd=root_fd)
        for rel in changes:
            write_relative(root_fd, stage_rel + "/" + rel, desired[rel])
        test_mode = os.environ.get("PERSISTENT_TEAM_BOOTSTRAP_TEST_MODE") == "1"
        failure_after = int(os.environ.get("PERSISTENT_TEAM_BOOTSTRAP_FAIL_AFTER", "0")) if test_mode else 0; published = 0
        for rel in changes:
            target_fd, target_name, created = open_parent_fd(root_fd, rel, create=True)
            made.extend(created)
            try:
                if exists_at(target_fd, target_name):
                    if stat.S_ISDIR(os.stat(target_name, dir_fd=target_fd, follow_symlinks=False).st_mode): raise OSError("directory target")
                    backup_rel = stage_rel + "/.backup/" + rel
                    made.extend(replace_relative(root_fd, rel, backup_rel, create_target_parent=True))
                    backups.append((rel, backup_rel))
                else:
                    backups.append((rel, None))
            finally:
                os.close(target_fd)
            if backups[-1][1] is not None:
                if test_mode and os.environ.get("PERSISTENT_TEAM_BOOTSTRAP_FAIL_BETWEEN_BACKUP_AND_INSTALL") == "1": raise OSError("injected backup/install failure")
            made.extend(replace_relative(root_fd, stage_rel + "/" + rel, rel, create_target_parent=True)); published += 1
            if failure_after and published >= failure_after: raise OSError("injected publication failure")
        return None
    except (OSError, ValueError, UnicodeError) as exc:
        rollback_errors: list[str] = []
        for target, backup in reversed(backups):
            try:
                target_fd, target_name, _ = open_parent_fd(root_fd, target)
                try:
                    if exists_at(target_fd, target_name): os.unlink(target_name, dir_fd=target_fd)
                finally:
                    os.close(target_fd)
                if backup is not None:
                    if test_mode and os.environ.get("PERSISTENT_TEAM_BOOTSTRAP_FAIL_RESTORE") == "1": raise OSError("injected rollback restoration failure")
                    replace_relative(root_fd, backup, target, create_target_parent=True)
            except OSError as rollback_exc:
                rollback_errors.append(target + ": " + str(rollback_exc))
        for directory in reversed(made):
            try:
                rmdir_relative(root_fd, directory)
            except OSError: pass
        if rollback_errors:
            preserve_recovery = True
            return "publication failed: " + str(exc) + "; rollback failed: " + "; ".join(rollback_errors) + "; recovery retained at " + str(stage_rel)
        return "publication failed: " + str(exc)
    finally:
        if stage_rel is not None and not preserve_recovery:
            try: remove_tree_relative(root_fd, stage_rel)
            except OSError: pass


def run(repo: Path, config_path: Path, mode: str, apply: bool) -> tuple[int, dict[str, Any]]:
    out = result(mode, apply)
    root_fd: int | None = None
    try:
        try:
            root_fd = open_repo_fd(repo)
        except OSError:
            add(out, "errors", "repo must be a real directory without symlink ancestors")
            return 1, out
        try:
            config_rel = config_path.relative_to(repo).as_posix()
            relative_parts(config_rel)
        except (OSError, ValueError):
            add(out, "errors", "config path escape")
            return 1, out
        config = load_config(root_fd, config_rel, out)
        if config is not None: validate_config(config, out)
        desired: dict[str, str] = {}
        if config is not None and not out["errors"]:
            agents = agents_file(root_fd, config, mode, out); desired = files(config, agents) if not out["errors"] else {}
            if desired: validate_rendered_personas(desired, out)
            if not out["errors"]: inspect(root_fd, desired, mode, out)
        for key in ("created", "unchanged", "conflicts", "errors"): out[key].sort()
        if out["errors"] or out["conflicts"]: return 1, out
        if mode == "validate":
            if out["created"]: out["errors"].append("bootstrap state is incomplete"); return 1, out
            return 0, out
        if apply and out["created"]:
            failure = publish(root_fd, desired, out["created"])
            if failure: out["errors"].append(failure); out["errors"].sort(); return 1, out
        return 0, out
    finally:
        if root_fd is not None:
            os.close(root_fd)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--repo", required=True, type=Path); parser.add_argument("--config", required=True, type=Path); parser.add_argument("--mode", required=True, choices=("new", "adopt", "validate")); parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(); repo = args.repo.absolute(); config = args.config if args.config.is_absolute() else repo / args.config
    code, out = run(repo, config, args.mode, args.apply); print(json.dumps(out, sort_keys=True, separators=(",", ":"))); return code


if __name__ == "__main__": raise SystemExit(main())
