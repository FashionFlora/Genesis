"""Small source-level probes for the latest action candidates."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(name):
    path = ROOT / "candidates" / name / "principle.py"
    spec = spec_from_file_location(name, path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.System()


def snake(head=11, direction=1, body=(), apple=88):
    obs = [0] * 700
    obs[direction * 100 + head] = 1
    for cell in body:
        obs[400 + cell] = 1
    obs[500 + apple] = 1
    return obs


def probe_action_vector():
    system = load("action_vector_closure")
    obs = snake()
    actions = []
    for _ in range(8):
        system.step(obs)
        actions.append(system.act(obs))
    return actions


def probe_returned_edge():
    system = load("returned_flow_edge_action")
    obs_a = snake(apple=88)
    obs_b = snake(apple=89)
    system.step(obs_a)
    first = system.act(obs_a)
    system.step(obs_b)
    second = system.act(obs_b)
    return first, second, system.action_mass


if __name__ == "__main__":
    print("action_vector_same_state_actions", probe_action_vector())
    print("returned_edge_apple_change", probe_returned_edge())
