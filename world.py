import dataclasses
import math
import random

import pygame

from consts import WALL_COLOR, FLOOR_COLOR

@dataclasses.dataclass
class WorldGridPoint:
    colour: pygame.Color
    collision: bool

class World:
    grid: list[list[WorldGridPoint]]

    def __init__(self, grid: list[list[WorldGridPoint]]):
        self.grid = grid

    def colliding(self, start_pos: pygame.Vector2, end_pos: pygame.Vector2) -> bool:

        min_x = int(math.floor(start_pos.x))
        max_x = int(math.floor(end_pos.x))
        min_y = int(math.floor(start_pos.y))
        max_y = int(math.floor(end_pos.y))

        width = len(self.grid)
        height = len(self.grid[0]) if width > 0 else 0

        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                if x < 0 or x >= width or y < 0 or y >= height:
                    return True
                if self.grid[x][y].collision:
                    return True

        return False

    def get_ground_tiles(self) -> list[pygame.Vector2]:
        ground_tiles: list[pygame.Vector2] = []
        width = len(self.grid)
        height = len(self.grid[0]) if width > 0 else 0
        for x in range(width):
            for y in range(height):
                if self.grid[x][y].collision: continue
                if y < height - 1 and self.grid[x][y + 1].collision:
                    ground_tiles.append(pygame.Vector2(x, y))
        return ground_tiles

    def get_ground_map(self, ground_tiles: list[pygame.Vector2]) -> list[list[int]]:
        ground_set = {(int(tile.x), int(tile.y)) for tile in ground_tiles}
        width = len(self.grid)
        height = len(self.grid[0]) if width > 0 else 0
        ground_map: list[list[int]] = []
        for y in range(height):
            row = []
            for x in range(width):
                row.append(1 if (x, y) in ground_set else 0)
            ground_map.append(row)
        return ground_map

    @staticmethod
    def generate(presets: list[list[str]], num_presets: pygame.Vector2) -> World:
        preset_len_y = len(presets[0])
        preset_len_x = len(presets[0][0])

        chosen_presets = [[random.choice(presets) for _ in range(int(num_presets.x))] for _ in range(int(num_presets.y))]

        world_map: list[list[WorldGridPoint]] = []

        point_map = {
            "-": (pygame.Color(WALL_COLOR), True),
            " ": (pygame.Color(FLOOR_COLOR), False)
        }

        for x in range(preset_len_x * int(num_presets.x)):
            world_map.append([])
            for y in range(preset_len_y * int(num_presets.y)):
                point_info = point_map[
                        chosen_presets[y // preset_len_y][x // preset_len_x][y % preset_len_y][x % preset_len_x]
                ]
                world_map[x].append(
                    WorldGridPoint(point_info[0], point_info[1])
                )

        world = World(world_map)

        return world
