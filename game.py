import dataclasses
import math
import random
from abc import ABC
from enum import Enum
from typing import ClassVar

import pygame

from consts import tileWidth, tileHeight, screen_height, screen_width, font2, WALL_COLOR, FLOOR_COLOR, GRID_COLOR, \
    FLOOR_NEXT_COL, PresetMaps
from game_ui import UIBar, draw_rect_alpha


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
    ui_bars: list[UIBar]

    @classmethod
    def new_game(cls, difficulty: Difficulty) -> GameState:
        player = Player(100, pygame.Vector2(90, -10), [None, None])
        world_map = generate_map(PresetMaps, 5, 5)

        ground_tiles = get_ground_tiles(world_map)

        enemies = [Enemy.spawn(ground_tiles) for _ in range(40)]

        items: list[Item] = []
        for x in range(20):
            items.append(Powerup.spawn(ground_tiles))
            items.append(Weapon.spawn(ground_tiles))

        ui_bars = [
            UIBar("Player Health", (200, 25, 25), lambda: player.health / 100),
            UIBar("Enemies remaining", (128, 128, 128), lambda: len(enemies) / 40)
        ]

        return GameState(difficulty, player, enemies, [], [], items, world_map, ui_bars)

    def handle_click(self, mouse_pos: pygame.Vector2) -> None:
        if ((not self.player.inventory.background_rect.collidepoint(mouse_pos))
                and self.player.inventory.slots[self.player.inventory.active_slot].item is not None):
            self.player.attack(self)
        self.player.inventory.handle_click(mouse_pos, self)

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
        super().__init__(1.0, location, pygame.Rect((tileWidth * (location[0])),
                                                    (tileHeight * (location[1])) + tileHeight - (screen_height / 30) + 1, (screen_width / 30), (screen_height / 30)))


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
        super().__init__(0.1, position, pygame.Rect((tileWidth * (position[0])), (tileHeight * (position[1])),
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

    @staticmethod
    def spawn(possible_locations: list[pygame.Vector2]) -> Weapon:
        location = possible_locations[random.randint(0, len(possible_locations) - 1)]
        weapon_type = random.choice(weapon_types)
        return weapon_type(location)


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

    @staticmethod
    def spawn(possible_locations: list[pygame.Vector2]) -> Enemy:
        location = possible_locations[random.randint(0, len(possible_locations) - 1)]
        enemy_type = random.choice(enemy_types)
        return enemy_type(100, location)

    def attack(self, game_state: GameState) -> None:
        if game_state.difficulty != Difficulty.Very_Difficult: attackMultiplierEnemies = 1
        else: attackMultiplierEnemies = 2
        weapon = self.weapon
        if isinstance(weapon, Gun):
            weapon.shoot(game_state, self, self.position.copy(),
                         math.atan2((game_state.player.rect.centery - self.rect.centery),
                                    (game_state.player.rect.centerx - self.rect.centerx)),
                         attackMultiplierEnemies)
        elif isinstance(weapon, Sword):
            weapon.attack(game_state.player, attackMultiplierEnemies)
        elif isinstance(weapon, Wand):
            weapon.fire(game_state, game_state.player, self.position, attackMultiplierEnemies)

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

class Powerup(Item):
    time_remaining: int = 1000

    def __init__(self, location: pygame.Vector2):
        super().__init__(location)

    @staticmethod
    def spawn(possible_locations: list[pygame.Vector2]) -> Powerup:
        location = possible_locations[random.randint(0, len(possible_locations) - 1)]
        powerup_type = random.choice(powerup_types)
        return powerup_type(location)

class SpeedBoost(Powerup):
    name = "Increased Speed"
    colour = (0, 0, 200)

class DamageBoost(Powerup):
    name = "Damage x2"
    colour = (0, 200, 200)

class HealthBoost(Powerup):
    name = "+20 Health"
    colour = (200, 25, 25)

    @staticmethod
    def spawn(possible_locations: list[pygame.Vector2]) -> HealthBoost:
        location = possible_locations[random.randint(0, len(possible_locations) - 1)]
        return HealthBoost(location)

powerup_types: list[type[Powerup]] = [SpeedBoost, DamageBoost, HealthBoost]

class Player(Entity):
    inventory: Inventory
    powerups: list[Powerup]

    def __init__(self, health: float, position: pygame.Vector2, inventory: list[Item | None]):
        super().__init__(health, position, pygame.Rect(screen_width * 39/80, screen_height * 39/80, screen_width / 40, screen_height / 40))
        self.inventory = Inventory(inventory)
        self.powerups = []

    def attack(self, game_state: GameState) -> None:

        weapon = self.inventory.slots[self.inventory.active_slot].item
        if not isinstance(weapon, Weapon): return None

        if isinstance(weapon, Gun):
            angle = math.atan2((pygame.mouse.get_pos()[1] - self.rect.centery), (pygame.mouse.get_pos()[0] - self.rect.centerx))
            attack_multiplier = 1 if not any(isinstance(x, DamageBoost) for x in self.powerups) else 2
            weapon.shoot(game_state, self, get_grid_pos(self.position, False), angle, attack_multiplier)
        elif isinstance(weapon, Sword):
            for x in range(len(game_state.enemies)):
                if abs(game_state.enemies[x].rect.centerx - self.rect.centerx) < 50 and abs(game_state.enemies[x].rect.centery - self.rect.centery) < 50:
                    attack_multiplier = 1 if not any(isinstance(n, DamageBoost) for n in game_state.player.powerups) else 2
                    weapon.attack(game_state.enemies[x], attack_multiplier)
        elif isinstance(weapon, Wand):
            shortestDistance: tuple[Enemy | None, float] = None, 1000000.0
            for enemy in game_state.enemies:
                distanceToX = pygame.math.Vector2(enemy.rect.centerx - self.rect.centerx, enemy.rect.centery - self.rect.centery)
                if distanceToX.length() < shortestDistance[1]:
                    shortestDistance = enemy, distanceToX.length()
            if shortestDistance[1] < 300 and shortestDistance[0] is not None:
                attack_multiplier = 1 if not any(isinstance(x, DamageBoost) for x in game_state.player.powerups) else 2
                weapon.fire(game_state, shortestDistance[0], get_grid_pos(self.position, False), attack_multiplier)

def get_grid_pos(position: pygame.Vector2, return_int: bool = True) -> pygame.Vector2:
    if return_int:
        return pygame.Vector2(int((((screen_width / 2) - position.x) / tileWidth) // 1),
                              int((((screen_height / 2) - position.y) / tileHeight) // 1))
    return pygame.Vector2((((screen_width / 2) - position.x) / tileWidth), (((screen_height / 2) - position.y) / tileHeight))

@dataclasses.dataclass
class SaveFile:
    difficulty: int | None
    game_state: GameState | None

@dataclasses.dataclass
class InvSlot:
    item: Item | None
    rect: pygame.Rect

    def render(self, screen: pygame.Surface, slot_num: int, total_slots: int, active: bool) -> None:
        if active: draw_rect_alpha(screen, (200, 200, 200, 128), self.rect)
        if self.item:
            item_rect = pygame.Rect(screen_width / 2 - (50 * total_slots - (100 * slot_num)) + 35, screen_height - 60 - 12.5, 30, 25)
            pygame.draw.rect(screen, self.item.colour, item_rect)


class Inventory:
    slots: list[InvSlot] = []
    background_rect: pygame.Rect
    active_slot: int

    def __init__(self, items: list[Item | None]):
        self.active_slot = 0
        for n, item in enumerate(items):
            slot_rect = pygame.Rect((screen_width / 2) - (50 * len(items) - (100 * n)), screen_height - 100, 100, 80)
            self.slots.append(InvSlot(item, pygame.Rect(slot_rect)))
        self.background_rect = pygame.Rect((screen_width / 2) - (50 * len(items)), screen_height - 100,
                                       100 * len(items), 80)

    def render(self, screen: pygame.Surface) -> None:
        draw_rect_alpha(screen, (0, 0, 0, 128), self.background_rect)
        for n, slot in enumerate(self.slots):
            slot.render(screen, n, len(self.slots), self.active_slot == n)

    def drop_item(self, slot: int, game_state: GameState) -> None:
        item = self.slots[slot].item
        if item is None: return None
        item.position = pygame.Vector2(get_grid_pos(game_state.player.position)[0],
                       get_grid_pos(game_state.player.position)[1])
        game_state.spawned_items.append(item)
        self.slots[slot].item = None
        return None

    def handle_click(self, mouse_pos: pygame.Vector2, game_state: GameState) -> None:
        if not self.background_rect.collidepoint(mouse_pos): return None
        for n, slot in enumerate(self.slots):
            if slot.rect.collidepoint(mouse_pos):
                if self.active_slot == n: self.drop_item(n, game_state)
                self.active_slot = n
                break
        return None