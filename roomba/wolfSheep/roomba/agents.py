from mesa.discrete_space import CellAgent, FixedAgent


class RoombaAgent(CellAgent):
    """A cleaning robot that moves around, cleans dirt, and needs to recharge."""

    def __init__(
        self, model, battery=100, cell=None, home_station=None
    ):
        """Initialize a Roomba agent.

        Args:
            model: Model instance
            battery: Starting battery level (0-100)
            cell: Cell in which the Roomba starts
            home_station: The charging station this Roomba knows about
        """
        super().__init__(model)
        self.battery = battery
        self.cell = cell
        self.home_station = home_station
        self.movements = 0

    def step(self):
        """Execute one step of the Roomba's behavior using subsumption architecture."""
        # Priority 1: If on station and battery < 100, stay and charge
        if self.is_on_charging_station() and self.battery < 100:
            self.charge()
            return
        
        # Priority 2: If on dirty cell, clean it
        if self.is_on_dirty_cell():
            if self.battery > 0:
                self.clean()
            return
        
        # Priority 3: If battery low, return to charger
        if self.battery < 20:
            if self.battery > 0:
                self.move_toward_charger()
            return
        
        # Priority 4: Explore (move randomly)
        if self.battery > 0:
            self.explore()

    def is_on_charging_station(self):
        """Check if Roomba is currently on a charging station."""
        return any(isinstance(obj, ChargingStation) for obj in self.cell.agents)

    def is_on_dirty_cell(self):
        """Check if Roomba is on a cell with dirt."""
        return any(isinstance(obj, DirtyCell) for obj in self.cell.agents)

    def charge(self):
        """Charge battery while on charging station."""
        self.battery = min(100, self.battery + 5)

    def clean(self):
        """Clean dirt at current location."""
        dirt = [obj for obj in self.cell.agents if isinstance(obj, DirtyCell)]
        if dirt:
            dirt[0].remove()
            self.battery -= 1
            self.model.cells_cleaned += 1

    def move_toward_charger(self):
        """Move toward the home charging station."""
        if self.home_station is None:
            # If no known station, explore randomly
            self.explore()
            return
        
        # Get available neighboring cells (not blocked by obstacles)
        available_cells = self.cell.neighborhood.select(
            lambda cell: not any(isinstance(obj, Obstacle) for obj in cell.agents)
        )
        
        if len(available_cells) == 0:
            return  # Stuck, can't move
        
        # Find the cell that gets us closest to the home station
        station_pos = self.home_station
        best_cell = None
        best_distance = float('inf')
        
        for neighbor in available_cells:
            # Calculate Manhattan distance to station
            distance = abs(neighbor.coordinate[0] - station_pos[0]) + \
                      abs(neighbor.coordinate[1] - station_pos[1])
            if distance < best_distance:
                best_distance = distance
                best_cell = neighbor
        
        if best_cell:
            self.cell = best_cell
            self.battery -= 1
            self.movements += 1

    def explore(self):
        """Move randomly to a safe adjacent cell."""
        # Get cells without obstacles
        available_cells = self.cell.neighborhood.select(
            lambda cell: not any(isinstance(obj, Obstacle) for obj in cell.agents)
        )
        
        if len(available_cells) == 0:
            return  # Stuck, can't move
        
        # Move to random available cell
        self.cell = available_cells.select_random_cell()
        self.battery -= 1
        self.movements += 1


class DirtyCell(FixedAgent):
    """A dirty cell that can be cleaned by a Roomba."""

    def __init__(self, model, cell):
        """Create a new dirty cell.

        Args:
            model: Model instance
            cell: Cell to which this dirt belongs
        """
        super().__init__(model)
        self.cell = cell


class Obstacle(FixedAgent):
    """An obstacle that blocks movement."""

    def __init__(self, model, cell):
        """Create a new obstacle.

        Args:
            model: Model instance
            cell: Cell to which this obstacle belongs
        """
        super().__init__(model)
        self.cell = cell


class ChargingStation(FixedAgent):
    """A charging station where Roombas can recharge."""

    def __init__(self, model, cell):
        """Create a new charging station.

        Args:
            model: Model instance
            cell: Cell to which this station belongs
        """
        super().__init__(model)
        self.cell = cell
