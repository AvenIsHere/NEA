from threading import Thread
import pathfinding  # type: ignore[import-untyped]
import pygame
from pathfinding.core.diagonal_movement import DiagonalMovement # type: ignore[import-untyped]
from pathfinding.core.grid import Grid # type: ignore[import-untyped]
from pathfinding.finder.a_star import AStarFinder # type: ignore[import-untyped]

from game import GameState, Wizard, Knight, Soldier, Enemy, Player


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
        self.tick += 1
        self.clock.tick(60)

class Pathfinding:
    grid: pathfinding.core.grid.Grid
    finder: AStarFinder
    game_state: GameState
    ground_map: list[pygame.Vector2]

    enemies_to_move: list[tuple[Enemy, pygame.Vector2]]

    def __init__(self, game_state: GameState, ground_map: list[pygame.Vector2]) -> None:
        self.game_state = game_state
        self.ground_map = ground_map
        self.enemies_to_move = []
        self.grid = Grid(matrix=ground_map)
        self.finder = AStarFinder(diagonal_movement=DiagonalMovement.never)

    def pathfind_enemy(self, enemy: Enemy) -> None:
        if not (abs(self.game_state.player.position[0] - int(
                enemy.position[0] // 1)) <= 20 and abs(
            self.game_state.player.position[1] - int(enemy.position[1] // 1)) <= 20):
            return None
        start = self.grid.node(int(enemy.position[0] // 1),
                               int(enemy.position[1] // 1))
        end = self.grid.node(int(self.game_state.player.position[0]),
                             int(self.game_state.player.position[1]))
        path, runs = self.finder.find_path(start, end, self.grid)
        path_grid = self.grid.grid_str(path=path, start=start, end=end).split('\n')
        enemy.current_speed.x = 0.0
        if path_grid[enemy.position.y//1][enemy.position.x//1 + 1] == 'x':
            enemy.current_speed.x += 0.05
        if path_grid[enemy.position.y//1][enemy.position.x//1 - 1] == 'x':
            enemy.current_speed.x -= 0.05
        return None

    def calculate_pathfinding(self) -> None:
        self.enemies_to_move = []
        for enemy in self.game_state.enemies:
            self.pathfind_enemy(enemy)