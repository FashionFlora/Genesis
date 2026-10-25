"""A viability-gated correlation law with a fixed local synaptic budget.

The only teaching signal is endogenous: a signed change in sensed energy
qualifies a delayed sensor/action correlation.  Each sensor keeps its initial
outgoing norm, so learning redistributes finite capacity instead of growing a
weight without bound.
"""

import torch


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0):
        self.torch = torch
        self.width = int(n_sensors)
        self.motors = int(n_motors)
        generator = torch.Generator(device=device).manual_seed(int(seed))
        self.weights = torch.randn(batch, self.width, self.motors, device=device,
                                   generator=generator) * (self.width ** -0.5)
        self.capacity = self.weights.norm(dim=2, keepdim=True).clamp_min(1e-8)
        self.trace = torch.zeros_like(self.weights)
        self.previous_sensor = torch.zeros(batch, self.width, device=device)
        self.previous_action = torch.zeros(batch, self.motors, device=device)
        self.previous_energy = torch.zeros(batch, device=device)
        self.has_previous = torch.zeros(batch, device=device)

    def act(self, sensors):
        torch = self.torch
        energy = sensors[:, -1].clamp(0, 1)
        # Eligibility is local and delayed by one action.  Energy change is
        # the organism's endogenous qualification signal, not world reward.
        eligibility = self.previous_sensor[:, :, None] * self.previous_action[:, None, :]
        self.trace.mul_(0.985).add_(eligibility, alpha=0.015)
        viability = (energy - self.previous_energy).clamp(-0.2, 0.2)
        update = 0.08 * viability[:, None, None] * self.trace
        self.weights.add_(update * self.has_previous[:, None, None])

        # Axiom: every sensor has a conserved outgoing synaptic capacity.
        norm = self.weights.norm(dim=2, keepdim=True).clamp_min(1e-8)
        self.weights.mul_(self.capacity / norm)
        action = torch.tanh(torch.einsum("bs,bsm->bm", sensors, self.weights))
        self.previous_sensor.copy_(sensors)
        self.previous_action.copy_(action.detach())
        self.previous_energy.copy_(energy)
        self.has_previous.fill_(1)
        return action

    def structure(self):
        return {"units": min(self.width * self.motors, 100000),
                "connections": self.width * self.motors}
