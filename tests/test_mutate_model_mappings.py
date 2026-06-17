"""Tests for the RoboVac model mapping mutation audit script."""

import ast
import shutil
from pathlib import Path

from scripts import mutate_model_mappings


def _map_id_locations(tree: ast.AST) -> list[tuple[int, int]]:
    """Return mapId string literal locations in NodeVisitor traversal order."""
    locations: list[tuple[int, int]] = []

    class Visitor(ast.NodeVisitor):
        def visit_Constant(self, node: ast.Constant) -> None:
            if node.value == "mapId":
                locations.append((node.lineno, node.col_offset))

    Visitor().visit(tree)
    return locations


def test_map_id_mutations_apply_to_matching_literal_occurrences(tmp_path: Path) -> None:
    """Map ID mutations should apply and target the same traversal order used to discover them."""
    source_file = mutate_model_mappings.ROOT / mutate_model_mappings.VACUUM_ENTITY
    expected_locations = _map_id_locations(ast.parse(source_file.read_text()))
    mutations = [
        mutation
        for mutation in mutate_model_mappings.build_mutations()
        if mutation.kind == "change_map_id_literal"
    ]

    assert len(mutations) == len(expected_locations)

    for mutation, expected_location in zip(mutations, expected_locations, strict=True):
        temp_root = tmp_path / mutation.id.replace(":", "-")
        target_file = temp_root / mutation.path
        target_file.parent.mkdir(parents=True)
        shutil.copy2(source_file, target_file)

        tree = ast.parse(target_file.read_text())
        transformer = mutate_model_mappings.MappingMutationTransformer(mutation)
        mutated_tree = transformer.visit(tree)
        mutated_sentinel_locations = [
            (node.lineno, node.col_offset)
            for node in ast.walk(mutated_tree)
            if isinstance(node, ast.Constant) and node.value == "__mutated_mapId__"
        ]

        assert mutated_sentinel_locations == [expected_location]
        assert transformer.applied

        mutate_model_mappings.apply_mutation(temp_root, mutation)
