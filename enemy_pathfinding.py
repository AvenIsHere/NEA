from threading import Thread
from typing import Never

import pathfinding  # type: ignore[import-untyped]
import pygame
from pathfinding.core.diagonal_movement import DiagonalMovement # type: ignore[import-untyped]
from pathfinding.core.grid import Grid # type: ignore[import-untyped]
from pathfinding.finder.a_star import AStarFinder # type: ignore[import-untyped]

from game import GameState, Enemy


class PathfindingThread:
    thread: Thread
    enemy_pathfinding: Pathfinding

    clock: pygame.time.Clock
    tick: int

    def __init__(self, game_state: GameState, ground_map: list[list[int]]) -> None:
        self.enemy_pathfinding = Pathfinding(game_state, ground_map)
        self.thread = Thread(target=self.do_tick)
        self.clock = pygame.time.Clock()
        self.tick = 20
        self.thread.start()

    def do_tick(self) -> Never:
        while True:
            if self.tick == 20:
                self.tick = 0
                self.enemy_pathfinding.calculate_pathfinding()
            self.tick += 1
            self.clock.tick(60)

class Pathfinding:
    grid: pathfinding.core.grid.Grid
    finder: AStarFinder
    game_state: GameState
    ground_map: list[list[int]]

    enemies_to_move: list[tuple[Enemy, pygame.Vector2]]

    def __init__(self, game_state: GameState, ground_map: list[list[int]]) -> None:
        self.game_state = game_state
        self.ground_map = ground_map
        self.enemies_to_move = []
        self.grid = Grid(matrix=ground_map)
        self.finder = AStarFinder(diagonal_movement=DiagonalMovement.never)

    def pathfind_enemy(self, enemy: Enemy) -> None:
        enemy_x = int(enemy.position.x // 1)
        enemy_y = int(enemy.position.y // 1)
        player_x = int(self.game_state.player.position.x // 1)
        player_y = int(self.game_state.player.position.y // 1)

        if not (abs(player_x - enemy_x) <= 20 and abs(player_y - enemy_y) <= 20):
            enemy.current_speed.x = 0.0
            return None

        if not (0 <= enemy_x < self.grid.width and 0 <= enemy_y < self.grid.height):
            enemy.current_speed.x = 0.0
            return None

        if not (0 <= player_x < self.grid.width and 0 <= player_y < self.grid.height):
            enemy.current_speed.x = 0.0
            return None

        start_y = enemy_y
        while start_y < self.grid.height and not self.grid.walkable(enemy_x, start_y):
            start_y += 1
        if start_y >= self.grid.height or not self.grid.walkable(enemy_x, start_y):
            enemy.current_speed.x = 0.0
            return None

        end_y = player_y
        while end_y < self.grid.height and not self.grid.walkable(player_x, end_y):
            end_y += 1
        if end_y >= self.grid.height or not self.grid.walkable(player_x, end_y):
            enemy.current_speed.x = 0.0
            return None

        self.grid.cleanup()
        start = self.grid.node(enemy_x, start_y)
        end = self.grid.node(player_x, end_y)
        path, runs = self.finder.find_path(start, end, self.grid)

        enemy.current_speed.x = 0.0
        if len(path) > 1:
            next_node = path[1]
            if next_node.x > enemy_x:
                enemy.current_speed.x = 0.05
            elif next_node.x < enemy_x:
                enemy.current_speed.x = -0.05
        return None

    def calculate_pathfinding(self) -> None:
        self.enemies_to_move = []
        for enemy in self.game_state.enemies:
            self.pathfind_enemy(enemy)