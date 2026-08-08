# importing different libraries
import dataclasses
import math
import os
import random
import sys
from abc import ABC
from enum import Enum
from threading import Thread

import pathfinding  # type: ignore[import-untyped]
import pygame
from pathfinding.core.diagonal_movement import DiagonalMovement  # type: ignore[import-untyped]
from pathfinding.core.grid import Grid  # type: ignore[import-untyped]
from pathfinding.finder.a_star import AStarFinder  # type: ignore[import-untyped]
from pygame.locals import QUIT

pygame.init()
pygame.joystick.init()
joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]

# defining different variables
screen = pygame.display.set_mode((1152, 648))
pygame.display.set_caption('NEA')
font = pygame.font.Font(None, 32)
font2 = pygame.font.Font(None, 24)
font3 = pygame.font.Font(None, 12)

loadMenu = True
ButtonsListOffset = 0
mouseNotUp = False
ButtonNotUp = False
TriggerNotUp = False
WALL_COLOR = (50, 50, 50)
GRID_COLOR = (0, 0, 0)
FLOOR_COLOR = (255, 255, 255)
FLOOR_NEXT_COL = (0, 0, 255)
gravity = -1.5
screenWidth = screen.get_width()
screenHeight = screen.get_height()
tileWidth = screenWidth / 20
tileHeight = screenHeight / 20
PresetMaps = [
    # the maps used in the game. "-" is the floors/walls (where the player cant pass through), and " " is empty space, where the player can pass through.
    ['-----------   -',
     '              -',
     '   --         -',
     '-       -------',
     '-              ',
     '----           ',
     '-----   --     ',
     '               ',
     '   -----      -',
     '              -',
     '             --',
     '             --',
     '---      ------'],

    ['------    -----',
     '------   ------',
     '-         -----',
     '-       -------',
     '     --     ---',
     '              -',
     '  ----  ---   -',
     '              -',
     '-      ---     ',
     '              -',
     '------   ------',
     '-------  ------',
     '------    -----'],

    ['        -----  ',
     '       -----   ',
     '       ----    ',
     '       -----   ',
     '  -------      ',
     '   ------      ',
     '              -',
     '              -',
     '             --',
     '-     ---   ---',
     '            ---',
     '     ---  - ---',
     '    -----------'],

    ['--   --   ---  ',
     ' --  ---   ----',
     '    ----   ----',
     '              -',
     '----           ',
     '               ',
     '-  ------      ',
     '  --    -      ',
     '      ----     ',
     '-             -',
     '-  ----     ---',
     '---------  ----',
     '-------     ---']
]

class Menu(Enum):
    MAIN = 0
    NEW = 1
    PLAY = 2
    SETTINGS = 3

menu: Menu = Menu.MAIN

@dataclasses.dataclass
class GameState:
    player: Player
    enemies: list[Enemy]
    bullets_fired: list[Bullet]
    wand_magic_fired: list[WandMagicThing]


class Entity(ABC):
    health: float
    position: pygame.Vector2
    rect: pygame.Rect

    def __init__(self, health: float, position: pygame.Vector2, rect: pygame.Rect):
        self.health = health
        self.position = position
        self.rect = rect


@dataclasses.dataclass
class Item(ABC):
    location: pygame.Vector2
    name: str
    colour: tuple[int, int, int]


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
    time_since_attack: int
    cooldown: int

    def __init__(self, location: pygame.Vector2, name: str, colour: tuple[int, int, int], strength: float = 1.0):
        self.name = name
        self.colour = colour
        self.cooldown = 10
        self.time_since_attack = 0
        self.location = location
        self.strength = strength


class Sword(Weapon):

    def __init__(self, location: pygame.Vector2, strength: float = 1.0):
        super().__init__(location, "Sword", (200, 200, 0), strength)

    def attack(self, target: Entity, attack_multiplier: float = 1) -> None:
        if self.time_since_attack <= self.cooldown:
            return

        target.health -= self.strength * attack_multiplier
        self.cooldown = random.randint(25, 40)

        self.time_since_attack = 0


class Gun(Weapon):

    def __init__(self, location: pygame.Vector2, strength: float = 1.0):
        super().__init__(location, "Gun", (0, 200, 0), strength)

    def shoot(self, given_state: GameState, shot_by: Entity, location: pygame.Vector2, direction: float,
              attack_multiplier: float = 1) -> None:
        if self.time_since_attack <= self.cooldown:
            return

        given_state.bullets_fired.append(Bullet(location, direction, self.strength * attack_multiplier, shot_by))
        self.cooldown = random.randint(10, 15)

        self.time_since_attack = 0


class Wand(Weapon):

    def __init__(self, location: pygame.Vector2, strength: float = 1.0):
        super().__init__(location, "Wand", (100, 255, 255), strength)

    def fire(self, given_state: GameState, target: Entity, location: pygame.Vector2, attack_multiplier: float = 1) -> None:
        if self.time_since_attack <= self.cooldown:
            return

        given_state.wand_magic_fired.append(WandMagicThing(location, 0, target, self.strength * attack_multiplier))
        self.cooldown = random.randint(100, 150)

        self.time_since_attack = 0


weapon_types: list[type[Weapon]] = [Sword, Gun, Wand]


class Enemy(Entity, ABC):
    name: str
    initial: str
    colour: tuple[int, int, int]
    weapon: Weapon

    def __init__(self, health: int, location: pygame.Vector2): ...

    def _init_inner(self, weapon: Weapon, health: float, position: pygame.Vector2) -> None:
        super().__init__(health, position, pygame.Rect((tileWidth * (position[0])),
                                           (tileHeight * (position[1])) + tileHeight - (
                                                screenHeight / 30) + 1,
                                           screenWidth / 30, screenHeight / 30))
        self.weapon = weapon

    def render(self, game_state: GameState) -> None:
        self.rect = pygame.Rect(
            (tileWidth * (self.position[0])) + game_state.player.position[0],
            (tileHeight * (self.position[1])) + game_state.player.position[1] + tileHeight - (
                    screenHeight / 30) + 1,
            screenWidth / 30, screenHeight / 30)
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

    def __init__(self, health: float, position: pygame.Vector2):
        self._init_inner(new_weapon(position, Sword), health, position)
        self.name = "Knight"
        self.initial = "K"
        self.colour = (200, 75, 0)


class Wizard(Enemy):

    def __init__(self, health: float, position: pygame.Vector2):
        self._init_inner(new_weapon(position, Wand), health, position)
        self.name = "Wizard"
        self.initial = "W"
        self.colour = (200, 0, 75)


class Soldier(Enemy):

    def __init__(self, health: float, position: pygame.Vector2):
        self._init_inner(new_weapon(position, Gun), health, position)
        self.name = "Soldier"
        self.initial = "S"
        self.colour = (0, 0, 100)


enemy_types: list[type[Enemy]] = [Knight, Soldier, Wizard]


class PowerupType(Enum):
    SPEED_BOOST = 0
    DAMAGE_BOOST = 1
    HEALTH_BOOST = 2


@dataclasses.dataclass
class Powerup(Item):
    type: PowerupType


powerups: dict[PowerupType, tuple[str, tuple[int, int, int]]] = {
    PowerupType.SPEED_BOOST: ("Increased Speed", (0, 0, 200)),
    PowerupType.DAMAGE_BOOST: ("Damage x2", (0, 200, 200)),
    PowerupType.HEALTH_BOOST: ("+20 Health", (200, 25, 25))
}


class Player(Entity):
    inventory: list[Item | None]

    def __init__(self, health: float, position: pygame.Vector2, rect: pygame.Rect, inventory: list[Item | None]):
        super().__init__(health, position, rect)
        self.inventory = inventory


inGame = False


def button(text, position, size, colour, action=None, *args) -> None:
    # draws a button on screen with optional function
    # input:
    #   text - string, determines what text will appear on the button
    #   position - tuple/array, determines where the button will be placed on the screen
    #   size - tuple/array, determines the size of the button
    #   colour - tuple, determines the colour of the button
    #   action (optional) - function name, determines which function (if any) is called when the button is clicked
    #   *args (optional) - any, arguments that are passed through to the function called when the button is pressed
    # output:
    #   This function displays a button on screen. It shows text on the button, and may also do something when clicked.
    global mouseNotUp
    button_rect = pygame.Rect(position[0] - (size[0] / 2), position[1] - (size[1] / 2), size[0],
                              size[1])  # creates a pygame Rect for the button
    pygame.draw.rect(screen, colour, button_rect)  # draws that rect onto the screen
    text = font.render(text, True, (0, 0, 0))  # creates the text to write on the screen
    textRect = text.get_rect(
        center=button_rect.center)  # creates a pygame rect for the text on the screen in the middle of the button
    screen.blit(text, textRect)  # draws the text on the screen
    if button_rect.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[
        0] and mouseNotUp == False and action is not None:  # determines whether or not the button has been pressed
        action(*args)  # does the action associated with pressing the button
        mouseNotUp = True

def menuEquals(menu_set: Menu) -> None:
    # Changes current menu to the menu in the input menu_set.
    # This function exists due to the way the button function works. Buttons can only call a function, so a function must be made to change a variable.
    # input:
    #   menu_set - string, determines which menu will be displayed.
    # output:
    #   menu - string, used in the menu function to display the correct menu
    global menu
    global difficulty
    global typedText
    global ButtonsListOffset
    menu = menu_set
    if menu == Menu.NEW:
        difficulty = 'Easy'
        typedText = ''
    if menu == Menu.PLAY:
        if os.path.isdir('gamesaves'):
            global gameSaves
            gameSaves = os.listdir('gamesaves')
        else:
            os.mkdir('gamesaves')
    ButtonsListOffset = 0


def drawTextBox(text, position, colour, borderColour, borderSize, typedText):
    # draws a text box that the user can type into. This is used in the file creation screen so that the user can type the name of the file.
    # Input:
    #   text - string, the default text to be displayed when nothing has been typed
    #   position - tuple, determines the position of the text box
    #   size - tuple/array, was planned to determine the size of the text box, currently unused.
    #   colour - tuple, determines the colour of the text box
    #   borderColour - tuple, determines the colour of the border
    #   borderSize - tuple/array, determines the size of the border
    #   typedText - string, the text that has been typed and will be displayed in the text box, if any.
    # Output:
    #   displays a text box on the screen
    if typedText == '':
        text = font.render(text, True, (0, 0, 0))
        textRect = text.get_rect(center=position)
    else:
        text = font.render(typedText, True, (0, 0, 0))
        textRect = text.get_rect(center=position)
    pygame.draw.rect(screen, colour, textRect)
    pygame.draw.rect(screen, borderColour, (
        textRect.x - borderSize, textRect.y - borderSize, textRect.width + borderSize * 2,
        textRect.height + borderSize * 2), borderSize)
    screen.blit(text, textRect)


def setDifficulty():
    # changes the difficulty in the create file menu
    # Exists due to how the button function works
    # When the difficulty button is pressed in the create file menu, this function changes the difficulty of the file
    global difficulty
    difficulties = {
        'Easy': 'Medium',
        'Medium': 'Difficult',
        'Difficult': 'Very difficult',
        'Very difficult': 'Easy'
    }
    difficulty = difficulties.get(difficulty, 'Easy')


def createFile():
    # creates a game file
    # Input:
    #   difficulty - string, determines the difficulty of the game save
    #   typedText - string, determines the name of the game file
    # Output:
    #   Creates a game file with the name provided
    global fileName
    global difficulty
    global gameSaves
    file = open(f'gamesaves/{typedText}.txt', 'w')
    file.write(f'Difficulty{difficulty}\n')
    file.write(f'firstplaythroughTrue\n')
    for x in range(2):
        file.write(f'None\n')
    gameSaves = os.listdir('gamesaves')


game_state_global = None


def loadFile(file: str) -> None:
    # loads the chosen game file. This function closes the main menu and starts the game
    # Input:
    #   file - string, determines which file is loaded
    # Output:
    #   Starts the game

    global inGame, loadMenu, currentFile, tile_map, fileLine, game_state_global
    inGame = True
    loadMenu = False
    currentFile = file
    enemies: list[Enemy] = []
    bullets_fired: list[Bullet] = []
    wand_magic_fired: list[WandMagicThing] = []
    player = Player(100, pygame.Vector2(0, 0), pygame.Rect(screenWidth / 2 - (screenWidth / 2) / 40,
                                             screenHeight / 2 - (screenHeight / 2) / 40, (screenWidth / 2) / 20,
                                             (screenHeight / 2) / 20), [None, None])
    game_state_global = GameState(player, enemies, bullets_fired, wand_magic_fired)
    with open(f"gamesaves/{file}", "r") as f:
        fileLine = [line.strip() for line in f]
    if fileLine[1] == "firstPlaythroughFalse":
        player.position = pygame.Vector2(float(fileLine[2].split(" ")[0]), float(fileLine[2].split(" ")[1]))
        tile_map = []
        mapTemp = fileLine[3].split("  ")
        for x in range(len(mapTemp)):
            tile_map.append(mapTemp[x].split(" "))
        for y in range(len(tile_map)):
            for x in range(len(tile_map[y])):
                if tile_map[y][x] == "FLOOR_COLOR":
                    tile_map[y][x] = FLOOR_COLOR
                elif tile_map[y][x] == "FLOOR_NEXT_COL":
                    tile_map[y][x] = FLOOR_NEXT_COL
                elif tile_map[y][x] == "WALL_COLOR":
                    tile_map[y][x] = WALL_COLOR
                elif tile_map[y][x] == "GRID_COLOR":
                    tile_map[y][x] = GRID_COLOR
    load_save(file, game_state_global)


def mainMenu(menu):
    # Shows and handles almost everything related to the main menu
    # It determines which buttons to show, then displays them on the screen.
    # Input:
    #   menu - string, controls which menu is currently showing
    # Output:
    #   displays the current menu on the screen
    global menuNameTextRect
    global buttonsList
    menuNameMap = {
        Menu.MAIN: "Game Name",
        Menu.PLAY: "Game Name",
        Menu.SETTINGS: "Settings",
        Menu.NEW: "New Game",
    }
    menuNameText = font.render(menuNameMap[menu], True, (255, 255, 255))
    menuNameTextRect = menuNameText.get_rect(center=(screenWidth / 2, screenHeight / 6))
    if menu == Menu.MAIN:
        buttonsList = [['Play', menuEquals, Menu.PLAY], ['Settings', menuEquals, Menu.SETTINGS], ['Quit', pygame.quit]]
    elif menu == Menu.SETTINGS:
        buttonsList = []
        button('Back', (menuNameTextRect.centerx, menuNameTextRect.centery + 200), (150, 37.5), (100, 100, 100),
               menuEquals, Menu.MAIN)
    elif menu == Menu.PLAY:
        buttonsList = [['New Game', menuEquals, Menu.NEW]]
        for savefile in gameSaves:
            buttonsList.append([savefile[:len(savefile) - 4], loadFile, savefile])
        if len(buttonsList) < 4:
            button('Back', (menuNameTextRect.centerx, menuNameTextRect.centery + 200), (150, 37.5), (100, 100, 100),
                   menuEquals, Menu.MAIN)
        else:
            buttonsList.append(['Back', menuEquals, Menu.MAIN])
    elif menu == Menu.NEW:
        drawTextBox(f'Enter a name for your new game', (menuNameTextRect.centerx, menuNameTextRect.centery + 50),
                    (100, 100, 100), (0, 0, 0), 2, typedText)
        buttonsList = [None, [f'Difficulty: {difficulty}', setDifficulty], ['Start', createFile],
                       ['Back', menuEquals, Menu.PLAY]]
    for i in range(len(buttonsList)):
        if buttonsList[i] == None:
            pass
        elif len(buttonsList[i]) == 1:
            button(buttonsList[i][0],
                   (menuNameTextRect.centerx, menuNameTextRect.centery + ButtonsListOffset + (50 + (i * 50))),
                   (150, 37.5), (100, 100, 100))
        elif len(buttonsList[i]) == 2:
            button(buttonsList[i][0],
                   (menuNameTextRect.centerx, menuNameTextRect.centery + ButtonsListOffset + (50 + (i * 50))),
                   (150, 37.5), (100, 100, 100), buttonsList[i][1])
        elif len(buttonsList[i]) == 3:
            button(buttonsList[i][0],
                   (menuNameTextRect.centerx, menuNameTextRect.centery + ButtonsListOffset + (50 + (i * 50))),
                   (150, 37.5), (100, 100, 100), buttonsList[i][1], buttonsList[i][2])
    TextBackground = pygame.Rect(0, 0, screenWidth, menuNameTextRect.centery + 15)
    pygame.draw.rect(screen, (20, 20, 20), TextBackground)
    screen.blit(menuNameText, menuNameTextRect)


def get_grid_pos(position: pygame.Vector2, return_int: bool = True) -> list[int] | list[float]:
    if return_int:
        return [int((((screenWidth / 2) - position.x) / tileWidth) // 1),
                int((((screenHeight / 2) - position.y) / tileHeight) // 1)]
    return [(((screenWidth / 2) - position.x) / tileWidth), (((screenHeight / 2) - position.y) / tileHeight)]


mapGenerated = False

inThread = False


def do_pathfinding(game_state: GameState):
    # Determines if the enemies should be moving.
    # for each enemy, it finds the players position, the enemies position, the possible paths that can be taken, and finally whether a path exists between the enemy and the player
    # It then moves the enemy in the direction of the player (or away, if that is what the pathfinding finds) if a path was found.
    # A new path for each enemy is only generated every 50 frames, however the enemy is moved every frame.
    global enemiesToMove, grid, pathGrid, pathTicks, inThread, onGroundMap
    inThread = True
    if pathTicks == 0:
        enemiesToMove = []
        grid = Grid(matrix=onGroundMap)
        for x in range(len(game_state.enemies)):
            if abs(get_grid_pos(game_state.player.position)[0] - int(
                    game_state.enemies[x].position[0] // 1)) <= 21 and abs(
                    get_grid_pos(game_state.player.position)[1] - int(game_state.enemies[x].position[1] // 1)) <= 21:
                start = grid.node(int(game_state.enemies[x].position[0] // 1),
                                  int(game_state.enemies[x].position[1] // 1))
                end = grid.node(get_grid_pos(game_state.player.position)[0],
                                get_grid_pos(game_state.player.position)[1])
                finder = AStarFinder(diagonal_movement=DiagonalMovement.never)
                path, runs = finder.find_path(start, end, grid)
                pathGrid = grid.grid_str(path=path, start=start, end=end).split('\n')
                if isinstance(game_state.enemies[x], Wizard):
                    for l in range(len(pathGrid)):
                        if 'se' in pathGrid[l] and not '#se' in pathGrid[l]:
                            n = int(get_grid_pos(game_state.player.position)[0] // 1) - 2
                            enemiesToMove.append([x, (n, l)])
                        elif 'es' in pathGrid[l] and not 'es#' in pathGrid[l]:
                            n = int(get_grid_pos(game_state.player.position)[0] // 1) + 2
                            enemiesToMove.append([x, (n, l)])
                        elif 'sxxe' in pathGrid[l] or 'exxs' in pathGrid[l]:
                            pass
                        elif 'x' in pathGrid[l]:
                            for z in range(len(pathGrid[l])):
                                if pathGrid[l][z] == 's':
                                    sLocation = z
                            for z in range(len(pathGrid[l])):
                                if pathGrid[l][z] == 'e':
                                    eLocation = z
                            if sLocation < eLocation:
                                n = int(get_grid_pos(game_state.player.position)[0] // 1) - 1
                            elif eLocation < sLocation:
                                n = int(get_grid_pos(game_state.player.position)[0] // 1) + 1
                            enemiesToMove.append([x, (n, l)])
                elif isinstance(game_state.enemies[x], Knight):
                    for l in range(len(pathGrid)):
                        if 'x' in pathGrid[l] or 'se' in pathGrid[l] or 'es' in pathGrid[l]:
                            for i in reversed(range(len(pathGrid[l]))):
                                if pathGrid[l][i] == 'x' or (pathGrid[l][i] == 'e' and (
                                        pathGrid[l][i - 1] == 's' or pathGrid[l][i + 1] == 's')):
                                    n = get_grid_pos(game_state.player.position)[0]
                            enemiesToMove.append([x, (n, l)])
        pathTicks = 50
    if enemiesToMove != []:
        for x in range(len(enemiesToMove)):
            if game_state.enemies[enemiesToMove[x][0]].position != enemiesToMove[x][1]:
                if game_state.enemies[enemiesToMove[x][0]].position[0] // 1 > enemiesToMove[x][1][0] // 1:
                    game_state.enemies[enemiesToMove[x][0]].position[0] -= 0.05
                if game_state.enemies[enemiesToMove[x][0]].position[0] // 1 < enemiesToMove[x][1][0] // 1:
                    game_state.enemies[enemiesToMove[x][0]].position[0] += 0.05
    pathTicks -= 1
    inThread = False


health_boost_num = 0
timeSinceSpawnHealthBoosts = 0

attackMultiplierEnemies = 1

enemiesDefeated = False


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
                colour_map[chosen_presets[y // preset_len_y][x // preset_len_x][x % preset_len_x][y % preset_len_y]])
            if not world_map[-1]: world_map.pop()

    return world_map


def load_save(file: str, game_state: GameState) -> None:
    global enemiesDefeated, difficulty, attackMultiplierEnemies, health_boost_num, timeSinceSpawnHealthBoosts, fileLine, firstTimeRun, timeSinceGun, enemyPreviousPosition, TriggerNotUp, spawnedItems, gameLost, tile_map, tileRect, tile, running, mapGenerated, cells, givePaths, pathTicks, enemiesToMove, grid, inThread, ButtonNotUp, mouseNotUp
    game_state.player.inventory = [None, None]
    with open(f"gamesaves/{file}", "r") as f:
        fileLine = [line.strip() for line in f]
    enemiesDefeated = False
    gameLost = False
    pathTicks = 0
    spawnedItems = []
    enemiesToMove = []
    if fileLine[0] == "DifficultyEasy":
        difficulty = 1
        attackMultiplierEnemies = 0.5
    elif fileLine[0] == "DifficultyMedium":
        difficulty = 2
        attackMultiplierEnemies = 0.8
    elif fileLine[0] == "DifficultyDifficult":
        difficulty = 3
        attackMultiplierEnemies = 1
    elif fileLine[0] == "DifficultyVery difficult":
        difficulty = 4
        attackMultiplierEnemies = 1.25
    if fileLine[1] == "firstplaythroughTrue":
        game_state.player.position = [90, -10]
        fileLine[2] = game_state.player.position
        tile_map = generate_map(PresetMaps, 5, 5)
        fileLine[1] = 'firstPlaythroughFalse'
    isOnGround()
    for x in range(20):
        spawnedItems.append(spawn_item(Powerup))
        spawnedItems.append(spawn_item(Weapon))
    if difficulty == 1: health_boost_num = 10
    elif difficulty == 2: health_boost_num = 5
    for x in range(health_boost_num):
        spawnedItems.append(spawn_item(Powerup, True))
    game_state.enemies = spawnEnemies(40)
    enemyPreviousPosition = []
    for x in range(len(game_state.enemies)):
        enemyPreviousPosition.append(game_state.enemies[x].position)


@dataclasses.dataclass
class UIBar:
    percent: float
    text: str
    colour: tuple[int, int, int]


def render_UI(game_state: GameState, speed_boost_remaining: int, attack_boost_remaining: int) -> None:
    ui_items: list[UIBar] = []

    if game_state.player.health > 0: ui_items.append(
        UIBar(game_state.player.health / 100, str(game_state.player.health), (200, 25, 25)))
    if len(game_state.enemies) > 0: ui_items.append(
        UIBar(len(game_state.enemies) / 40, str(len(game_state.enemies)) + " enemies remaining", (128, 128, 128)))
    if speed_boost_remaining > 0: ui_items.append(UIBar(speed_boost_remaining / 1000, "Speed Boost", (50, 50, 255)))
    if attack_boost_remaining > 0: ui_items.append(UIBar(attack_boost_remaining / 1000, "Damage x2", (0, 200, 255)))

    for index, ui_element in enumerate(ui_items):
        element_bar = pygame.Rect(20, 20 + (index * 50), 200 * ui_element.percent, 20)
        element_text = font2.render(ui_element.text, True, (0, 0, 0))
        element_text_rect = element_text.get_rect(left=20, top=element_bar.bottom + 5)
        pygame.draw.rect(screen, ui_element.colour, element_bar)
        screen.blit(element_text, element_text_rect)


pathfindingThread = Thread(target=do_pathfinding)


@dataclasses.dataclass
class RenderedElements:
    items_rendered: dict[int, pygame.Rect]
    tiles_rendered: list[list[pygame.Rect]]
    inventory_background: pygame.Rect


def render_map(game_state: GameState, tile_map) -> list[list[pygame.Rect]]:
    tiles_rendered: list[list[pygame.Rect]] = []
    for x, colour in enumerate(tile_map, start=0):
        tiles_rendered.append([])
        for y, tileColour in enumerate(colour, start=0):
            tiles_rendered[x].append(pygame.Rect(((tileWidth) * (x)) + game_state.player.position[0],
                                                 ((tileHeight) * (y)) + game_state.player.position[1],
                                                 tileWidth + 1, tileHeight + 1))
            pygame.draw.rect(screen, tileColour, tiles_rendered[x][y])
    return tiles_rendered


def render_frame(game_state: GameState, tile_map, speed_boost_remaining, attack_boost_remaining) -> RenderedElements:
    screen.fill((50, 50, 50))
    tiles_rendered = render_map(game_state, tile_map)
    items_rendered = render_items(game_state, spawnedItems)
    render_enemies(game_state)
    pygame.draw.rect(screen, (0, 255, 0), game_state.player.rect)
    inventory_background = render_inventory(game_state)
    render_UI(game_state, speed_boost_remaining, attack_boost_remaining)
    return RenderedElements(items_rendered, tiles_rendered, inventory_background)


def game_frame(game_state: GameState) -> None:  # TODO: Split into multiple functions
    # Handles most of the gameplay.
    # The main game function where most other functions are called (other than menu functions)
    # Sets up the file if it is the first time running the file
    # loads everything in the first frame
    # manages player health, enemy health, enemy/player attacks, UI elements, starting pathfinding, etc.
    # Input:
    #   file - string, the file that is currently open
    global pathfindingThread, enemiesDefeated, difficulty, attackMultiplierEnemies, health_boost_num, timeSinceSpawnHealthBoosts, playerGridPosition, fileLine, timeSinceGun, enemyPreviousPosition, TriggerNotUp, spawnedItems, gameLost, timeSinceSword, playerHealth, timeSinceEnemyAttack, randomEnemyAttackTime, randomAttackTime, map, player, tileRect, running, mapGenerated, cells, givePaths, pathTicks, enemiesToMove, grid, inThread, ButtonNotUp, mouseNotUp
    render_data = render_frame(game_state, tile_map, timeRemainingSpeedBoost, timeRemainingAttackBoost)
    tileRect = render_data.tiles_rendered
    if gameLost:
        lostGame()
        return
    if enemiesDefeated:
        wonGame()
        return
    if CollectItem: collect_item(game_state, spawnedItems, render_data.items_rendered)
    if not pathfindingThread.is_alive():
        pathfindingThread = Thread(target=do_pathfinding, args=[game_state])
        pathfindingThread.start()
    if not render_data.inventory_background.collidepoint(pygame.mouse.get_pos()) and ((pygame.mouse.get_pressed()[
                                                                                           0] and mouseNotUp == False) or (
                                                                                              (joysticks and joysticks[
                                                                                                  0].get_axis(
                                                                                                  5) > 0.5) and TriggerNotUp == False)) and \
            game_state.player.inventory[itemSelected] is not None:

        if pygame.mouse.get_pressed()[0]:
            mouseNotUp = True
            attack(game_state, game_state.player)
        if joysticks and joysticks[0].get_axis(5) > 0.5:
            TriggerNotUp = True
            attack(game_state, game_state.player, True)

    for x in range(len(game_state.enemies)):

        if (isinstance(game_state.enemies[x], Knight) and
                abs(game_state.enemies[x].rect.x - game_state.player.rect.x) < 30 and
                abs(game_state.enemies[x].rect.y - game_state.player.rect.y) < 40):
            attack(game_state, game_state.enemies[x])

        distance = pygame.math.Vector2(abs(game_state.enemies[x].rect.x - game_state.player.rect.x),
                                       abs(game_state.enemies[x].rect.y - game_state.player.rect.y))
        if (distance.length() < 300 and
                (isinstance(game_state.enemies[x], Soldier) or
                 isinstance(game_state.enemies[x], Wizard))):
            attack(game_state, game_state.enemies[x])

        game_state.enemies[x].weapon.time_since_attack += 1

    for item in game_state.player.inventory:
        if isinstance(item, Weapon): item.time_since_attack += 1

    health_boost_num = sum(
        1 for item in spawnedItems
        if isinstance(item, Powerup) and item.type == PowerupType.HEALTH_BOOST
    )
    if health_boost_num < 10:
        if timeSinceSpawnHealthBoosts >= 600:
            spawnedItems.append(spawn_item(Powerup, True))
            timeSinceSpawnHealthBoosts = 0
    timeSinceSpawnHealthBoosts += 1

    if game_state.player.health <= 0:
        gameLost = True
    manageBullets(game_state)
    if not game_state.enemies:
        enemiesDefeated = True


def lostGame():
    # If the player has died, this function is called and displays this screen which creates a gray translucent background, and displays "GAME OVER!" and two buttons to respawn or go to the menu.
    lostGameRect = pygame.Rect(0, 0, screenWidth, screenHeight)
    draw_rect_alpha(screen, (50, 50, 50, 128), lostGameRect)
    lostGameText = font.render("GAME OVER!", True, (255, 0, 0))
    lostGameTextRect = lostGameText.get_rect(center=(screenWidth / 2, screenHeight / 6))
    screen.blit(lostGameText, lostGameTextRect)
    button('Respawn', (menuNameTextRect.centerx, menuNameTextRect.centery + 100), (150, 37.5), (100, 100, 100), respawn)
    button('Menu', (menuNameTextRect.centerx, menuNameTextRect.centery + 150), (150, 37.5), (100, 100, 100), toMenu)


def wonGame():
    # If the player has killed all enemies (and therefore won), this function is called and displays this screen which creates a gray translucent background, and displays "YOU WON!" and two buttons to play again or go to the menu.
    lostGameRect = pygame.Rect(0, 0, screenWidth, screenHeight)
    draw_rect_alpha(screen, (50, 50, 50, 128), lostGameRect)
    lostGameText = font.render("YOU WON!", True, (255, 0, 0))
    lostGameTextRect = lostGameText.get_rect(center=(screenWidth / 2, screenHeight / 6))
    screen.blit(lostGameText, lostGameTextRect)
    button('Play again', (menuNameTextRect.centerx, menuNameTextRect.centery + 100), (150, 37.5), (100, 100, 100),
           respawn)
    button('Menu', (menuNameTextRect.centerx, menuNameTextRect.centery + 150), (150, 37.5), (100, 100, 100), toMenu)


def respawn():
    global gameLost, firstTimeRun, mapGenerated
    gameLost = False
    mapGenerated = False
    loadFile(currentFile)


def toMenu():
    # takes the user back to the main menu. This function is called when the player presses the button to go to the menu on the game over screen.
    global mapGenerated, inGame, loadMenu, firstTimeRun
    menuEquals('main')
    mapGenerated = False
    inGame = False
    loadMenu = True


def draw_rect_alpha(surface: pygame.Surface, color: tuple[int, int, int, int], rect: pygame.Rect) -> None:
    # sourced from https://stackoverflow.com/questions/6339057/draw-a-transparent-rectangles-and-polygons-in-pygame
    # draws a translucent rectangle on the screen
    shape_surf = pygame.Surface(pygame.Rect(rect).size, pygame.SRCALPHA)
    pygame.draw.rect(shape_surf, color, shape_surf.get_rect())
    surface.blit(shape_surf, rect)


attackStrength = random.randint(6, 9)
attackMultiplier = 1


def attack(given_state: GameState, origin: Player | Enemy, controller: bool = False) -> None:
    # called when the player or an enemy uses a weapon. Checks to see who fired the weapon, which weapon was used and whether the player is close enough to use the weapon.
    # If all conditions are met, it then either lowers the enemy/player health (if it is a sword being used) or spawns a bullet/magic
    # Input:
    #   weaponType - string, determines which weapon is being used (sword, gun, wand)
    #   origin - integer (if it is an enemy) or pygame.Rect (if it is the player), determines who fired the weapon
    # Output:
    #   if it is a gun or wand being fired, it appends to the wandFired or bulletsFired array

    if isinstance(origin, Player):
        weapon = origin.inventory[itemSelected]
        if not isinstance(weapon, Weapon): raise RuntimeError("Player attempted to attack with powerup")
    else:
        weapon = origin.weapon

    if isinstance(weapon, Gun):
        if isinstance(origin, Player):

            if not controller:
                angle = math.atan2((pygame.mouse.get_pos()[1] - origin.rect.centery),
                                   (pygame.mouse.get_pos()[0] - origin.rect.centerx))
            else:
                angle = math.atan2(joysticks[0].get_axis(3), joysticks[0].get_axis(2))
            weapon.shoot(given_state, origin, get_grid_pos(origin.position, False), angle, attackMultiplier)
        else:
            weapon.shoot(given_state, origin, origin.position.copy(),
                         math.atan2((given_state.player.rect.centery - origin.rect.centery),
                                    (given_state.player.rect.centerx - origin.rect.centerx)), attackMultiplierEnemies)
    elif isinstance(weapon, Sword):
        if isinstance(origin, Player):
            for x in range(len(given_state.enemies)):
                if abs(given_state.enemies[x].rect.centerx - origin.rect.centerx) < 50 and abs(
                        given_state.enemies[x].rect.centery - origin.rect.centery) < 50:
                    weapon.attack(given_state.enemies[x], attackMultiplier)
        else:
            weapon.attack(given_state.player, attackMultiplierEnemies)
    elif isinstance(weapon, Wand):
        if isinstance(origin, Player):
            shortestDistance: tuple[int, float] = 0, 1000000.0
            if len(given_state.enemies) > 0:
                for x in range(len(given_state.enemies)):
                    distanceToX = pygame.math.Vector2(given_state.enemies[x].rect.centerx - origin.rect.centerx,
                                                      given_state.enemies[x].rect.centery - origin.rect.centery)
                    if distanceToX.length() < shortestDistance[1]:
                        shortestDistance = x, distanceToX.length()
                if shortestDistance[1] < 300:
                    weapon.fire(given_state, given_state.enemies[shortestDistance[0]],
                                get_grid_pos(origin.position, False), attackMultiplier)
        else:
            weapon.fire(given_state, given_state.player, origin.position, attackMultiplierEnemies)


def manageBullets(given_state: GameState) -> None:
    # is called every frame.
    # manages any current bullets; moves them, checks if they are colliding with an enemy/the player (if it is, it reduces the health of the player/enemy and removes the bullet), checks if it has been alive too long (if it is magic), checks if it has collided with any walls (if it is a bullet. if so, it removes it)
    global AttackMultiplier
    breakForLoop = False
    for magic in given_state.wand_magic_fired:
        if isinstance(magic.target, Player):
            target_grid_pos = get_grid_pos(magic.target.position, False)
            dx, dy = (target_grid_pos[0] - (magic.position[0]), target_grid_pos[1] - (magic.position[1]))
            stepx, stepy = (dx / 25, dy / 25)
            magic.position = [magic.position[0] + stepx, magic.position[1] + stepy]
            magic.rect = pygame.Rect(((tileWidth) * (magic.position[0])) + given_state.player.position[0],
                                     ((tileHeight) * (magic.position[1])) + given_state.player.position[1],
                                     magic.target.rect.width / 4,
                                     magic.target.rect.width / 4)
            pygame.draw.circle(screen, (100, 255, 255), magic.rect.center, magic.rect.width)
            magic.age += 1
            if magic.age >= 250:
                given_state.wand_magic_fired.remove(magic)
                continue
            if magic.rect.colliderect(magic.target.rect):
                if magic.target.health <= 1:
                    magic.target.health = 0
                else:
                    magic.target.health = int(
                        (magic.target.health * ((5 / 6) + ((1 / 20) * (1 / attackMultiplierEnemies)))) // 1)
                given_state.wand_magic_fired.remove(magic)
        elif isinstance(magic.target, Enemy):
            dx, dy = (magic.target.position[0] - (magic.position[0]), magic.target.position[1] - (magic.position[1]))
            stepx, stepy = (dx / 25, dy / 25)
            magic.position = [magic.position[0] + stepx, magic.position[1] + stepy]
            magic.rect = pygame.Rect(((tileWidth) * (magic.position[0])) + given_state.player.position[0],
                                     ((tileHeight) * (magic.position[1])) + given_state.player.position[1],
                                     magic.target.rect.width / 4,
                                     magic.target.rect.width / 4)
            pygame.draw.circle(screen, (100, 255, 255), magic.rect.center, magic.rect.width)
            if magic.rect.colliderect(magic.target.rect):
                if magic.target.health <= 1:
                    given_state.enemies.remove(magic.target)
                else:
                    if attackMultiplier == 2:
                        magic.target.health = int((magic.target.health * (2 / 4)) // 1)
                    else:
                        magic.target.health = int((magic.target.health * (3 / 4)) // 1)
                given_state.wand_magic_fired.remove(magic)
    for bullet in given_state.bullets_fired:
        bulletRect = pygame.Rect(((tileWidth) * (bullet.position[0])) + given_state.player.position[0],
                                 ((tileHeight) * (bullet.position[1])) + given_state.player.position[1],
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
                    enemy.health -= 15 * attackMultiplier
                given_state.bullets_fired.remove(bullet)
                breakForLoop = True
                break
            if breakForLoop:
                breakForLoop = False
                break
        else:
            if bulletSurfaceRect.colliderect(given_state.player.rect):
                given_state.player.health -= 1 * attackMultiplierEnemies
                break
        for y, tileRectRow in enumerate(tileRect):
            for z, tileRectRowColumn in enumerate(tileRectRow):
                if bulletSurfaceRect.colliderect(tileRect[y][z]) and (
                        tile_map[y][z] == GRID_COLOR or tile_map[y][z] == WALL_COLOR or tile_map[y][
                    z] == FLOOR_NEXT_COL):
                    given_state.bullets_fired.remove(bullet)
                    breakForLoop = True
                    break
            if breakForLoop:
                break
        if breakForLoop:
            breakForLoop = False
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


spawnedItems: list[Item] = []


def spawn_item(item_type: type[Item], health_boost: bool = False) -> Item:
    # called when the game is started. spawns a random item.
    # Inputs:
    #   type - string, determines whether it is a weapon or a powerup that is spawned.
    # Outputs:
    #   appends a weapon/powerup to the list of weapons/powerups spawned in a random location on the floor
    location = onGround[random.randint(0, len(onGround) - 1)]
    if item_type == Powerup:
        powerup_type = PowerupType.HEALTH_BOOST if health_boost else random.choice(list(PowerupType))
        item = powerups[powerup_type]
        return Powerup(location, item[0], item[1], powerup_type)
    else:
        weapon_type: type[Weapon] = random.choice(weapon_types)
        return weapon_type(location)


def collect_item(game_state: GameState, items: list[Item], items_rendered: dict[int, pygame.Rect]) -> None:
    global speed, attackMultiplier, timeRemainingSpeedBoost, timeRemainingAttackBoost
    for x, item in reversed(list(enumerate(items))):
        if not (abs(game_state.player.rect.x - items_rendered[x][0]) < 100 and abs(
                game_state.player.rect.y - items_rendered[x][1]) < 100):
            continue
        if isinstance(item, Weapon):
            for i in range(len(game_state.player.inventory)):
                if not game_state.player.inventory[i]:
                    game_state.player.inventory[i] = item
                    items.remove(item)
                    break
        if type(item) == Powerup and item.type == PowerupType.SPEED_BOOST:
            if speed != 400:
                continue
            speed = 300
            timeRemainingSpeedBoost = 1000
            items.remove(item)
            break
        if type(item) == Powerup and item.type == PowerupType.DAMAGE_BOOST:
            if attackMultiplier != 1:
                continue
            attackMultiplier = 2
            timeRemainingAttackBoost = 1000
            items.remove(item)
            break
        if type(item) == Powerup and item.type == PowerupType.HEALTH_BOOST:
            if game_state.player.health == 100:
                continue
            if game_state.player.health < 80:
                game_state.player.health += 20
            else:
                game_state.player.health = 100
            items.remove(item)
            break


def render_items(game_state: GameState, items: list[Item]) -> dict[int, pygame.Rect]:
    # Is called every frame. Shows the items on screen. If the player is close, it shows text saying the name of the item/powerup and tells the user to press E to pick up.
    # Input:
    #   items - array, the list of items to be rendered. It includes which item it is and where it is
    # Output:
    #   a bunch of pygame.Rects which are displayed on screen; the items.
    global speed, timeRemainingSpeedBoost, attackMultiplier, timeRemainingAttackBoost
    itemsRendered: dict[int, pygame.Rect] = {}
    width = screenWidth / 30
    height = screenHeight / 30
    for x, item in enumerate(items):
        current_item = pygame.Rect(((tileWidth) * (item.location[0])) + game_state.player.position[0],
                                   ((tileHeight) * (item.location[1])) + game_state.player.position[
                                       1] + tileHeight - height + 1, width, height)
        itemsRendered[x] = current_item
        if isinstance(item, Powerup):
            pygame.draw.rect(screen, items[x].colour, current_item)
            if item.type == PowerupType.HEALTH_BOOST:
                enemyNameText = font2.render("+", True, (255, 255, 255))
                enemyNameTextRect = enemyNameText.get_rect(center=(current_item.center[0], current_item.center[1]))
                screen.blit(enemyNameText, enemyNameTextRect)
        elif isinstance(item, Weapon):
            pygame.draw.rect(screen, item.colour, current_item)
        if abs(game_state.player.rect.x - current_item[0]) < 100 and abs(
                game_state.player.rect.y - current_item[1]) < 100:
            itemText = font2.render(item.name, True, (30, 30, 30))
            itemTextRect = itemText.get_rect(center=(current_item.center[0], current_item.center[1] - 20))
            itemText2 = font3.render("Press E to pick up", True, (30, 30, 30))
            itemTextRect2 = itemText2.get_rect(center=(current_item.center[0], current_item.center[1] - 35))
            screen.blit(itemText, itemTextRect)
            screen.blit(itemText2, itemTextRect2)
    return itemsRendered


def jump():
    # Is called when the player jumps
    # calculates the player movement up and down when jumping, as well as stopping the jump when landing by checking if the player is colliding with anything below.
    global player
    global jumpCount
    global playerPosition
    global jumping
    if jumpCount < 20:
        move = pygame.math.Vector2(0, -((screenWidth / 800) * (0.1 * jumpCount)) - gravity - (screenWidth / 800))
    else:
        move = pygame.math.Vector2(0, -(screenWidth / 600) - gravity - (screenWidth / 800))
    nextPlayer_y = game_state_global.player.rect.move(0, move.y)
    for x, tileRectRow in enumerate(tileRect):
        for y, tileRectRowColumn in enumerate(tileRectRow):
            if nextPlayer_y.colliderect(tileRect[x][y]) and (
                    tile_map[x][y] == GRID_COLOR or tile_map[x][y] == WALL_COLOR or tile_map[x][
                y] == FLOOR_NEXT_COL) and tileRect[x][y].top < nextPlayer_y.top:
                if move.y > 0:  # moving down
                    move.y = 0
                elif move.y < 0:  # moving up
                    move.y = 0
                break

    if game_state_global.player.position[1] <= -1776:
        if move.y > 0:
            move.y = 0
        game_state_global.player.position[1] = -1776

    if game_state_global.player.position[1] >= 315.2:
        if move.y < 0:
            move.y = 0
        game_state_global.player.position[1] = 315.2

    game_state_global.player.position[1] -= move.y
    jumpCount += 1


jumping = False


def new_weapon(location: pygame.Vector2, weapon_type: type[Weapon] | None = None) -> Weapon:
    if weapon_type is None: weapon_type = random.choice(weapon_types)
    return weapon_type(location)


def spawnEnemies(number: int) -> list[Enemy]:
    # called at the beginning of the game. spawns 40 enemies.
    # makes sure they are on the ground and not in a wall
    # Output:
    #   appends a random enemy and its location to game_state.enemies
    return_enemies: list[Enemy] = []
    for x in range(number):
        location = onGround[random.randint(0, len(onGround) - 1)]
        enemy_type = random.choice(enemy_types)
        return_enemies.append(enemy_type(100, location))
    return return_enemies


def render_enemies(given_state: GameState) -> None:
    for enemy in given_state.enemies:
        enemy.render(given_state)


itemSelected = 0


def render_inventory(game_state: GameState) -> pygame.Rect:
    # shows the inventory at the bottom of the screen. shows which item is currently selected, and checks to see if either inventory slot is clicked
    # If an inventory slot is clicked, if it is the currently selected slot, it drops the item in the slot, if not, it switches to that item
    # Output:
    #   some rects which are displayed and show the inventory and items
    global itemSelected, mouseNotUp, ButtonNotUp

    inventory_background = pygame.Rect((screenWidth / 2) - (50 * len(game_state.player.inventory)), screenHeight - 100,
                                       100 * len(game_state.player.inventory), 80)
    draw_rect_alpha(screen, (0, 0, 0, 128), inventory_background)

    rendered_inv = []
    rendered_inv_items: dict[int, pygame.Rect] = {}
    for n, item in enumerate(game_state.player.inventory):
        rendered_inv.append(
            pygame.Rect((screenWidth / 2) - (50 * len(game_state.player.inventory) - (100 * n)), screenHeight - 100,
                        100, 80))
        if n == itemSelected: draw_rect_alpha(screen, (200, 200, 200, 128), rendered_inv[n])
        if item:
            rendered_inv_items[n] = (
                pygame.Rect(screenWidth / 2 - (50 * len(game_state.player.inventory) - (100 * n)) + 35,
                            screenHeight - 60 - 12.5, 30, 25))
            pygame.draw.rect(screen, item.colour, rendered_inv_items[n])

    inventory_slot_pressed: list[bool] = [
        (pygame.mouse.get_pressed()[0] and rendered_inv[n].collidepoint(pygame.mouse.get_pos()) and mouseNotUp == False)
        for n in range(len(rendered_inv))
    ]

    controller_drop_pressed: bool = joysticks != [] and joysticks[0].get_button(1)

    # drop item
    current_item = game_state.player.inventory[itemSelected]
    current_item_pressed = inventory_slot_pressed[itemSelected]
    if (current_item_pressed or controller_drop_pressed) and current_item is not None:
        current_item.location = pygame.Vector2(get_grid_pos(game_state.player.position)[0],
                                               get_grid_pos(game_state.player.position)[1])
        spawnedItems.append(current_item)
        game_state.player.inventory[itemSelected] = None
        if pygame.mouse.get_pressed()[0]:
            mouseNotUp = True
        if joysticks and joysticks[0].get_button(1):
            ButtonNotUp = True

    # switch inventory slots
    for x in range(len(rendered_inv)):
        if inventory_slot_pressed[x]:
            itemSelected = x
            mouseNotUp = True

    controller_inv_button = [4, 5]
    if joysticks and joysticks[0].get_button(controller_inv_button[0]): itemSelected -= 1
    if joysticks and joysticks[0].get_button(controller_inv_button[1]): itemSelected += 1

    return inventory_background


def saveFile():
    # Saves the current file, called when exiting the game
    # Input:
    #   currentFile - string, the name of the file to be saved
    # Output:
    # writes the player location, the map details, and the fact that the file has been played to the file.
    global fileLine
    fileLine[2] = str(game_state_global.player.position[0]) + " " + str(game_state_global.player.position[1])
    fileLine[3] = ""
    for y in range(len(tile_map)):
        for x in range(len(tile_map[y])):
            if tile_map[y][x] == FLOOR_COLOR:
                tile_map[y][x] = "FLOOR_COLOR"
            elif tile_map[y][x] == FLOOR_NEXT_COL:
                tile_map[y][x] = "FLOOR_NEXT_COL"
            elif tile_map[y][x] == WALL_COLOR:
                tile_map[y][x] = "WALL_COLOR"
            elif tile_map[y][x] == GRID_COLOR:
                tile_map[y][x] = "GRID_COLOR"
    for y in range(len(tile_map)):
        mapTemp = tile_map[y]
        tile_map[y] = ""
        for x in range(len(mapTemp)):
            if x == len(mapTemp) - 1:
                tile_map[y] += mapTemp[x]
            else:
                tile_map[y] += mapTemp[x] + " "

    for x in range(len(tile_map)):
        if x == len(tile_map) - 1:
            fileLine[3] += tile_map[x]
        else:
            fileLine[3] += tile_map[x] + "  "
    for x in range(len(fileLine)):
        fileLine[x] = str(fileLine[x]) + "\n"
    with open("gamesaves/" + currentFile, 'w') as file:
        file.writelines(fileLine)


CollectItem = False

speed = 400
timeRemainingSpeedBoost = 0
timeRemainingAttackBoost = 0


def isOnGround():
    # Called at the beginning of the game. Determines which tiles are just above the ground.
    # used when spawning enemies and items, and in enemy pathfinding.
    # Output:
    #   onGround - array, list of tiles which are just above the ground
    global onGround, onGroundMap
    onGround = []
    for x in range(len(tile_map)):
        for y in range(len(tile_map[0])):
            if y == 64:
                if tile_map[x][y] == GRID_COLOR or tile_map[x][y] == WALL_COLOR or tile_map[x][y] == FLOOR_NEXT_COL:
                    pass
                else:
                    onGround.append([x, y])
            else:
                if tile_map[x][y + 1] == FLOOR_COLOR:
                    pass
                else:
                    if tile_map[x][y] == GRID_COLOR or tile_map[x][y] == WALL_COLOR or tile_map[x][y] == FLOOR_NEXT_COL:
                        pass
                    else:
                        onGround.append([x, y])
    onGroundMap = []
    for x in range(len(tile_map)):
        onGroundMap.append([])
        for y in range(len(tile_map)):
            if [y, x] in onGround:
                onGroundMap[x].append(1)
            else:
                onGroundMap[x].append(0)


clock = pygame.time.Clock()

while True:
    pygame.display.update()

    for event in pygame.event.get():
        if event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0:
                if jumping == False:
                    jumping = True
                    jumpCount = 0
            if event.button == 7:
                saveFile()
                pygame.quit()
                sys.exit()
            if event.button == 2:
                CollectItem = True
        if event.type == pygame.JOYBUTTONUP:
            if event.button == 0:
                if jumping == True:
                    jumping = False
                    jumpCount = 0
            ButtonNotUp = False
        if event.type == QUIT:
            if inGame:
                saveFile()
            pygame.quit()
            sys.exit()
        if event.type == pygame.MOUSEBUTTONUP:
            mouseNotUp = False
        if event.type == pygame.KEYDOWN:
            if menu == 'new':
                if event.key == pygame.K_BACKSPACE:
                    typedText = typedText[:-1]
                else:
                    typedText += event.unicode
            if inGame:
                if event.key == pygame.K_ESCAPE:
                    saveFile()
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_SPACE:
                    if jumping == False:
                        jumping = True
                        jumpCount = 0

                if event.key == pygame.K_h:
                    player.position = [screenWidth, 0]
                if event.key == pygame.K_e:
                    CollectItem = True
            # if event.key == pygame.K_F11: # - disabled due to issues with collision and player position.
            #     toggleFullscreen()
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                if jumping == True:
                    jumping = False
                    jumpCount = 0

        if event.type == pygame.MOUSEWHEEL:
            if menu == 'play' and loadMenu == True and menuNameTextRect.centery + (
                    50 + ((len(buttonsList) - 1) * 50)) > screenHeight:
                ButtonsListOffset += event.y * 10
                if ButtonsListOffset > 0:
                    ButtonsListOffset = 0
                if menuNameTextRect.centery + ButtonsListOffset + (
                        50 + ((len(buttonsList) - 1) * 50)) + 30 < screenHeight:
                    ButtonsListOffset -= event.y * 10
    screen.fill((20, 20, 20))

    if loadMenu:
        mainMenu(menu)

    if (joysticks and joysticks[0].get_axis(5) < 0.5):
        TriggerNotUp = False
    if joysticks and joysticks[0].get_axis(4) < 0.5:
        ButtonNotUp = False
    keys = pygame.key.get_pressed()

    if inGame:
        game_frame(game_state_global)

        key = pygame.key.get_pressed()

        left = 0
        right = 0

        for x in range(len(joysticks)):
            if joysticks[x].get_axis(0) > 0.25:
                right = (abs(joysticks[x].get_axis(0)) - 0.25) * (4 / 3)
            if joysticks[x].get_axis(0) < -0.5:
                left = (abs(joysticks[x].get_axis(0)) - 0.25) * (4 / 3)

        left += key[pygame.K_a] or key[pygame.K_LEFT]
        if left > 1:
            left = 1
        right += key[pygame.K_d] or key[pygame.K_RIGHT]
        if right > 1:
            right = 1

        if joysticks and joysticks[0].get_axis(4) > 0.5:
            if jumping == False:
                jumping = True
                jumpCount = 0
        elif (joysticks and joysticks[0].get_axis(4) < 0.5) and not joysticks[0].get_button(0) and not key[
            pygame.K_SPACE]:
            if jumping == True:
                jumping = False
                jumpCount = 0

        if not gameLost:
            if jumping:
                jump()

            move = pygame.math.Vector2(right - left, 0)
            if not jumping:
                move.y -= gravity
            if move.length_squared() > 0:
                move.scale_to_length(screenWidth / speed)

                nextPlayer_x = game_state_global.player.rect.move(move.x, 0)
                for x, tileRectRow in enumerate(tileRect):
                    for y, tileRectRowColumn in enumerate(tileRectRow):
                        if nextPlayer_x.colliderect(tileRect[x][y]) and (
                                tile_map[x][y] == GRID_COLOR or tile_map[x][y] == WALL_COLOR or tile_map[x][
                            y] == FLOOR_NEXT_COL):
                            if move.x > 0:  # moving right
                                move.x = 0
                            elif move.x < 0:  # moving left
                                move.x = 0
                            break

                nextPlayer_y = game_state_global.player.rect.move(0, move.y)
                for x, tileRectRow in enumerate(tileRect):
                    for y, tileRectRowColumn in enumerate(tileRectRow):
                        if nextPlayer_y.colliderect(tileRect[x][y]) and (
                                tile_map[x][y] == GRID_COLOR or tile_map[x][y] == WALL_COLOR or tile_map[x][
                            y] == FLOOR_NEXT_COL):
                            if move.y > 0:  # moving down
                                move.y = 0
                            elif move.y < 0:  # moving up
                                move.y = 0
                            break

                if game_state_global.player.position[0] <= -3268.8:
                    if move.x > 0:
                        move.x = 0
                    game_state_global.player.position[0] = -3268.8
                if game_state_global.player.position[0] >= 561:
                    if move.x < 0:
                        move.x = 0
                    game_state_global.player.position[0] = 561
                if game_state_global.player.position[1] <= -1776:
                    if move.y > 0:
                        move.y = 0
                    game_state_global.player.position[1] = -1776
                if game_state_global.player.position[1] >= 315.2:
                    if move.y < 0:
                        move.y = 0
                    game_state_global.player.position[1] = 315.2

                game_state_global.player.position[0] -= move.x
                game_state_global.player.position[1] -= move.y
                fileLine[2] = game_state_global.player.position

            if timeRemainingSpeedBoost > 0:
                if timeRemainingSpeedBoost == 1:
                    speed = 400
                timeRemainingSpeedBoost -= 1
            if timeRemainingAttackBoost > 0:
                if timeRemainingAttackBoost == 1:
                    attackMultiplier = 1
                timeRemainingAttackBoost -= 1

    if CollectItem:
        CollectItem = False

    clock.tick(60)

# FIXME: Player sometimes goes one pixel into the wall. No clue what causes it, it appears to be random. Player cannot move in other axis until moving away from the wall.
# FIXME: things can spawn in areas inaccessible to the player. this could just be an item or powerup that then cant be used, but it could also be an enemy, in which case the game can only be won with the wand.
# FIXME: soldiers and wizards go 1 too far left and 2 too far right, which can cause many issues.

# Todo: Save enemies, inventory, powerups, items, and health. (Is this needed?)
# Todo: Optimise pathfinding (V2?)

# Considerations for V2:
# Add random player spawning
# Make movement more smooth
# Add doors
# Add levels
# Better pathfinding and enemy movement
# Adjust sizing of assets
# Add sprites/assets
# Add more items
# Enemy idle movement
# Add difficulty settings
