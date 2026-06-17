#!/usr/bin/env python3
"""Run domain-specific mutation checks for RoboVac model mappings.

The script copies the source tree to a temporary directory, applies one mapping
mutation at a time, and runs the relevant tests against the mutated copy. It
does not modify the working tree.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = Path("custom_components/robovac/vacuums")
VACUUM_ENTITY = Path("custom_components/robovac/vacuum.py")
REPORT_DIR = Path("mutation-reports")

CRITICAL_COMMANDS = {"START_PAUSE", "RETURN_HOME", "MODE", "STATUS"}
GENERIC_MAPPING_TESTS = (
    "tests/test_vacuum/test_dps_command_mapping.py",
    "tests/test_vacuum/test_get_robovac_command_value.py",
    "tests/test_vacuum/test_get_robovac_human_readable_value.py",
    "tests/test_vacuum/test_legacy_start_pause_mappings.py",
)
ROOM_COMMAND_TESTS = (
    "tests/test_vacuum/test_vacuum_commands.py",
    "tests/test_vacuum/test_vacuum_entity.py",
)


@dataclass(frozen=True)
class Mutation:
    """A single mapping mutation to apply to a temporary source copy."""

    id: str
    path: str
    description: str
    kind: str
    model: str | None = None
    command: str | None = None
    detail: str | None = None
    occurrence: int | None = None
    target_lineno: int | None = None
    target_col_offset: int | None = None
    tests: tuple[str, ...] = field(default_factory=tuple)


@dataclass
class MutationResult:
    """Result for one mutation run."""

    id: str
    path: str
    description: str
    outcome: str
    tests: tuple[str, ...]
    duration_seconds: float
    returncode: int | None = None
    output_tail: str = ""


def _command_name(node: ast.AST | None) -> str | None:
    if (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "RobovacCommand"
    ):
        return node.attr
    return None


def _string_constant(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _find_dict_value(dictionary: ast.Dict, key: str) -> ast.AST | None:
    for dict_key, value in zip(dictionary.keys, dictionary.values, strict=True):
        if _string_constant(dict_key) == key:
            return value
    return None


def _has_dict_key(dictionary: ast.Dict, key: str) -> bool:
    return any(_string_constant(dict_key) == key for dict_key in dictionary.keys)


def _model_test_paths(model: str) -> tuple[str, ...]:
    model_test = f"tests/test_vacuum/test_{model.lower()}_command_mappings.py"
    tests = [*GENERIC_MAPPING_TESTS]
    if (ROOT / model_test).exists():
        tests.insert(0, model_test)
    return tuple(dict.fromkeys(tests))


def _build_model_mutations(path: Path, tree: ast.Module) -> list[Mutation]:
    mutations: list[Mutation] = []
    relative = path.relative_to(ROOT).as_posix()
    model = path.stem

    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name != model:
            continue

        for statement in node.body:
            if not isinstance(statement, ast.Assign):
                continue
            if not any(isinstance(target, ast.Name) and target.id == "commands" for target in statement.targets):
                continue
            if not isinstance(statement.value, ast.Dict):
                continue

            for key_node, value_node in zip(statement.value.keys, statement.value.values, strict=True):
                command = _command_name(key_node)
                if command is None:
                    continue

                if command in CRITICAL_COMMANDS:
                    mutations.append(
                        Mutation(
                            id=f"{model}:{command}:remove-command",
                            path=relative,
                            model=model,
                            command=command,
                            kind="remove_command",
                            description=f"Remove {command} command from {model}",
                            tests=_model_test_paths(model),
                        )
                    )

                if isinstance(value_node, ast.Dict):
                    code_value = _find_dict_value(value_node, "code")
                    if _is_mutable_code(code_value):
                        mutations.extend(
                            _code_mutations(
                                relative=relative,
                                model=model,
                                command=command,
                                tests=_model_test_paths(model),
                            )
                        )

                    if _has_dict_key(value_node, "values"):
                        mutations.append(
                            Mutation(
                                id=f"{model}:{command}:remove-values",
                                path=relative,
                                model=model,
                                command=command,
                                kind="remove_values",
                                description=f"Remove values mapping from {model} {command}",
                                tests=_model_test_paths(model),
                            )
                        )

                    if command == "START_PAUSE":
                        values = _find_dict_value(value_node, "values")
                        if isinstance(values, ast.Dict):
                            for detail in ("start", "pause"):
                                if _has_bool_value(values, detail):
                                    mutations.append(
                                        Mutation(
                                            id=f"{model}:START_PAUSE:flip-{detail}",
                                            path=relative,
                                            model=model,
                                            command=command,
                                            detail=detail,
                                            kind="flip_bool_value",
                                            description=f"Flip {detail} boolean for {model} START_PAUSE",
                                            tests=_model_test_paths(model),
                                        )
                                    )

                    if command == "STATUS":
                        values = _find_dict_value(value_node, "values")
                        if isinstance(values, ast.Dict) and _has_dict_key(values, "Recharge"):
                            mutations.append(
                                Mutation(
                                    id=f"{model}:STATUS:remove-Recharge",
                                    path=relative,
                                    model=model,
                                    command=command,
                                    detail="Recharge",
                                    kind="remove_nested_value",
                                    description=f"Remove Recharge status mapping from {model}",
                                    tests=_model_test_paths(model),
                                )
                            )
                elif _is_mutable_code(value_node):
                    mutations.extend(
                        _code_mutations(
                            relative=relative,
                            model=model,
                            command=command,
                            tests=_model_test_paths(model),
                        )
                    )

    return mutations


def _is_mutable_code(node: ast.AST | None) -> bool:
    if isinstance(node, ast.Constant) and isinstance(node.value, int | str):
        return isinstance(node.value, int) or node.value.isdigit()
    return False


def _code_mutations(
    *, relative: str, model: str, command: str, tests: tuple[str, ...]
) -> list[Mutation]:
    return [
        Mutation(
            id=f"{model}:{command}:code-plus-one",
            path=relative,
            model=model,
            command=command,
            detail="plus_one",
            kind="change_code",
            description=f"Increment DPS code for {model} {command}",
            tests=tests,
        ),
        Mutation(
            id=f"{model}:{command}:code-minus-one",
            path=relative,
            model=model,
            command=command,
            detail="minus_one",
            kind="change_code",
            description=f"Decrement DPS code for {model} {command}",
            tests=tests,
        ),
    ]


def _has_bool_value(dictionary: ast.Dict, key: str) -> bool:
    value = _find_dict_value(dictionary, key)
    return isinstance(value, ast.Constant) and isinstance(value.value, bool)


def _build_map_id_mutations(path: Path, tree: ast.Module) -> list[Mutation]:
    mutations: list[Mutation] = []
    relative = path.relative_to(ROOT).as_posix()

    class Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.occurrence = 0

        def visit_Constant(self, node: ast.Constant) -> None:
            if node.value == "mapId":
                mutations.append(
                    Mutation(
                        id=f"vacuum.py:mapId:{self.occurrence}",
                        path=relative,
                        occurrence=self.occurrence,
                        target_lineno=node.lineno,
                        target_col_offset=node.col_offset,
                        kind="change_map_id_literal",
                        description=(
                            f"Change mapId literal occurrence {self.occurrence} "
                            "in vacuum.py"
                        ),
                        tests=ROOM_COMMAND_TESTS,
                    )
                )
                self.occurrence += 1

    Visitor().visit(tree)
    return mutations


class MappingMutationTransformer(ast.NodeTransformer):
    """Apply one requested mutation to a parsed source file."""

    def __init__(self, mutation: Mutation) -> None:
        self.mutation = mutation
        self.applied = False

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        if (
            self.mutation.kind == "change_map_id_literal"
            and node.value == "mapId"
            and node.lineno == self.mutation.target_lineno
            and node.col_offset == self.mutation.target_col_offset
        ):
            self.applied = True
            return ast.copy_location(ast.Constant("__mutated_mapId__"), node)
        return node

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:
        if self.mutation.kind == "change_map_id_literal":
            return self.generic_visit(node)
        if self.mutation.model is None or node.name != self.mutation.model:
            return node
        return self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> ast.AST:
        if self.mutation.kind == "change_map_id_literal":
            return self.generic_visit(node)
        if self.mutation.model is None:
            return node
        if not any(isinstance(target, ast.Name) and target.id == "commands" for target in node.targets):
            return node
        if isinstance(node.value, ast.Dict):
            node.value = self._mutate_commands_dict(node.value)
        return node

    def _mutate_commands_dict(self, commands: ast.Dict) -> ast.Dict:
        new_keys: list[ast.expr | None] = []
        new_values: list[ast.expr] = []

        for key_node, value_node in zip(commands.keys, commands.values, strict=True):
            command = _command_name(key_node)
            if command != self.mutation.command:
                new_keys.append(key_node)
                new_values.append(value_node)
                continue

            if self.mutation.kind == "remove_command":
                self.applied = True
                continue

            new_keys.append(key_node)
            new_values.append(self._mutate_command_value(value_node))

        commands.keys = new_keys
        commands.values = new_values
        return commands

    def _mutate_command_value(self, value_node: ast.expr) -> ast.expr:
        if self.mutation.kind == "change_code" and _is_mutable_code(value_node):
            self.applied = True
            return self._change_code(value_node)

        if not isinstance(value_node, ast.Dict):
            return value_node

        if self.mutation.kind == "remove_values":
            return self._remove_top_level_key(value_node, "values")

        if self.mutation.kind == "change_code":
            return self._mutate_code_key(value_node)

        if self.mutation.kind == "flip_bool_value":
            return self._flip_bool_in_values(value_node)

        if self.mutation.kind == "remove_nested_value":
            return self._remove_nested_value(value_node)

        return value_node

    def _remove_top_level_key(self, dictionary: ast.Dict, key: str) -> ast.Dict:
        new_keys: list[ast.expr | None] = []
        new_values: list[ast.expr] = []
        for dict_key, value in zip(dictionary.keys, dictionary.values, strict=True):
            if _string_constant(dict_key) == key:
                self.applied = True
                continue
            new_keys.append(dict_key)
            new_values.append(value)
        dictionary.keys = new_keys
        dictionary.values = new_values
        return dictionary

    def _mutate_code_key(self, dictionary: ast.Dict) -> ast.Dict:
        for index, dict_key in enumerate(dictionary.keys):
            if _string_constant(dict_key) == "code":
                dictionary.values[index] = self._change_code(dictionary.values[index])
        return dictionary

    def _change_code(self, node: ast.expr) -> ast.expr:
        if not isinstance(node, ast.Constant):
            return node
        delta = 1 if self.mutation.detail == "plus_one" else -1
        if isinstance(node.value, int):
            self.applied = True
            return ast.copy_location(ast.Constant(node.value + delta), node)
        if isinstance(node.value, str) and node.value.isdigit():
            self.applied = True
            return ast.copy_location(ast.Constant(str(int(node.value) + delta)), node)
        return node

    def _flip_bool_in_values(self, dictionary: ast.Dict) -> ast.Dict:
        values = _find_dict_value(dictionary, "values")
        if not isinstance(values, ast.Dict):
            return dictionary
        for index, dict_key in enumerate(values.keys):
            if _string_constant(dict_key) != self.mutation.detail:
                continue
            current = values.values[index]
            if isinstance(current, ast.Constant) and isinstance(current.value, bool):
                values.values[index] = ast.copy_location(ast.Constant(not current.value), current)
                self.applied = True
        return dictionary

    def _remove_nested_value(self, dictionary: ast.Dict) -> ast.Dict:
        values = _find_dict_value(dictionary, "values")
        if not isinstance(values, ast.Dict) or self.mutation.detail is None:
            return dictionary

        new_keys: list[ast.expr | None] = []
        new_values: list[ast.expr] = []
        for dict_key, value in zip(values.keys, values.values, strict=True):
            if _string_constant(dict_key) == self.mutation.detail:
                self.applied = True
                continue
            new_keys.append(dict_key)
            new_values.append(value)
        values.keys = new_keys
        values.values = new_values
        return dictionary


def build_mutations() -> list[Mutation]:
    mutations: list[Mutation] = []
    for path in sorted((ROOT / MODEL_DIR).glob("T*.py")):
        tree = ast.parse(path.read_text(), filename=str(path))
        mutations.extend(_build_model_mutations(path, tree))

    vacuum_path = ROOT / VACUUM_ENTITY
    mutations.extend(_build_map_id_mutations(vacuum_path, ast.parse(vacuum_path.read_text())))
    return mutations


def apply_mutation(temp_root: Path, mutation: Mutation) -> None:
    path = temp_root / mutation.path
    tree = ast.parse(path.read_text(), filename=str(path))
    transformer = MappingMutationTransformer(mutation)
    mutated = transformer.visit(tree)
    ast.fix_missing_locations(mutated)
    if not transformer.applied:
        raise RuntimeError(f"Mutation was not applied: {mutation.id}")
    path.write_text(ast.unparse(mutated) + "\n")


def copy_project_subset(temp_root: Path) -> None:
    shutil.copytree(ROOT / "custom_components", temp_root / "custom_components")
    shutil.copytree(ROOT / "tests", temp_root / "tests")
    for filename in ("pytest.ini", "pyproject.toml"):
        shutil.copy2(ROOT / filename, temp_root / filename)


def run_pytest(temp_root: Path, tests: tuple[str, ...], timeout: float) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = f"{temp_root}{os.pathsep}{env.get('PYTHONPATH', '')}"
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", *tests],
        cwd=temp_root,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )


def output_tail(output: str, lines: int = 30) -> str:
    return "\n".join(output.splitlines()[-lines:])


def run_mutation(mutation: Mutation, timeout: float) -> MutationResult:
    start = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="robovac-mapping-mutant-") as temp_dir:
        temp_root = Path(temp_dir)
        copy_project_subset(temp_root)
        apply_mutation(temp_root, mutation)
        try:
            completed = run_pytest(temp_root, mutation.tests, timeout)
        except subprocess.TimeoutExpired as exc:
            return MutationResult(
                id=mutation.id,
                path=mutation.path,
                description=mutation.description,
                outcome="timeout",
                tests=mutation.tests,
                duration_seconds=round(time.monotonic() - start, 3),
                output_tail=output_tail(exc.output or ""),
            )

    return MutationResult(
        id=mutation.id,
        path=mutation.path,
        description=mutation.description,
        outcome="survived" if completed.returncode == 0 else "killed",
        tests=mutation.tests,
        duration_seconds=round(time.monotonic() - start, 3),
        returncode=completed.returncode,
        output_tail=output_tail(completed.stdout),
    )


def verify_baseline(timeout: float) -> None:
    tests = tuple(dict.fromkeys([*GENERIC_MAPPING_TESTS, *ROOM_COMMAND_TESTS]))
    with tempfile.TemporaryDirectory(prefix="robovac-mapping-baseline-") as temp_dir:
        temp_root = Path(temp_dir)
        copy_project_subset(temp_root)
        completed = run_pytest(temp_root, tests, timeout)
    if completed.returncode != 0:
        print("Baseline tests failed in temporary mutation workspace.", file=sys.stderr)
        print(output_tail(completed.stdout), file=sys.stderr)
        raise SystemExit(2)


def write_reports(report_dir: Path, mutations: list[Mutation], results: list[MutationResult]) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "total_mutations": len(mutations),
        "executed_mutations": len(results),
        "killed": sum(result.outcome == "killed" for result in results),
        "survived": sum(result.outcome == "survived" for result in results),
        "timeout": sum(result.outcome == "timeout" for result in results),
        "results": [asdict(result) for result in results],
    }
    (report_dir / "model-mapping-mutations.json").write_text(json.dumps(payload, indent=2) + "\n")

    survivors = [result for result in results if result.outcome == "survived"]
    lines = [
        "# RoboVac Mapping Mutation Report",
        "",
        f"- Total discovered mutations: {len(mutations)}",
        f"- Executed mutations: {len(results)}",
        f"- Killed: {payload['killed']}",
        f"- Survived: {payload['survived']}",
        f"- Timed out: {payload['timeout']}",
        "",
    ]
    if survivors:
        lines.extend(
            [
                "## Survivors",
                "",
                "| ID | Path | Description | Tests |",
                "| --- | --- | --- | --- |",
            ]
        )
        for survivor in survivors:
            tests = "<br>".join(survivor.tests)
            lines.append(
                f"| `{survivor.id}` | `{survivor.path}` | {survivor.description} | {tests} |"
            )
        lines.append("")
    else:
        lines.extend(["No surviving mapping mutants.", ""])

    (report_dir / "model-mapping-mutations.md").write_text("\n".join(lines))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-mutants",
        type=int,
        default=None,
        help="Limit execution to the first N discovered mutants for smoke testing.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=90.0,
        help="Per-mutant pytest timeout in seconds.",
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=REPORT_DIR,
        help="Directory for JSON and Markdown reports.",
    )
    parser.add_argument(
        "--fail-on-survivors",
        action="store_true",
        help="Exit non-zero when any executed mutation survives.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    mutations = build_mutations()
    selected = mutations[: args.max_mutants] if args.max_mutants is not None else mutations

    print(f"Discovered {len(mutations)} mapping mutations.")
    if args.max_mutants is not None:
        print(f"Executing first {len(selected)} mutations.")

    verify_baseline(args.timeout)

    results: list[MutationResult] = []
    for index, mutation in enumerate(selected, start=1):
        print(f"[{index}/{len(selected)}] {mutation.id}: {mutation.description}")
        result = run_mutation(mutation, args.timeout)
        print(f"  -> {result.outcome} in {result.duration_seconds:.3f}s")
        results.append(result)

    write_reports(args.report_dir, mutations, results)

    survivors = [result for result in results if result.outcome == "survived"]
    print(
        "Mapping mutation report written to "
        f"{args.report_dir / 'model-mapping-mutations.md'}"
    )
    print(f"Killed: {sum(result.outcome == 'killed' for result in results)}")
    print(f"Survived: {len(survivors)}")
    print(f"Timed out: {sum(result.outcome == 'timeout' for result in results)}")

    if args.fail_on_survivors and survivors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
