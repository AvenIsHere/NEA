import dataclasses
import random
from abc import ABC
from enum import Enum
from typing import ClassVar

import pygame

from consts import tileWidth, tileHeight, screen_height, screen_width, font2, WALL_COLOR, FLOOR_COLOR, GRID_COLOR, \
    FLOOR_NEXT_COL, PresetMaps


class Difficulty(Enum):
    Easy = 1
    Normal = 2
    Difficult = 3
    Very_Difficult = 4

@dataclasses.dataclass
class GameState:
    difficulty: Difficulty
    player: Player
    enemies: list[Enemy]
    bullets_fired: list[Bullet]
    wand_magic_fired: list[WandMagicThing]
    spawned_items: list[Item]
    tile_map: list[list[tuple[int, int, int]]]

    @classmethod
    def new_game(cls, difficulty: Difficulty) -> GameState:
        player = Player(100, pygame.Vector2(90, -10), [None, None])
        world_map = generate_map(PresetMaps, 5, 5)

        ground_tiles = get_ground_tiles(world_map)

        enemies = spawn_enemies(40, ground_tiles)

        items: list[Item] = []
        for x in range(20):
            items.append(spawn_item(Powerup, ground_tiles))
            items.append(spawn_item(Weapon, ground_tiles))

        return GameState(difficulty, player, enemies, [], [], items, world_map)

def generate_map(preset_maps: list[list[str]], num_presets_x: int, num_presets_y: int) -> list[list[tuple[int, int, int]]]:
    preset_len_x = len(preset_maps[0])
    preset_len_y = len(preset_maps[0][0])

    chosen_presets = [[random.choice(preset_maps) for _ in range(num_presets_x)] for _ in range(num_presets_y)]

    world_map: list[list[tuple[int, int, int]]] = []

    colour_map = {
        "-": WALL_COLOR,
        " ": FLOOR_COLOR
    }

    for y in range(preset_len_y * num_presets_y):
        world_map.append([])
        for x in range(preset_len_x * num_presets_x):
            world_map[y].append(
                colour_map[chosen_presets[y // preset_len_y][x // preset_len_x][x % preset_len_x][y % preset_len_y]]
            )

    return world_map

def get_ground_tiles(tile_map: list[list[tuple[int, int, int]]]) -> list[pygame.Vector2]:
    not_ground_colours = (GRID_COLOR, WALL_COLOR, FLOOR_NEXT_COL)
    ground_tiles: list[pygame.Vector2] = []
    for x in range(len(tile_map)):
        for y in range(len(tile_map[0])):
            if tile_map[x][y] in not_ground_colours: continue
            if y != len(tile_map[0]) - 1 and tile_map[x][y + 1] == FLOOR_COLOR: continue
            ground_tiles.append(pygame.Vector2(x, y))
    return ground_tiles

def get_ground_map(tile_map: list[list[tuple[int, int, int]]], ground_tiles: list[pygame.Vector2]) -> list[list[int]]:
    ground_map: list[list[int]] = []
    for x in range(len(tile_map)):
        ground_map.append([])
        for y in range(len(tile_map[0])):
            if pygame.Vector2(x, y) in ground_tiles:
                ground_map[x].append(1)
            else:
                ground_map[x].append(0)
    return ground_map


class Entity(ABC):
    health: float
    position: pygame.Vector2
    rect: pygame.Rect

    def __init__(self, health: float, position: pygame.Vector2, rect: pygame.Rect):
        self.health = health
        self.position = position
        self.rect = rect


class Item(Entity, ABC):
    name: ClassVar[str]
    colour: ClassVar[tuple[int, int, int]]

    def __init__(self, location: pygame.Vector2):
        super().__init__(1.0, location, pygame.Rect(((tileWidth) * (location[0])),
                                   ((tileHeight) * (location[1])) + tileHeight - (screen_height/30) + 1, (screen_width/30), (screen_height/30)))


class Bullet(Entity):
    direction: float
    damage: float
    shot_by: Entity

    def __init__(self, position: pygame.Vector2, direction: float, damage: float, shot_by: Entity):
        super().__init__(0.1, position, pygame.Rect(0, 0, 10, 10))
        self.direction = direction
        self.damage = damage
        self.shot_by = shot_by


@dataclasses.dataclass
class WandMagicThing(Entity):
    age: int
    target: Entity
    damage: float

    def __init__(self, position: pygame.Vector2, age: int, target: Entity, damage: float):
        super().__init__(0.1, position, pygame.Rect(((tileWidth) * (position[0])), ((tileHeight) * (position[1])),
                                                    target.rect.width / 4, target.rect.width / 4))
        self.age = age
        self.target = target
        self.damage = damage


class Weapon(Item, ABC):
    strength: float
    time_since_attack: int = 0
    cooldown: int = 10

    def __init__(self, location: pygame.Vector2, strength: float = 1.0):
        super().__init__(location)
        self.strength = strength


class Sword(Weapon):
    name = "Sword"
    colour = (200, 200, 0)

    def attack(self, target: Entity, attack_multiplier: float = 1) -> None:
        if self.time_since_attack <= self.cooldown:
            return

        target.health -= self.strength * attack_multiplier
        self.cooldown = random.randint(25, 40)

        self.time_since_attack = 0


class Gun(Weapon):
    name = "Gun"
    colour = (0, 200, 0)

    def shoot(self, given_state: GameState, shot_by: Entity, location: pygame.Vector2, direction: float,
              attack_multiplier: float = 1) -> None:
        if self.time_since_attack <= self.cooldown:
            return

        given_state.bullets_fired.append(Bullet(location, direction, self.strength * attack_multiplier, shot_by))
        self.cooldown = random.randint(10, 15)

        self.time_since_attack = 0


class Wand(Weapon):
    name = "Wand"
    colour = (100, 255, 255)

    def fire(self, given_state: GameState, target: Entity, location: pygame.Vector2, attack_multiplier: float = 1) -> None:
        if self.time_since_attack <= self.cooldown:
            return

        given_state.wand_magic_fired.append(WandMagicThing(location, 0, target, self.strength * attack_multiplier))
        self.cooldown = random.randint(100, 150)

        self.time_since_attack = 0


weapon_types: list[type[Weapon]] = [Sword, Gun, Wand]

def new_weapon(location: pygame.Vector2, weapon_type: type[Weapon] | None = None) -> Weapon:
    if weapon_type is None: weapon_type = random.choice(weapon_types)
    return weapon_type(location)


class Enemy(Entity, ABC):
    name: str
    initial: str
    colour: tuple[int, int, int]
    weapon: Weapon
    weapon_type: ClassVar[type[Weapon]]

    def __init__(self, health: int, location: pygame.Vector2):
        super().__init__(health, location, pygame.Rect((tileWidth * (location[0])),
                                                       (tileHeight * (location[1])) + tileHeight - (
                                                               screen_height / 30) + 1,
                                                       screen_width / 30, screen_height / 30))
        self.weapon = new_weapon(location, self.weapon_type)

    def render(self, game_state: GameState, screen: pygame.Surface) -> None:
        self.rect = pygame.Rect(
            (tileWidth * (self.position[0])) + game_state.player.position[0],
            (tileHeight * (self.position[1])) + game_state.player.position[1] + tileHeight - (
                    screen_height / 30) + 1,
            screen_width / 30, screen_height / 30)
        pygame.draw.rect(screen, self.colour, self.rect)
        if abs(self.rect.x - game_state.player.rect.x) < 100 and abs(
                self.rect.y - game_state.player.rect.y) < 100:
            enemyHealthText = font2.render(str(self.health), True, (30, 30, 30))
            enemyHealthTextRect = enemyHealthText.get_rect(
                center=(self.rect.center[0], self.rect.center[1] - 20))
            screen.blit(enemyHealthText, enemyHealthTextRect)
        enemyNameText = font2.render(self.initial, True, (30, 30, 30))
        enemyNameTextRect = enemyNameText.get_rect(
            center=(self.rect.center[0], self.rect.center[1]))
        screen.blit(enemyNameText, enemyNameTextRect)

class Knight(Enemy):
    weapon_type = Sword
    name = "Knight"
    initial = "K"
    colour = (200, 75, 0)


class Wizard(Enemy):
    weapon_type = Wand
    name = "Wizard"
    initial = "W"
    colour = (200, 0, 75)


class Soldier(Enemy):
    weapon_type = Gun
    name = "Soldier"
    initial = "S"
    colour = (0, 0, 100)

enemy_types: list[type[Enemy]] = [Knight, Soldier, Wizard]

def spawn_enemies(number: int, possible_locations: list[pygame.Vector2]) -> list[Enemy]:
    return_enemies: list[Enemy] = []
    for x in range(number):
        location = possible_locations[random.randint(0, len(possible_locations) - 1)]
        enemy_type = random.choice(enemy_types)
        return_enemies.append(enemy_type(100, location))
    return return_enemies

class Powerup(Item):
    time_remaining: int = 1000

    def __init__(self, location: pygame.Vector2):
        super().__init__(location)

class SpeedBoost(Powerup):
    name = "Increased Speed"
    colour = (0, 0, 200)

class DamageBoost(Powerup):
    name = "Damage x2"
    colour = (0, 200, 200)

class HealthBoost(Powerup):
    name = "+20 Health"
    colour = (200, 25, 25)

powerup_types: list[type[Powerup]] = [SpeedBoost, DamageBoost, HealthBoost]


def spawn_item(item_type: type[Item], possible_locations: list[pygame.Vector2], health_boost: bool = False) -> Item:
    location = possible_locations[random.randint(0, len(possible_locations) - 1)]
    if item_type == Powerup:
        powerup_type = HealthBoost if health_boost else random.choice(powerup_types)
        return powerup_type(location)
    else:
        weapon_type: type[Weapon] = random.choice(weapon_types)
        return weapon_type(location)


class Player(Entity):
    inventory: list[Item | None]
    powerups: list[Powerup]

    def __init__(self, health: float, position: pygame.Vector2, inventory: list[Item | None]):
        super().__init__(health, position, pygame.Rect(screen_width * 39/80, screen_height * 39/80, screen_width / 40, screen_height / 40))
        self.inventory = inventory
        self.powerups = []

@dataclasses.dataclass
class SaveFile:
    difficulty: int | None
    game_state: GameState | None