"""Static dependency audit for newly submitted action candidates."""

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NAMES = (
    "resource_balance_flow_action",
    "resource_flow_contact_action",
    "resource_flow_contact_return",
    "resource_flow_reserve_action",
    "coactivity_single_support_source_mass_action",
)


def audit(path):
    tree = ast.parse(path.read_text())
    act = next((n for n in ast.walk(tree)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "act"), None)
    if act is None:
        return {"has_act": False}
    names = sorted({n.id for n in ast.walk(act) if isinstance(n, ast.Name)})
    attrs = sorted({n.attr for n in ast.walk(act) if isinstance(n, ast.Attribute)})
    constants = sorted(
        {repr(c.value) for c in ast.walk(act)
         if isinstance(c, ast.Constant) and isinstance(c.value, (int, float, str))}
    )
    return {
        "has_act": True,
        "names": names,
        "attrs": attrs,
        "literal_constants": constants,
        "reads_obs": "obs" in names,
        "reads_prediction": "prediction" in names or "prediction" in attrs,
        "reads_action_mass": "action_mass" in names or "action_mass" in attrs,
        "reads_last_action": "last_action" in names or "last_action" in attrs,
        "snake_geometry_tokens": sorted(set(names) & {"cells", "side", "body", "head", "moves", "direction", "flow"}),
        "apple_or_length_tokens": sorted(set(names) & {"apple", "apples", "length", "snake_length"}),
    }


def main():
    result = {name: audit(ROOT / "candidates" / name / "principle.py") for name in NAMES}
    out = ROOT / "audit" / "act_dependency_audit_20261023_result.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
