"""Placeholder module used only to identify organism-v6 baseline calibration."""

import torch


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0):
        self.batch = batch
        self.n_motors = n_motors
        self.device = device

    def act(self, sensors):
        return torch.zeros(self.batch, self.n_motors, device=self.device)
