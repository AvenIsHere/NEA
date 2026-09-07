import dataclasses
import math
import random
import sys
import jsonpickle  # type: ignore[import-untyped]

import pygame
from pygame.locals import QUIT

from consts import font2, font, font3, screen_width, tileWidth, screen_height, tileHeight
from enemy_pathfinding import PathfindingThread
from file import GameFile, save_game
from game import GameState, Knight, Weapon, HealthBoost, Powerup, Player, \
    Enemy, DamageBoost, get_camera_offset
from game_ui import UIBar, draw_rect_alpha
from menu import MainMenu, Button

# Pygame initialization
pygame.init()
screen = pygame.display.set_mode((1152, 648))
pygame.display.set_caption('NEA')

# TODO: Replace remaining globals
tileRect: list[list[pygame.Rect]]
timeSinceSpawnHealthBoosts = 0
attackMultiplierEnemies = 1
pathfindingThread: PathfindingThread


def render_UI(game_state: GameState) -> None:
    for i, ui_bar in enumerate(reversed(game_state.ui_bars)):
        if ui_bar.get_percent() <= 0:
            game_state.ui_bars.remove(ui_bar)
            continue
        ui_bar.render(screen, pygame.Vector2(20, 20 + (i * 50)))


@dataclasses.dataclass
class RenderedElements:
    tiles_rendered: list[list[pygame.Rect]]


def render_map(game_state: GameState) -> list[list[pygame.Rect]]:
    tiles_rendered: list[list[pygame.Rect]] = []
    for x, colour in enumerate(game_state.tile_map.grid, start=0):
        tiles_rendered.append([])
        for y, tileColour in enumerate(colour, start=0):
            tiles_rendered[x].append(pygame.Rect((tileWidth * x) + get_camera_offset(game_state.player.position)[0],
                                                 (tileHeight * y) + get_camera_offset(game_state.player.position)[1],
                                                 tileWidth + 1, tileHeight + 1))
            pygame.draw.rect(screen, tileColour.colour, tiles_rendered[x][y])
    return tiles_rendered


def render_frame(game_state: GameState) -> RenderedElements:
    screen.fill((50, 50, 50))
    tiles_rendered = render_map(game_state)
    render_items(game_state)
    render_enemies(game_state)
    game_state.player.render(screen)
    render_UI(game_state)
    game_state.player.inventory.render(screen)
    return RenderedElements(tiles_rendered)


def game_frame(game_state: GameState, render_data: RenderedElements) -> None:
    global pathfindingThread, attackMultiplierEnemies, timeSinceSpawnHealthBoosts, tileRect

    game_state.player.move(game_state.tile_map)

    tileRect = render_data.tiles_rendered
    if pygame.key.get_pressed()[pygame.K_e]: collect_item(game_state)

    for enemy in game_state.enemies:
        enemy.move(game_state.tile_map)
        distance = pygame.math.Vector2(abs(enemy.rect.x - game_state.player.rect.x),
                                       abs(enemy.rect.y - game_state.player.rect.y))
        if isinstance(enemy, Knight) and distance.length() < 40:
            enemy.attack(game_state)
        if not isinstance(enemy, Knight) and distance.length() < 300:
            enemy.attack(game_state)
        enemy.weapon.time_since_attack += 1

    manage_bullets(game_state)
    manage_magic(game_state)

    for slot in game_state.player.inventory.slots:
        if isinstance(slot.item, Weapon): slot.item.time_since_attack += 1

    health_boost_num = sum(
        1 for item in game_state.spawned_items
        if isinstance(item, HealthBoost)
    )
    if health_boost_num < 10 and timeSinceSpawnHealthBoosts >= 600:
        game_state.spawned_items.append(Powerup.spawn(game_state.tile_map.get_ground_tiles()))
        timeSinceSpawnHealthBoosts = 0
    timeSinceSpawnHealthBoosts += 1

    for powerup in game_state.player.powerups:
        powerup.time_remaining -= 1
        if powerup.time_remaining <= 0: game_state.player.powerups.remove(powerup)


def lostGame(game_state: GameState) -> None:
    lostGameRect = pygame.Rect(0, 0, screen_width, screen_height)
    draw_rect_alpha(screen, (50, 50, 50, 128), lostGameRect)
    lostGameText = font.render("GAME OVER!", True, (255, 0, 0))
    lostGameTextRect = lostGameText.get_rect(center=(screen_width / 2, screen_height / 6))
    screen.blit(lostGameText, lostGameTextRect)
    Button.inline_button('Respawn', (lostGameTextRect.centerx, lostGameTextRect.centery + 100), (150, 37.5), (100, 100, 100), lambda: respawn(game_state), screen)


def wonGame(game_state: GameState) -> None:
    lostGameRect = pygame.Rect(0, 0, screen_width, screen_height)
    draw_rect_alpha(screen, (50, 50, 50, 128), lostGameRect)
    lostGameText = font.render("YOU WON!", True, (255, 0, 0))
    lostGameTextRect = lostGameText.get_rect(center=(screen_width / 2, screen_height / 6))
    screen.blit(lostGameText, lostGameTextRect)
    Button.inline_button('Play again', (lostGameTextRect.centerx, lostGameTextRect.centery + 100), (150, 37.5), (100, 100, 100),
           lambda: respawn(game_state), screen)


def respawn(game_state: GameState) -> None:
    game_state.player.health = 100
    ground_tiles = game_state.tile_map.get_ground_tiles()
    game_state.player.position = random.choice(ground_tiles)
    game_state.enemies = [Enemy.spawn(ground_tiles) for _ in range(40)]
    game_state.ui_bars = [
        UIBar("Health remaining", (200, 25, 25), lambda: game_state.player.health / 100),
        UIBar("Enemies remaining", (128, 128, 128), lambda: len(game_state.enemies) / 40)
    ]


def manage_magic(game_state: GameState) -> None:
    for magic in game_state.wand_magic_fired:
        if isinstance(magic.target, Player):
            target_pos = magic.target.position
            dx, dy = (target_pos[0] - (magic.position[0]), target_pos[1] - (magic.position[1]))
        elif isinstance(magic.target, Enemy):
            dx, dy = (magic.target.position[0] - (magic.position[0]), magic.target.position[1] - (magic.position[1]))
        magic.age += 1
        if magic.age >= 250:
            game_state.wand_magic_fired.remove(magic)
            continue
        if magic.rect.colliderect(magic.target.rect):
            if magic.target.health <= 1:
                magic.target.health = 0
            else:
                magic.target.health = int(
                    (magic.target.health * ((5 / 6) + (1 / 20))) // 1)
            game_state.wand_magic_fired.remove(magic)
        step_x, step_y = (dx / 25, dy / 25)
        magic.position = pygame.Vector2(magic.position[0] + step_x, magic.position[1] + step_y)
        magic.rect = pygame.Rect((tileWidth * magic.position[0]) + get_camera_offset(game_state.player.position).x,
                                 (tileHeight * magic.position[1]) + get_camera_offset(game_state.player.position).y,
                                 magic.target.rect.width / 4,
                                 magic.target.rect.width / 4)
        pygame.draw.circle(screen, (100, 255, 255), magic.rect.center, magic.rect.width)

def manage_bullets(given_state: GameState) -> None:
    breakForLoop = False

    for bullet in given_state.bullets_fired:
        bulletRect = pygame.Rect((tileWidth * bullet.position[0]) + get_camera_offset(given_state.player.position).x,
                                 (tileHeight * bullet.position[1]) + get_camera_offset(given_state.player.position).y,
                                 10, 10)
        bulletSurface = pygame.Surface((bulletRect.width, bulletRect.height))
        bulletSurface = pygame.transform.rotate(bulletSurface, math.degrees(bullet.direction))
        bulletSurfaceRect = bulletSurface.get_rect()
        bulletSurfaceRect.center = bulletRect.center
        pygame.draw.rect(screen, (255, 164, 0), bulletSurfaceRect)
        bullet.position[0] += 0.2 * math.cos(bullet.direction)
        bullet.position[1] += 0.2 * math.sin(bullet.direction)
        if isinstance(bullet.shot_by, Player):
            for enemy in given_state.enemies:
                if not bulletSurfaceRect.colliderect(enemy.rect):
                    continue
                if enemy.health <= 15:
                    given_state.enemies.remove(enemy)
                else:
                    damage_multiplier = 1 if not any(isinstance(x, DamageBoost) for x in given_state.player.powerups) else 2
                    enemy.health -= 15 * damage_multiplier
                given_state.bullets_fired.remove(bullet)
                breakForLoop = True
                break
            if breakForLoop:
                break
        else:
            if bulletSurfaceRect.colliderect(given_state.player.rect):
                given_state.player.health -= 1 * attackMultiplierEnemies
                break
        for y, tileRectRow in enumerate(tileRect):
            for z, tileRectRowColumn in enumerate(tileRectRow):
                if bulletSurfaceRect.colliderect(tileRect[y][z]) and (
                        given_state.tile_map.grid[y][z].collision):
                    given_state.bullets_fired.remove(bullet)
                    breakForLoop = True
                    break
            if breakForLoop:
                break
        if breakForLoop:
            break
        if bullet.position[0] <= 0:
            given_state.bullets_fired.remove(bullet)
            break
        if bullet.position[0] >= 66:
            given_state.bullets_fired.remove(bullet)
            break
        if bullet.position[1] <= 0:
            given_state.bullets_fired.remove(bullet)
            break
        if bullet.position[1] >= 67:
            given_state.bullets_fired.remove(bullet)
            break


def collect_item(game_state: GameState) -> None:
    for x, item in reversed(list(enumerate(game_state.spawned_items))):
        if not (abs(game_state.player.rect.x - item.rect[0]) < 100 and abs(
                game_state.player.rect.y - item.rect[1]) < 100):
            continue
        if isinstance(item, Weapon):
            for i in range(len(game_state.player.inventory.slots)):
                if not game_state.player.inventory.slots[i].item:
                    game_state.player.inventory.slots[i].item = item
                    game_state.spawned_items.remove(item)
                    break
            return
        if isinstance(item, HealthBoost):
            if game_state.player.health == 100:
                continue
            if game_state.player.health < 80:
                game_state.player.health += 20
            else:
                game_state.player.health = 100
            game_state.spawned_items.remove(item)
            break
        if isinstance(item, Powerup):
            if any(isinstance(x, type(item)) for x in game_state.player.powerups): continue
            game_state.player.powerups.append(item)
            game_state.spawned_items.remove(item)
            game_state.ui_bars.append(UIBar(item.name, item.colour, lambda: item.time_remaining / 1000))
            break



def render_items(game_state: GameState) -> None:
    width = screen_width / 30
    height = screen_height / 30
    for x, item in enumerate(game_state.spawned_items):
        item.rect = pygame.Rect((tileWidth * item.position[0]) + get_camera_offset(game_state.player.position)[0],
                                   (tileHeight * item.position[1]) + get_camera_offset(game_state.player.position)[
                                       1] + tileHeight - height + 1, width, height)
        if isinstance(item, Powerup):
            pygame.draw.rect(screen, item.colour, item.rect)
            if isinstance(item, HealthBoost):
                enemyNameText = font2.render("+", True, (255, 255, 255))
                enemyNameTextRect = enemyNameText.get_rect(center=(item.rect.center[0], item.rect.center[1]))
                screen.blit(enemyNameText, enemyNameTextRect)
        elif isinstance(item, Weapon):
            pygame.draw.rect(screen, item.colour, item.rect)
        if abs(game_state.player.rect.x - item.rect[0]) < 100 and abs(
                game_state.player.rect.y - item.rect[1]) < 100:
            itemText = font2.render(item.name, True, (30, 30, 30))
            itemTextRect = itemText.get_rect(center=(item.rect.center[0], item.rect.center[1] - 20))
            itemText2 = font3.render("Press E to pick up", True, (30, 30, 30))
            itemTextRect2 = itemText2.get_rect(center=(item.rect.center[0], item.rect.center[1] - 35))
            screen.blit(itemText, itemTextRect)
            screen.blit(itemText2, itemTextRect2)

jumping = False
jumpCount: int = 0

def jump(game_state: GameState) -> None:
    global jumpCount, jumping
    amount = 0.1
    mult = 0.05 if jumpCount < 40 else 0
    move = pygame.math.Vector2(0, -amount * mult)
    game_state.player.current_speed += move
    jumpCount += 1

def render_enemies(given_state: GameState) -> None:
    for enemy in given_state.enemies:
        enemy.render(given_state, screen)

def start_pathfinding(game_state: GameState) -> None:
    global pathfindingThread
    ground_tiles = game_state.tile_map.get_ground_tiles()
    ground_tile_map = game_state.tile_map.get_ground_map(ground_tiles)
    pathfindingThread = PathfindingThread(game_state, ground_tile_map)

clock = pygame.time.Clock()
main_menu = MainMenu()
game_file: GameFile | None = None

while True:

    for event in pygame.event.get():
        if event.type == QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            if game_file is not None: save_game(game_file)
            pygame.quit()
            sys.exit()
        if game_file is None:
            main_menu.handle_input(event)
            continue
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if not jumping:
                    jumping = True
                    jumpCount = 0
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                if not jumping: continue
                game_file.game_state.player.current_speed.y -= -0.1 * 0.05 * (40 if jumpCount > 40 else jumpCount)
                jumping = False
                jumpCount = 0
        game_file.game_state.handle_input(event)

    pygame.display.update()
    screen.fill((20, 20, 20))

    if game_file is None:
        main_menu.render(screen)
        game_file = main_menu.get_game()
        if game_file: start_pathfinding(game_file.game_state)

    if game_file is not None:
        render_data = render_frame(game_file.game_state)
        if game_file.game_state.player.health <= 0: lostGame(game_file.game_state)
        elif not game_file.game_state.enemies: wonGame(game_file.game_state)
        else: game_frame(game_file.game_state, render_data)

        key = pygame.key.get_pressed()

        if not game_file.game_state.player.health <= 0:
            if jumping:
                jump(game_file.game_state)

    clock.tick(60)
