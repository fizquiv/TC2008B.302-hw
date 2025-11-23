from roomba.agents import ChargingStation, DirtyCell, Obstacle, RoombaAgent
from roomba.model import RoombaCleaning

from mesa.experimental.devs import ABMSimulator

from mesa.visualization import (
    CommandConsole,
    Slider,
    SolaraViz,
    SpaceRenderer,
    make_plot_component,
)
from mesa.visualization.components import AgentPortrayalStyle


def roomba_portrayal(agent):
    if agent is None:
        return

    portrayal = AgentPortrayalStyle(
        size=50,
        marker="o",
        zorder=2,
    )

    if isinstance(agent, RoombaAgent):
        # Color based on battery level
        if agent.battery > 60:
            portrayal.update(("color", "green"))
        elif agent.battery > 20:
            portrayal.update(("color", "yellow"))
        else:
            portrayal.update(("color", "red"))
        portrayal.update(("marker", "o"), ("size", 80), ("zorder", 4))
    elif isinstance(agent, DirtyCell):
        portrayal.update(("color", "brown"))
        portrayal.update(("marker", "s"), ("size", 100), ("zorder", 1))
    elif isinstance(agent, Obstacle):
        portrayal.update(("color", "black"))
        portrayal.update(("marker", "s"), ("size", 125), ("zorder", 2))
    elif isinstance(agent, ChargingStation):
        portrayal.update(("color", "blue"))
        portrayal.update(("marker", "^"), ("size", 100), ("zorder", 3))

    return portrayal


model_params = {
    "seed": {
        "type": "InputText",
        "value": 42,
        "label": "Random Seed",
    },
    "width": Slider("Grid Width", 20, 10, 50, 5),
    "height": Slider("Grid Height", 20, 10, 50, 5),
    "simulation_type": {
        "type": "Select",
        "value": "Sim 1",
        "values": ["Sim 1", "Sim 2"],
        "label": "Simulation Type",
    },
    "num_agents": Slider("Number of Agents", 1, 1, 10, 1),
    "dirt_percentage": Slider("Dirt Percentage", 30, 0, 80, 5),
    "obstacle_percentage": Slider("Obstacle Percentage", 10, 0, 30, 5),
    "max_time": Slider("Max Time Steps", 1000, 100, 5000, 100),
}


def post_process_space(ax):
    ax.set_aspect("equal")
    ax.set_title("Roomba Cleaning Simulation")


def post_process_lines(ax):
    ax.legend(loc="center left", bbox_to_anchor=(1, 0.9))


lineplot_component = make_plot_component(
    {
        "Dirty Cells": "tab:brown",
        "Average Battery": "tab:green",
        "Roombas": "tab:blue",
    },
    post_process=post_process_lines,
)

simulator = ABMSimulator()
model = RoombaCleaning(simulator=simulator)

renderer = SpaceRenderer(
    model,
    backend="matplotlib",
)
renderer.draw_agents(roomba_portrayal)
renderer.post_process = post_process_space

page = SolaraViz(
    model,
    renderer,
    components=[lineplot_component, CommandConsole],
    model_params=model_params,
    name="Roomba Cleaning Simulation",
    simulator=simulator,
)
page  # noqa
