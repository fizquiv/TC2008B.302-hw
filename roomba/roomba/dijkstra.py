# importamos priority queue para implementar dijkstra
import heapq

# start - coordenadas de inicio, goal - coordenadas de nodo objetivo
# obstacles - set de coordenadas de obstáculos, width y height son ints para no salirnos del grid
def dijkstra(start, goal, obstacles, width, height):

    # condición de parada
    if start == goal:
        return [start]
    
    # priority queue
    pq = [(0, start)]
    
    # lista que guarda las distancias más cortas desde posición actual a cada nodo (coordenada)
    distances = {start: 0}
    
    # lista que guarda la úlitma coordenada antes de llegar a un nodo 
    previous = {}
    
    # guarda nodos visitados para no regresar
    visited = set()
    

    while pq:
        current_dist, current_pos = heapq.heappop(pq)
        
        # ignoramos si ya lo visitamos
        if current_pos in visited:
            continue
        
        visited.add(current_pos)
        
        # si llegamos a goal, custruimos el camino usando el hash map (previous) con los pasos
        if current_pos == goal:
            return reconstruct_path(previous, start, goal)
        
        # exploramos los vecinos
        x, y = current_pos
        neighbors = [
            (x + 1, y),
            (x - 1, y),
            (x, y + 1),
            (x, y - 1),
        ]
        
        for neighbor in neighbors:
            nx, ny = neighbor
            
            if not (0 <= nx < width and 0 <= ny < height):
                continue  # fuera del grid
            
            if neighbor in obstacles:
                continue  # el vecino está bloqueado
            
            if neighbor in visited:
                continue  # ya lo procesamos
            
            new_dist = current_dist + 1
            
            # si encontramos un camino más corto para llegar a un nodo, o si no habíamos guardado un camino para llegar a ese nodo, lo guardamos
            if neighbor not in distances or new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                previous[neighbor] = current_pos
                heapq.heappush(pq, (new_dist, neighbor))
    
    # no hubo camino para llegar al goal
    return None

# previous - hash map con los pasos para llegar, start y goal - coordenadas de inicio y fin
def reconstruct_path(previous, start, goal):
    path = []

    # la lista camino tiene los pasos de goal a start
    current = goal
    
    while current != start:
        path.append(current)
        current = previous[current]
    
    path.append(start)

    # invertimos la lista para tener el orden de start a goal
    path.reverse()
    
    return path

# esta función encuentra la celda sucia más cerca 
# start - coordenadas de nodo inicial, targets y obstacles - sets de coordenadas
def find_closest_target(start, targets, obstacles, width, height):

    if not targets:
        return None
    
    # variables para guardar camino más corto y su distancia 
    shortest_path = None
    closest_target = None

    shortest_distance = float('inf')
    
    # usamos dijsktra para encontrar el target más cercano
    for target in targets:
        path = dijkstra(start, target, obstacles, width, height)
        if path and len(path) < shortest_distance:
            shortest_distance = len(path)
            shortest_path = path
            closest_target = target
    
    if shortest_path:
        return (shortest_path, closest_target)
    
    return None


def get_path_length(start, goal, obstacles, width, height):
    path = dijkstra(start, goal, obstacles, width, height)
    if path:
        return len(path) - 1  # restamos 1 porque el camino incluye la posición inicial
    return float('inf') # regresamos infinito si no hay camino
