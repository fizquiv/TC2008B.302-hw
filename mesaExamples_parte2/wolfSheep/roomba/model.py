"""
Roomba Cleaning Robot Simulation
================================

A simulation of autonomous cleaning robots (Roombas) that navigate a room,
clean dirt, avoid obstacles, and manage their battery by returning to charging stations.
"""

import math

from mesa import Model
from mesa.datacollection import DataCollector
from mesa.discrete_space import OrthogonalVonNeumannGrid
from .agents import ChargingStation, DirtyCell, Obstacle, RoombaAgent
from mesa.experimental.devs import ABMSimulator


class RoombaCleaning(Model):
    """Roomba Cleaning Simulation Model.

    A model for simulating autonomous cleaning robots with subsumption architecture.
    """

    description = (
        "A model for simulating Roomba cleaning robots with battery management and obstacle avoidance."
    )

    def __init__(
        self,
        width=20,
        height=20,
        num_agents=1,
        dirt_percentage=30,
        obstacle_percentage=10,
        max_time=1000,
        simulation_type="Sim 1",
        seed=None,
        simulator: ABMSimulator = None,
    ):
        """Create a new Roomba Cleaning model with the given parameters.

        Args:
            width: Width of the grid
            height: Height of the grid
            num_agents: Number of Roomba agents
            dirt_percentage: Percentage of cells that are dirty (0-100)
            obstacle_percentage: Percentage of cells with obstacles (0-100)
            max_time: Maximum simulation steps
            simulation_type: "Sim 1" (single agent) or "Sim 2" (multi-agent)
            seed: Random seed
            simulator: ABMSimulator instance for event scheduling
        """
        super().__init__(seed=seed)
        self.simulator = simulator
        self.simulator.setup(self)

        # Initialize model parameters
        self.height = height
        self.width = width
        self.num_agents = num_agents
        self.dirt_percentage = dirt_percentage
        self.obstacle_percentage = obstacle_percentage
        self.max_time = max_time
        self.simulation_type = simulation_type
        self.cells_cleaned = 0
        self.initial_dirt_count = 0

        # Create grid using experimental cell space
        self.grid = OrthogonalVonNeumannGrid(
            [self.height, self.width],
            torus=False,
            capacity=math.inf,
            random=self.random,
        )

        # Set up data collection
        model_reporters = {
            "Roombas": lambda m: len(m.agents_by_type[RoombaAgent]),
            "Dirty Cells": lambda m: len(m.agents_by_type[DirtyCell]),
            "Average Battery": lambda m: sum(a.battery for a in m.agents_by_type[RoombaAgent]) / max(len(m.agents_by_type[RoombaAgent]), 1),
            "Total Movements": lambda m: sum(a.movements for a in m.agents_by_type[RoombaAgent]),
            "Cells Cleaned": lambda m: m.cells_cleaned,
        }

        self.datacollector = DataCollector(model_reporters)

        # Place obstacles first
        num_obstacles = int((width * height) * (obstacle_percentage / 100))
        available_cells = list(self.grid.all_cells.cells)
        
        # Reserve (0,0) for Sim 1
        if simulation_type == "Sim 1":
            reserved_cell = self.grid[(0, 0)]
            if reserved_cell in available_cells:
                available_cells.remove(reserved_cell)
        
        obstacle_cells = self.random.sample(available_cells, min(num_obstacles, len(available_cells)))
        for cell in obstacle_cells:
            Obstacle(self, cell)
            available_cells.remove(cell)

        # Create Roomba agents and charging stations based on simulation type
        if simulation_type == "Sim 1":
            # Single agent at (0,0) with charging station
            start_cell = self.grid[(0, 0)]
            ChargingStation(self, start_cell)
            RoombaAgent.create_agents(
                self,
                1,
                battery=100,
                cell=[start_cell],
                home_station=[(0, 0)],
            )
        else:  # Sim 2
            # Multi-agent at random positions
            agent_cells = self.random.sample(available_cells, min(num_agents, len(available_cells)))
            for cell in agent_cells:
                ChargingStation(self, cell)
                available_cells.remove(cell)
            
            home_stations = [cell.coordinate for cell in agent_cells]
            RoombaAgent.create_agents(
                self,
                num_agents,
                battery=100,
                cell=agent_cells,
                home_station=home_stations,
            )

        # Place dirt in remaining available cells
        num_dirt = int(len(available_cells) * (dirt_percentage / 100))
        dirt_cells = self.random.sample(available_cells, num_dirt)
        for cell in dirt_cells:
            DirtyCell(self, cell)
        
        self.initial_dirt_count = num_dirt

        # Collect initial data
        self.running = True
        self.datacollector.collect(self)

    def step(self):
        """Execute one step of the model."""
        # Activate all Roombas in random order
        self.agents_by_type[RoombaAgent].shuffle_do("step")

        # Collect data
        self.datacollector.collect(self)

        # Check if simulation should stop
        if self.simulator.time >= self.max_time:
            self.running = False
        
        # Check if all dirt is cleaned
        if len(self.agents_by_type[DirtyCell]) == 0:
            self.running = False

    @property
    def clean_percentage(self):
        """Calculate the percentage of cells cleaned."""
        if self.initial_dirt_count == 0:
            return 100.0
        return (self.cells_cleaned / self.initial_dirt_count) * 100
