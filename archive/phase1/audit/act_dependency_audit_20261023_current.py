"""Static audit of every submitted Snake act implementation."""

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def audit(path):
    tree = ast.parse(path.read_text())
    act = next((node for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == "act"), None)
    if act is None:
        return {"has_act": False}
    names = sorted({node.id for node in ast.walk(act) if isinstance(node, ast.Name)})
    attrs = sorted({node.attr for node in ast.walk(act) if isinstance(node, ast.Attribute)})
    tokens = set(names) | set(attrs)
    return {
        "has_act": True,
        "reads_prediction_or_cells": bool(tokens & {"prediction", "cells", "support"}),
        "reads_action_state": bool(tokens & {"action_mass", "field_mass", "last_action", "last_target"}),
        "snake_geometry": sorted(tokens & {"body", "head", "side", "moves", "direction", "free", "flow"}),
        "apple_or_length": sorted(tokens & {"apple", "apples", "length", "snake_length"}),
        "literal_constants": sorted({repr(node.value) for node in ast.walk(act)
                                      if isinstance(node, ast.Constant)
                                      and isinstance(node.value, (int, float, str))}),
    }


def main():
    result = {}
    for path in sorted((ROOT / "candidates").glob("*/principle.py")):
        info = audit(path)
        if info.get("has_act"):
            result[path.parent.name] = info
    out = ROOT / "audit/act_dependency_audit_20261023_current_result.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
