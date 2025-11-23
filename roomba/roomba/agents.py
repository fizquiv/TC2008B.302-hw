from mesa.discrete_space import CellAgent, FixedAgent
from .dijkstra import dijkstra, find_closest_target, get_path_length


class RoombaAgent(CellAgent):    
    def __init__(
        self, model, battery=100, cell=None, home_station=None
    ):
        super().__init__(model)
        self.battery = battery
        self.cell = cell
        self.home_station = home_station
        self.movements = 0
        self.times_charged = 0
        self.cells_cleaned = 0
        

        self.current_path = []  #  camino para llegar a target
        self.target_dirty_cell = None  # siguiente celda sucia a limpiar
        self.returning_home = False  # var booleana para ver si ya es hora de regrear

    def step(self):
        # prioridad 1: cargar al máximo si está en estación de carga
        if self.is_on_charging_station() and self.battery < 100:
            self.charge()
            return
        
        # prioridad 2: limpiar celda si está sucia
        if self.is_on_dirty_cell():
            if self.battery > 0:
                self.clean()
                # quitar celda de los targets
                self.target_dirty_cell = None
            return
        
        # calcular distancia a estación de carga para ver si es hora de regresar
        distance_to_home = self.calculate_distance_to_home()
        
        # prioridad 3: checar si necesitamos regresar para no quedarnos sin batería
        # checamos que nos sobre 10 de batería extra por si pasamos por celdas sucias en el camino
        if self.battery - 10 <= distance_to_home:
            if self.battery > 0:
                self.return_to_charging_station()
            return
        
        # prioridad 4: ir a la celda sucia más cerca
        if self.battery > 0:
            self.navigate_to_dirty_cell()
    
    def calculate_distance_to_home(self):
        
        current_pos = self.cell.coordinate
        obstacles = self.get_obstacle_positions()
        
        distance = get_path_length(
            current_pos,
            self.home_station,
            obstacles,
            self.model.width,
            self.model.height
        )
        
        return distance
    
    def return_to_charging_station(self):
        current_pos = self.cell.coordinate
        
        # si no estamos regresando ya a estación de carga, calcular camino de regreso
        if not self.returning_home:
            obstacles = self.get_obstacle_positions()
            path = dijkstra(
                current_pos,
                self.home_station,
                obstacles,
                self.model.width,
                self.model.height
            )
            
            if path and len(path) > 1:
                self.current_path = path[1:]  # quitamos la posición en la que ya estamos
                self.returning_home = True
        
        # seguimos el camino a la estación de carga
        if self.current_path:
            next_pos = self.current_path[0]
            next_cell = self.model.grid[next_pos]
            
            self.cell = next_cell
            self.battery -= 1
            self.movements += 1
            self.current_path.pop(0)
    
    def navigate_to_dirty_cell(self):
        current_pos = self.cell.coordinate
        
        dirty_positions = [
            agent.cell.coordinate 
            for agent in self.model.agents_by_type[DirtyCell]
        ]
        
        if not dirty_positions:
            return
        
        # si no estamos siguiendo un path, o no tenemos target dirty cell, encontramos siguiente target 
        if not self.current_path or self.target_dirty_cell not in dirty_positions:
            obstacles = self.get_obstacle_positions()
            result = find_closest_target(
                current_pos,
                dirty_positions,
                obstacles,
                self.model.width,
                self.model.height
            )
            
            if result:
                path, target = result
                if len(path) > 1:
                    self.current_path = path[1:]  # quitamos posición actual
                    self.target_dirty_cell = target
                    self.returning_home = False
        
        # seguimos camino
        if self.current_path:
            next_pos = self.current_path[0]
            next_cell = self.model.grid[next_pos]
            
            if next_cell:
                self.cell = next_cell
                self.battery -= 1
                self.movements += 1
                self.current_path.pop(0)
    
    def get_obstacle_positions(self):
        obstacles = set()
        for agent in self.model.agents_by_type[Obstacle]:
            obstacles.add(agent.cell.coordinate)
        return obstacles

    def is_on_charging_station(self):
        return any(isinstance(obj, ChargingStation) for obj in self.cell.agents)

    def is_on_dirty_cell(self):
        return any(isinstance(obj, DirtyCell) for obj in self.cell.agents)

    def charge(self):
        self.battery = min(100, self.battery + 5)
        self.times_charged += 1

    def clean(self):
        dirt = [obj for obj in self.cell.agents if isinstance(obj, DirtyCell)]
        if dirt:
            dirt[0].remove()
            self.battery -= 1
            self.model.cells_cleaned += 1
            self.cells_cleaned += 1


class DirtyCell(FixedAgent):
    def __init__(self, model, cell):
        super().__init__(model)
        self.cell = cell


class Obstacle(FixedAgent):
    def __init__(self, model, cell):
        super().__init__(model)
        self.cell = cell


class ChargingStation(FixedAgent):
  def __init__(self, model, cell):
        super().__init__(model)
        self.cell = cell
