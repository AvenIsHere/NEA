from threading import Thread
import pathfinding  # type: ignore[import-untyped]
import pygame
from pathfinding.core.diagonal_movement import DiagonalMovement # type: ignore[import-untyped]
from pathfinding.core.grid import Grid # type: ignore[import-untyped]
from pathfinding.finder.a_star import AStarFinder # type: ignore[import-untyped]

from game import GameState, Wizard, Knight, Soldier, Enemy


class PathfindingThread:
    thread: Thread
    enemy_pathfinding: Pathfinding

    clock: pygame.time.Clock
    tick: int

    def __init__(self, game_state: GameState, ground_map: list[pygame.Vector2]) -> None:
        self.enemy_pathfinding = Pathfinding(game_state, ground_map)
        self.thread = Thread(target=self.do_tick)
        self.clock = pygame.time.Clock()
        self.tick = 20
        self.thread.start()

    def do_tick(self) -> None:
        if self.tick == 20:
            self.tick = 0
            self.enemy_pathfinding.calculate_pathfinding()
        else:
            self.enemy_pathfinding.move_enemies()
            self.tick += 1
        self.clock.tick(60)

class Pathfinding:
    grid: pathfinding.core.grid.Grid
    game_state: GameState
    ground_map: list[pygame.Vector2]

    enemies_to_move: list[tuple[Enemy, pygame.Vector2]]

    def __init__(self, game_state: GameState, ground_map: list[pygame.Vector2]) -> None:
        self.game_state = game_state
        self.ground_map = ground_map
        self.enemies_to_move = []
        self.grid = Grid(matrix=ground_map)

    def calculate_pathfinding(self) -> None:
        self.enemies_to_move = []
        for x, enemy in enumerate(self.game_state.enemies):
            if not (abs(self.game_state.player.position[0] - int(
                    enemy.position[0] // 1)) <= 21 and abs(
                self.game_state.player.position[1] - int(enemy.position[1] // 1)) <= 21):
                continue
            start = self.grid.node(int(enemy.position[0] // 1),
                              int(enemy.position[1] // 1))
            end = self.grid.node(int(self.game_state.player.position[0]),
                            int(self.game_state.player.position[1]))
            finder = AStarFinder(diagonal_movement=DiagonalMovement.never)
            path, runs = finder.find_path(start, end, self.grid)
            pathGrid = self.grid.grid_str(path=path, start=start, end=end).split('\n')
            if isinstance(enemy, Wizard) or isinstance(enemy, Soldier):
                for l in range(len(pathGrid)):
                    if 'se' in pathGrid[l] and not '#se' in pathGrid[l]:
                        n = int(self.game_state.player.position[0] // 1) - 2
                        self.enemies_to_move.append((enemy, pygame.Vector2(n, l)))
                    elif 'es' in pathGrid[l] and not 'es#' in pathGrid[l]:
                        n = int(self.game_state.player.position[0] // 1) + 2
                        self.enemies_to_move.append((enemy, pygame.Vector2(n, l)))
                    elif 'sxxe' in pathGrid[l] or 'exxs' in pathGrid[l]:
                        pass
                    elif 'x' in pathGrid[l]:
                        sLocation, eLocation = None, None
                        for z in range(len(pathGrid[l])):
                            if pathGrid[l][z] == 's':
                                sLocation = z
                        for z in range(len(pathGrid[l])):
                            if pathGrid[l][z] == 'e':
                                eLocation = z
                        if sLocation is None or eLocation is None: continue
                        if sLocation < eLocation:
                            n = int(self.game_state.player.position[0] // 1) - 1
                        else:
                            n = int(self.game_state.player.position[0] // 1) + 1
                        self.enemies_to_move.append((enemy, pygame.Vector2(n, l)))
            elif isinstance(enemy, Knight):
                for l in range(len(pathGrid)):
                    if 'x' in pathGrid[l] or 'se' in pathGrid[l] or 'es' in pathGrid[l]:
                        n = None
                        for i in reversed(range(len(pathGrid[l]))):
                            if pathGrid[l][i] == 'x' or (pathGrid[l][i] == 'e' and (
                                    pathGrid[l][i - 1] == 's' or pathGrid[l][i + 1] == 's')):
                                n = int(self.game_state.player.position[0])
                        if n is None: continue
                        self.enemies_to_move.append((enemy, pygame.Vector2(n, l)))

    def move_enemies(self) -> None:
        for enemy in self.enemies_to_move:
            if enemy[0].position != enemy[1]:
                if enemy[0].position.x // 1 > enemy[1].x // 1:
                    enemy[0].position.x -= 0.05
                if enemy[0].position.x // 1 < enemy[1].x // 1:
                    enemy[0].position.x += 0.05