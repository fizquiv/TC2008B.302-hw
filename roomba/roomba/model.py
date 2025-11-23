import math

from mesa import Model
from mesa.datacollection import DataCollector
from mesa.discrete_space import OrthogonalVonNeumannGrid
from .agents import ChargingStation, DirtyCell, Obstacle, RoombaAgent
from mesa.experimental.devs import ABMSimulator


class RoombaCleaning(Model):

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
            "Times Charged": lambda m: sum(a.times_charged for a in m.agents_by_type[RoombaAgent]),
        }

        self.datacollector = DataCollector(model_reporters)

        # número de obstáculos
        num_obstacles = int((width * height) * (obstacle_percentage / 100))
        available_cells = list(self.grid.all_cells.cells)
        
        obstacle_cells = self.random.sample(available_cells, min(num_obstacles, len(available_cells)))
        for cell in obstacle_cells:
            Obstacle(self, cell)
            available_cells.remove(cell)

        # Crear roombas y estaciones de cargas según Sim 1 o Sim 2
        if simulation_type == "Sim 1":
            # sim 1 para la simulación con 1 sólo agente que empieza en (0, 0)
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
            # muchos agentes en posiciones random
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

        # crear celdas sucias
        num_dirt = int(len(available_cells) * (dirt_percentage / 100))
        dirt_cells = self.random.sample(available_cells, num_dirt)
        for cell in dirt_cells:
            DirtyCell(self, cell)
        
        self.initial_dirt_count = num_dirt

        # Collect initial data
        self.running = True
        self.datacollector.collect(self)
        self.stats_printed = False

    def step(self):
        # activar roombas
        self.agents_by_type[RoombaAgent].shuffle_do("step")

        # coleccionar datos
        self.datacollector.collect(self)

        # checar si ya pasó tiempo máximo
        if self.simulator.time >= self.max_time:
            self.running = False
        
        # checar si todo está limpio
        if len(self.agents_by_type[DirtyCell]) == 0:
            self.running = False
        
        # imprimir estadísticas solo una vez al final
        if not self.running and not self.stats_printed:
            self.print_individual_stats()
            self.stats_printed = True
    
    def print_individual_stats(self):
        print("ESTADÍSTICAS FINALES DE LA SIMULACIÓN")

        # Métricas globales
        print("\n--- Métricas Globales ---")
        print(f"Tiempo total: {self.simulator.time} pasos")
        print(f"Roombas: {len(self.agents_by_type[RoombaAgent])}")
        print(f"Celdas sucias iniciales: {self.initial_dirt_count}")
        print(f"Celdas limpiadas: {self.cells_cleaned}")
        print(f"Celdas sucias restantes: {len(self.agents_by_type[DirtyCell])}")
        print(f"Porcentaje limpiado: {(self.cells_cleaned / self.initial_dirt_count * 100):.1f}%")
        
        roombas = self.agents_by_type[RoombaAgent]
        total_movements = sum(a.movements for a in roombas)
        total_charges = sum(a.times_charged for a in roombas)
        avg_battery = sum(a.battery for a in roombas) / max(len(roombas), 1)
        
        print(f"Total movimientos: {total_movements}")
        print(f"Total cargas: {total_charges}")
        print(f"Batería promedio final: {avg_battery:.1f}%")
        
        # Estadísticas individuales
        print("\n--- Estadísticas Individuales ---")
        for i, agent in enumerate(roombas):
            print(f"Agente {i}: Movimientos={agent.movements}, Cargas={agent.times_charged}, Celdas Limpiadas={agent.cells_cleaned}, Batería={agent.battery}%")
        
        print("="*60 + "\n")