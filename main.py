import sys
import pygame
from pygame.locals import QUIT
import numpy as np
import time
import os
import random
import pathfinding
from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder
from threading import Thread
import multiprocessing

pygame.init()

screen = pygame.display.set_mode((1152, 648))
pygame.display.set_caption('NEA')
font = pygame.font.Font(None, 32)
font2 = pygame.font.Font(None, 24)
font3 = pygame.font.Font(None, 12)
isFullscreen = False
displayAudioError = False
audioMessagePressed = False
try:
    pygame.mixer.init()
except:
    displayAudioError = True
    audioMessagePressed = False

loadMenu = True
menu = 'main'
ButtonsListOffset = 0
volume = 100
mouseNotUp = False
WALL_COLOR = (50, 50, 50)
GRID_COLOR = (0, 0, 0)
FLOOR_COLOR = (255, 255, 255)
FLOOR_NEXT_COL = (0, 0, 255)
gravity = -1.5
screenWidth = screen.get_width()
screenHeight = screen.get_height()
tileWidth = screenWidth/20
tileHeight = screenHeight/20
PresetMaps = [
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

powerups = [['Increased speed', (0,0,200)],
            ['Damage x2', (0,200,200)]

]

weapons = [['Gun', (0,200,0)],
           ['Sword', (200,200,0)],
           ['Wand', (100, 255, 255)]

]

enemies = [['Knight', (200,75,0)],
           ['Wizard', (200,0,75)],
           ['Soldier', (0,0,100)]

]

playerInventory = [[],[]]

inGame = False

def button(text, position, size, colour, action=None, *args): # draws a button on screen with optional function
    global mouseNotUp
    button_rect = pygame.Rect(position[0] - (size[0] / 2), position[1] - (size[1] / 2), size[0], size[1])
    pygame.draw.rect(screen, colour, button_rect)
    text = font.render(text, True, (0, 0, 0))
    textRect = text.get_rect(center=button_rect.center)
    screen.blit(text, textRect)
    if button_rect.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[
        0] and mouseNotUp == False and action != None:
        action(*args)
        mouseNotUp = True


def menuEquals(menu_set): # changes the menu to menu_set
    global menu
    global difficulty
    global typedText
    global ButtonsListOffset
    menu = menu_set
    if menu == 'new':
        difficulty = 'Easy'
        typedText = ''
    if menu == 'play':
        if os.path.isdir('gamesaves'):
            global gameSaves
            gameSaves = os.listdir('gamesaves')
            print(gameSaves)
        else:
            os.mkdir('gamesaves')
    ButtonsListOffset = 0


def changeVolume(): # changes the volume
    global volume
    volume += 10
    if volume > 100:
        volume = 0
    pygame.mixer.music.set_volume(volume / 100)


def toggleFullscreen(): # toggles fullscreen, currently unused.
    global isFullscreen
    global player
    if not isFullscreen:
        pygame.display.set_mode((pygame.display.list_modes()[0][0], pygame.display.list_modes()[0][1]))
        pygame.display.toggle_fullscreen()
        isFullscreen = True
    else:
        pygame.display.toggle_fullscreen()
        pygame.display.set_mode((1152, 648), pygame.RESIZABLE)
        isFullscreen = False
    if inGame and 'player' in globals():
        player = pygame.Rect(screenWidth / 2 - (screenWidth / 2) / 40,
                             screenHeight / 2 - (screenHeight / 2) / 40, (screenWidth / 2) / 20,
                             (screenHeight / 2) / 20)


def drawTextBox(text, position, size, colour, borderColour, borderSize, typedText): # draws a text box
    if typedText == '':
        text = font.render(text, True, (0, 0, 0))
        textRect = text.get_rect(center=position)
    if typedText != '':
        text = font.render(typedText, True, (0, 0, 0))
        textRect = text.get_rect(center=position)
    pygame.draw.rect(screen, colour, textRect)
    pygame.draw.rect(screen, borderColour, (
    textRect.x - borderSize, textRect.y - borderSize, textRect.width + borderSize * 2,
    textRect.height + borderSize * 2), borderSize)
    screen.blit(text, textRect)


def setDifficulty(): # changes the difficulty in the create file menu
    global difficulty
    difficulties = {
        'Easy': 'Medium',
        'Medium': 'Difficult',
        'Difficult': 'Very difficult',
        'Very difficult': 'Easy'
    }
    difficulty = difficulties.get(difficulty, 'Easy')


def createFile(): # creates a game file
    global fileName
    global difficulty
    global gameSaves
    file = open(f'gamesaves/{typedText}.txt', 'w')
    file.write(f'Difficulty{difficulty}\n')
    file.write(f'firstplaythroughTrue\n')
    for x in range(2):
        file.write(f'None\n')
    global gameSaves
    gameSaves = os.listdir('gamesaves')
    print(gameSaves)
    loadFile(f'{typedText}.txt')


def loadFile(file): # loads the chosen game file
    global inGame, loadMenu, currentFile, firstTimeRun, map, playerPosition, fileLine
    print(f'load {file}')
    inGame = True
    loadMenu = False
    currentFile = file
    firstTimeRun = True
    with open(f"gamesaves/{file}", "r") as f:
        fileLine = [line.strip() for line in f]
        print(fileLine)
    if fileLine[1] == "firstplaythroughFalse":
        playerPosition = [float(fileLine[2].split(" ")[0]), float(fileLine[2].split(" ")[1])]
        map = []
        mapTemp = fileLine[3].split("  ")
        print(len(mapTemp))
        for x in range(len(mapTemp)):
            map.append(mapTemp[x].split(" "))
        for y in range(len(map)):
            for x in range(len(map[y])):
                if map[y][x] == "FLOOR_COLOR":
                    map[y][x] = FLOOR_COLOR
                elif map[y][x] == "FLOOR_NEXT_COL":
                    map[y][x] = FLOOR_NEXT_COL
                elif map[y][x] == "WALL_COLOR":
                    map[y][x] = WALL_COLOR
                elif map[y][x] == "GRID_COLOR":
                    map[y][x] = GRID_COLOR


def mainMenu(menu): # Shows and handles almost everything related to the main menu, menu parameter controls which menu is currently showing
    global menuNameTextRect
    global volume
    global buttonsList
    if menu == 'main' or menu == 'play':
        menuNameText = font.render("Game Name", True, (255, 255, 255))
    elif menu == 'settings':
        menuNameText = font.render("Settings", True, (255, 255, 255))
    elif menu == 'new':
        menuNameText = font.render("New Game", True, (255, 255, 255))
    menuNameTextRect = menuNameText.get_rect(center=(screenWidth / 2, screenHeight / 6))
    if menu == 'main':
        buttonsList = [['Play', menuEquals, 'play'], ['Settings', menuEquals, 'settings'], ['Quit', pygame.quit]]
    elif menu == 'settings':
        if not displayAudioError:
            buttonsList = [[f'Volume: {volume}%', changeVolume]]
        else:
            buttonsList = []
    elif menu == 'play':
        buttonsList = [['New Game', menuEquals, 'new']]
        for savefile in gameSaves:
            buttonsList.append([savefile[:len(savefile) - 4], loadFile, savefile])
        if len(buttonsList) < 4:
            button('Back', (menuNameTextRect.centerx, menuNameTextRect.centery + 200), (150, 37.5), (100, 100, 100),
                   menuEquals, 'main')
        else:
            buttonsList.append(['Back', menuEquals, 'main'])
    elif menu == 'new':
        drawTextBox(f'Enter a name for your new game', (menuNameTextRect.centerx, menuNameTextRect.centery + 50),
                    (150, 37.5), (100, 100, 100), (0, 0, 0), 2, typedText)
        buttonsList = [None, [f'Difficulty: {difficulty}', setDifficulty], ['Start', createFile],
                       ['Back', menuEquals, 'play']]
    if menu != "main" and menu != 'play' and menu != 'new':
        button('Back', (menuNameTextRect.centerx, menuNameTextRect.centery + 200), (150, 37.5), (100, 100, 100),
               menuEquals, 'main')
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

mapGenerated = False

inThread = False
def pathfinding():
    global enemiesToMove, grid, spawnedEnemies, playerGridPosition, pathGrid, pathTicks, inThread, onGroundMap
    inThread = True
    # print(playerGridPosition)
    if pathTicks == 0:
        enemiesToMove = []
        grid = Grid(matrix=onGroundMap)
        for x in range(len(spawnedEnemies)):
            if abs(playerGridPosition[0] - int(spawnedEnemies[x][2][0]//1)) <= 21 and abs(playerGridPosition[1] - int(spawnedEnemies[x][2][1]//1)) <= 21:
                start = grid.node(int(spawnedEnemies[x][2][0]//1), int(spawnedEnemies[x][2][1]//1))
                end = grid.node(playerGridPosition[0], playerGridPosition[1])
                finder = AStarFinder(diagonal_movement=DiagonalMovement.never)
                path, runs = finder.find_path(start, end, grid)
                pathGrid = grid.grid_str(path=path, start=start, end=end).split('\n')
                if spawnedEnemies[x][0] == 'Soldier' or spawnedEnemies[x][0] == 'Wizard':
                    for l in range(len(pathGrid)):
                        if 'se' in pathGrid[l] and not '#se' in pathGrid[l]:
                            n = int(playerGridPosition[0]//1) - 2
                            enemiesToMove.append([x, (n, l)])
                        elif 'es' in pathGrid[l] and not 'es#' in pathGrid[l]:
                            n = int(playerGridPosition[0]//1) + 2
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
                                n = int(playerGridPosition[0] // 1) - 1
                            elif eLocation < sLocation:
                                n = int(playerGridPosition[0] // 1) + 1
                            enemiesToMove.append([x, (n, l)])
                else:
                    for l in range(len(pathGrid)):
                        if 'x' in pathGrid[l] or 'se' in pathGrid[l] or 'es' in pathGrid[l]:
                            for i in reversed(range(len(pathGrid[l]))):
                                if pathGrid[l][i] == 'x' or (pathGrid[l][i] == 'e' and (pathGrid[l][i-1] == 's' or pathGrid[l][i+1] == 's')):
                                    n = playerGridPosition[0]
                            enemiesToMove.append([x, (n, l)])
        pathTicks = 50
    # print(enemiesToMove)
    if enemiesToMove != []:
        for x in range(len(enemiesToMove)):
            if spawnedEnemies[enemiesToMove[x][0]][2] != enemiesToMove[x][1]:
                if spawnedEnemies[enemiesToMove[x][0]][2][0]//1 > enemiesToMove[x][1][0]//1:
                    spawnedEnemies[enemiesToMove[x][0]][2][0] -= 0.05
                if spawnedEnemies[enemiesToMove[x][0]][2][0]//1 < enemiesToMove[x][1][0]//1:
                    spawnedEnemies[enemiesToMove[x][0]][2][0] += 0.05
    pathTicks -= 1
    inThread = False


def playGame(file): # Handles most of the gameplay TODO: Split into multiple functions
    global playerPosition, playerGridPosition, fileLine, firstTimeRun, spawnedItems, gameLost, spawnedEnemies, timeSinceSword, timeSinceWand, playerHealth, timeSinceEnemyAttack, randomEnemyAttackTime, randomAttackTime, map, player, tileRect, tile, running, mapGenerated, cells, size, givePaths, pathTicks, enemiesToMove, grid, inThread, mouseNotUp
    if firstTimeRun == True:
        with open(f"gamesaves/{file}", "r") as f:
            fileLine = [line.strip() for line in f]
        firstTimeRun = False
        player = pygame.Rect(screenWidth / 2 - (screenWidth / 2) / 40,
                             screenHeight / 2 - (screenHeight / 2) / 40, (screenWidth / 2) / 20,
                             (screenHeight / 2) / 20)
        enemiesDefeated = False
        gameLost = False
        pathTicks = 0
        size = 10
        spawnedEnemies = []
        spawnedItems = []
        enemiesToMove = []
        if fileLine[1] == "firstplaythroughTrue":
            playerPosition = [90, -10]
            fileLine[2] = playerPosition
            map = []
            # Set dimension of cells and their initial configuration
            cells = np.random.choice(2, size=(60, 80), p=[0.38, 0.62])
            cells[0:60, 0] = 1
            cells[0, 0:80] = 1
            cells[0:60, 79] = 1
            cells[59, 0:80] = 1
            if not mapGenerated:
                map = []
                randomMaps = []

                for y in range(5):
                    randomMaps.append([])
                    for x in range(5):
                        randomMaps[y].append(random.randint(0, len(PresetMaps)-1))

                for LevelY in range(5):
                    for y in range(len(PresetMaps[0][0])):
                        map.append([])
                        for LevelX in range(5):
                            for x in range(len(PresetMaps[0])):
                                if PresetMaps[randomMaps[LevelY][LevelX]][x][y] == "-":
                                    map[LevelY * len(PresetMaps[0]) + y].append(WALL_COLOR)
                                elif PresetMaps[randomMaps[LevelY][LevelX]][x][y] == " ":
                                    map[LevelY * len(PresetMaps[0]) + y].append(FLOOR_COLOR)
                        if map[-1] == []:
                            map.pop()
                mapGenerated = True
            fileLine[1] = 'firstPlaythroughFalse'
        isOnGround()
        playerGridPosition = [int((((screenWidth/2) - playerPosition[0])/tileWidth)//1), int((((screenHeight/2) - playerPosition[1])/ tileHeight)//1)]
        for x in range(20):
            spawnItem("powerup")
            spawnItem("weapon")
        spawnEnemies()
        timeSinceEnemyAttack = []
        for x in range(len(spawnedEnemies)):
            timeSinceEnemyAttack.append(0)
            timeSinceWand.append(0)
        playerHealth = 100
        randomEnemyAttackTime = 50


    #    running = 34
    # if mapGenerated:
        # if running > 0:
        #     map = []
        #     cells = update(screen, cells, size, with_progress=True)
        #     running -= 1
    # backgroundImage = pygame.image.load('Seasonal Tilesets/1 - Grassland/Background parts/_Complete_static_BG_(288 x ''208).png')
    # backgroundImage = pygame.transform.scale(backgroundImage, (screenWidth, screenHeight))
    # screen.blit(backgroundImage, (0, 0))
    # print("map len " + str(len(map)) + " " + str(len(map[0])))
    screen.fill((50, 50, 50))
    tileRect = []
    tile = []
    for x, colour in enumerate(map, start=0):
        tileRect.append([])
        tile.append([])
        for y, tileColour in enumerate(colour, start=0):
            tileRect[x].append(pygame.Rect(((tileWidth) * (x)) + playerPosition[0],
                                           ((tileHeight) * (y)) + playerPosition[1],
                                           tileWidth + 1, tileHeight + 1))
            tile[x].append([pygame.draw.rect(screen, tileColour, tileRect[x][y]), (255, 0, 0)])
    renderItem(spawnedItems, len(spawnedItems))
    renderEnemies()
    pygame.draw.rect(screen, (0, 255, 0), player)
    renderInventory()
    playerGridPosition = [int((((screenWidth/2) - playerPosition[0])/ tileWidth)//1), int(((screenHeight/2 - playerPosition[1])/ tileHeight)//1)]
    if not gameLost:
        try:
            if not pathfindingThread.is_alive():
                pathfindingThread = Thread(target=pathfinding)
                pathfindingThread.start()
        except:
            pathfindingThread = Thread(target=pathfinding)
            pathfindingThread.start()
        if not inventoryBackground.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[
            0] and mouseNotUp == False and ((itemSelected == 1 and playerInventory[0] != []) or (itemSelected == 2 and playerInventory[1] != [])):
            Attack(playerInventory[itemSelected - 1][0], player)
            mouseNotUp = True
        print("spawned enemies ", len(spawnedEnemies))
        timeSinceSword += 1
        for x in range(len(timeSinceWand)):
            timeSinceWand[x] += 1
        for x in range(len(spawnedEnemies)):
            if abs(enemiesRendered[x].x - player.x) < 30 and abs(enemiesRendered[x].y - player.y) < 40 and timeSinceEnemyAttack[x] > randomEnemyAttackTime:
                if spawnedEnemies[x][0] == 'Knight':
                    timeSinceEnemyAttack[x] = 0
                    playerHealth -= random.randint(2, 5)
                    criticalHit = random.randint(0, 100)
                    if criticalHit == 99:
                        playerHealth -= 5
                        print("Critical Hit!")
            distance = pygame.math.Vector2(abs(enemiesRendered[x].x - player.x), abs(enemiesRendered[x].y - player.y))
            if distance.length() < 300 and timeSinceWand[x+1] > randomEnemyAttackTime:
                if spawnedEnemies[x][0] == 'Wizard':
                    Attack(2, x)
                    timeSinceWand[x + 1] = 0

                randomEmemyAttackTime = random.randint(60, 85)
        for x in range(len(timeSinceEnemyAttack)):
            timeSinceEnemyAttack[x] += 1
    if playerHealth < 0:
        print("you died!")
        gameLost = True
    if gameLost:
        lostGame()
    print(playerHealth)
    manageBullets()
    if not spawnedEnemies:
        enemiesDefeated = True


def lostGame():
    lostGameRect = pygame.Rect(0, 0, screenWidth, screenHeight)
    draw_rect_alpha(screen, (50,50,50, 128), lostGameRect)
    lostGameText = font.render("GAME OVER!", True, (255, 0, 0))
    lostGameTextRect = lostGameText.get_rect(center=(screenWidth / 2, screenHeight / 6))
    button('Respawn',(menuNameTextRect.centerx, menuNameTextRect.centery + 100),(150, 37.5), (100, 100, 100), respawn)
    button('Menu', (menuNameTextRect.centerx, menuNameTextRect.centery + 150), (150, 37.5), (100, 100, 100), toMenu)

def respawn():
    gameLost = False

def toMenu():
    global mapGenerated, inGame, loadMenu
    menuEquals('main')
    mapGenerated = False
    inGame = False
    loadMenu = True

def draw_rect_alpha(surface, color, rect): # sourced from https://stackoverflow.com/questions/6339057/draw-a-transparent-rectangles-and-polygons-in-pygame
    shape_surf = pygame.Surface(pygame.Rect(rect).size, pygame.SRCALPHA)
    pygame.draw.rect(shape_surf, color, shape_surf.get_rect())
    surface.blit(shape_surf, rect)

attackStrength = random.randint(6, 9)
attackMultiplier = 1
bulletsFired = []
wandFired = []
timeSinceSword = 30
randomAttackTime = 30
timeSinceWand = [0]
randomWandAttackTime = 120
def Attack(weaponType, origin):
    global timeSinceSword, randomAttackTime, timeSinceWand, randomWandAttackTime
    if weaponType == 0:
        if origin == player:
            bulletsFired.append([playerGridPosition, pygame.Rect(player.x + (player.width/2), player.y + player.height - (player.height * (1/3)), player.width * (4/5), player.height * (1/3))])
        else:
            bulletsFired.append([playerGridPosition, pygame.Rect(origin.x + (origin.width / 2),origin.y + origin.height - (player.height * (1 / 3)),player.width * (4 / 5), player.height * (1 / 3))])
    elif weaponType == 1:
        for x in range(len(spawnedEnemies)):
            if abs(enemiesRendered[x].x - player.x) < 30 and abs(enemiesRendered[x].y - player.y) < 40 and timeSinceSword > randomAttackTime:
                spawnedEnemies[x][3] -= attackStrength * attackMultiplier
                if spawnedEnemies[x][3] <= 0:
                    spawnedEnemies.pop(x)
                timeSinceSword = 0
                randomAttackTime = random.randint(25, 40)
    elif weaponType == 2:
        if origin == player:
            if timeSinceWand[0] > randomWandAttackTime:
                for x in range(len(spawnedEnemies)):
                    if x == 0:
                        shortestDistance = x, pygame.math.Vector2(abs(enemiesRendered[x].x - player.x), abs(enemiesRendered[x].y - player.y))
                    distanceToX = pygame.math.Vector2(abs(enemiesRendered[x].x - player.x), abs(enemiesRendered[x].y - player.y))
                    print(distanceToX)
                    if distanceToX.length() < shortestDistance[1].length():
                        shortestDistance = x, pygame.math.Vector2(abs(enemiesRendered[x].x - player.x), abs(enemiesRendered[x].y - player.y))
                if shortestDistance[1].length() < 300:
                    wandFired.append([playerGridPosition, shortestDistance, pygame.Rect(player.x + (player.width/2), player.y - (player.height/2), player.width/4, player.width/4)])
                    timeSinceWand[0] = 0
                    randomWandAttackTime = random.randint(100, 140)
        else:
            if timeSinceWand[origin+1] > randomWandAttackTime:
                print("We are getting this far")
                distance = player, pygame.math.Vector2(abs(player.x - enemiesRendered[origin].x), abs(player.y - enemiesRendered[origin].y))
                wandFired.append([spawnedEnemies[origin][2], distance, pygame.Rect(enemiesRendered[origin].x + (player.width/2), enemiesRendered[origin].y - (player.height/2), player.width/4, player.width/4)])
                timeSinceWand[origin+1] = 0





def win():
    i
def manageBullets():
    global playerHealth
    if wandFired:
        for x in range(len(wandFired)):
            if wandFired[x][1][0] == player:
                dx, dy = (playerPosition[0] - (wandFired[x][0][0]),playerPosition[1] - (wandFired[x][0][1]))
                stepx, stepy = (dx / 25, dy / 25)
                wandFired[x][0] = [wandFired[x][0][0] + stepx, wandFired[x][0][1] + stepy]
                wandFired[x][2] = pygame.Rect(((tileWidth) * (wandFired[x][0][0])) + playerPosition[0] + 20, ((tileHeight) * (wandFired[x][0][1])) + playerPosition[1] + 20, player.width / 4, player.width / 4)
                pygame.draw.circle(screen, (100, 255, 255), wandFired[x][2].center, wandFired[x][2].width)
                if wandFired[x][2].colliderect(player):
                    if playerHealth <= 1:
                        pass
                    else:
                        playerHealth = int((playerHealth * (3/4))//1)
                    wandFired.pop(x)
            else:
                dx, dy = (spawnedEnemies[wandFired[x][1][0]][2][0] - (wandFired[x][0][0]), spawnedEnemies[wandFired[x][1][0]][2][1] - (wandFired[x][0][1]))
                stepx, stepy = (dx / 25, dy / 25)
                wandFired[x][0] = [wandFired[x][0][0] + stepx, wandFired[x][0][1] + stepy]
                wandFired[x][2] = pygame.Rect(((tileWidth) * (wandFired[x][0][0])) + playerPosition[0] + 20,((tileHeight) * (wandFired[x][0][1])) + playerPosition[1] + 20, player.width/4, player.width/4)
                pygame.draw.circle(screen, (100, 255, 255), wandFired[x][2].center, wandFired[x][2].width)
                if wandFired[x][2].colliderect(enemiesRendered[wandFired[x][1][0]]):
                    if spawnedEnemies[wandFired[x][1][0]][3] <= 1:
                        pass
                    else:
                        spawnedEnemies[wandFired[x][1][0]][3] = int((spawnedEnemies[wandFired[x][1][0]][3] * (3/4))//1)
                    wandFired.pop(x)

spawnedItems = []
def spawnItem(type):
    global spawnedItems
    location = (random.randint(0,66),random.randint(0,64))
    isDone = False
    while isDone == False:
        if location[1] == 64:
            if map[location[0]][location[1]] == GRID_COLOR or map[location[0]][location[1]] == WALL_COLOR or map[location[0]][location[1]] == FLOOR_NEXT_COL:
                location = (random.randint(0, 66), random.randint(0, 64))
            else:
                isDone = True
        else:
            if map[location[0]][location[1]+1] == FLOOR_COLOR:
                location = (random.randint(0, 66), random.randint(0, 64))
            else:
                if map[location[0]][location[1]] == GRID_COLOR or map[location[0]][location[1]] == WALL_COLOR or map[location[0]][location[1]] == FLOOR_NEXT_COL:
                    location = (random.randint(0, 66), random.randint(0, 64))
                else:
                    isDone = True
    if type == "powerup":
        spawnedItems.append([random.randint(0, len(powerups)-1), type, location])
    elif type == "weapon":
        spawnedItems.append([random.randint(0, len(weapons)-1), type, location])

def renderItem(spawnedItems, amount):
    global speed, timeRemainingSpeedBoost, attackMultiplier, timeRemainingAttackBoost
    itemsRendered = []
    width = screenWidth / 30
    height = screenHeight / 30
    for x in range(amount):
        itemsRendered.append(pygame.Rect(((tileWidth) * (spawnedItems[x][2][0])) + playerPosition[0],((tileHeight) * (spawnedItems[x][2][1])) + playerPosition[1] + tileHeight - height +1,width,height))
        if spawnedItems[x][1] == "powerup":
            pygame.draw.rect(screen,powerups[spawnedItems[x][0]][1],itemsRendered[-1])
        elif spawnedItems[x][1] == "weapon":
            pygame.draw.rect(screen, weapons[spawnedItems[x][0]][1], itemsRendered[-1])
        if abs(player.x - itemsRendered[-1][0]) < 100 and abs(player.y - itemsRendered[-1][1]) < 100:
            if spawnedItems[x][1] == "powerup":
                itemText = font2.render(powerups[spawnedItems[x][0]][0], True, (30,30,30))
                itemTextRect = itemText.get_rect(center=(itemsRendered[-1].center[0],itemsRendered[-1].center[1] - 20))
                itemText2 = font3.render("Press E to pick up", True, (30,30,30))
                itemTextRect2 = itemText2.get_rect(center=(itemsRendered[-1].center[0],itemsRendered[-1].center[1] - 35))
                screen.blit(itemText, itemTextRect)
                screen.blit(itemText2, itemTextRect2)
            if spawnedItems[x][1] == "weapon":
                itemText = font2.render(weapons[spawnedItems[x][0]][0], True, (30,30,30))
                itemTextRect = itemText.get_rect(center=(itemsRendered[-1].center[0],itemsRendered[-1].center[1] - 20))
                itemText2 = font3.render("Press E to pick up", True, (30,30,30))
                itemTextRect2 = itemText2.get_rect(center=(itemsRendered[-1].center[0],itemsRendered[-1].center[1] - 35))
                screen.blit(itemText, itemTextRect)
                screen.blit(itemText2, itemTextRect2)
            if CollectItem:
                print(f"Pop {spawnedItems[x]}")
                if spawnedItems[x][1] == "weapon":
                    if playerInventory[0] == []:
                        playerInventory[0] = spawnedItems[x]
                        spawnedItems.pop(x)
                        break
                    elif playerInventory[1] == []:
                        playerInventory[1] = spawnedItems[x]
                        spawnedItems.pop(x)
                        break
                    else:
                        print("inventory full")
                if spawnedItems[x][1] == "powerup" and spawnedItems[x][0] == 0:
                    if speed == 400:
                        speed = 300
                        timeRemainingSpeedBoost = 1000
                        spawnedItems.pop(x)
                        break
                    else:
                        print("Speed Boost already applied.")
                if spawnedItems[x][1] == "powerup" and spawnedItems[x][0] == 1:
                    if attackMultiplier == 1:
                        attackMultiplier = 2
                        timeRemainingAttackBoost = 1000
                        spawnedItems.pop(x)
                        break
                    else:
                        print("Attack boost already applied.")


def jump(): # Is called when the player jumps, calculates the player movement up and down when jumping, as well as stopping the jump when landing.
    global player
    global jumpCount
    global playerPosition
    global jumping
    if jumpCount < 20:
        move = pygame.math.Vector2(0, -((screenWidth / 800) * (0.1 * jumpCount)) - gravity - (screenWidth / 800))
    else:
        move = pygame.math.Vector2(0, -(screenWidth / 600) - gravity - (screenWidth / 800))
    nextPlayer_y = player.move(0, move.y)
    for x, tileRectRow in enumerate(tileRect):
        for y, tileRectRowColumn in enumerate(tileRectRow):
            if nextPlayer_y.colliderect(tileRect[x][y]) and (map[x][y] == GRID_COLOR or map[x][y] == WALL_COLOR or map[x][y] == FLOOR_NEXT_COL) and tileRect[x][y].top < nextPlayer_y.top:
                if move.y > 0:  # moving down
                    move.y = 0
                elif move.y < 0:  # moving up
                    move.y = 0
                break

    playerPosition[1] -= move.y
    jumpCount += 1


playerPosition = []
jumping = False

spawnedEnemies = []
def spawnEnemies():
    for x in range(40):
        location = [random.randint(0, 66), random.randint(0, 64)]
        isDone = False
        while isDone == False:
            if location in onGround:
                isDone = True
            else:
                location = [random.randint(0, 66), random.randint(0, 64)]
        enemyType = random.randint(0, len(enemies)-1)
        spawnedEnemies.append([enemies[enemyType][0], enemies[enemyType][1], location, 100])

enemiesRendered = []
def renderEnemies():
    global spawnedEnemiesCopy, spawnedEnemies, enemiesRendered
    enemiesRendered = []
    if len(spawnedEnemies) > 0:
        for x in range (len(spawnedEnemies)):
            enemiesRendered.append(pygame.Rect(((tileWidth) * (spawnedEnemies[x][2][0])) + playerPosition[0],
                                             ((tileHeight) * (spawnedEnemies[x][2][1])) + playerPosition[1] + tileHeight - (screenHeight/30) +1,
                                             screenWidth / 30, screenHeight / 30))
            pygame.draw.rect(screen, spawnedEnemies[x][1], enemiesRendered[-1])
            if abs(enemiesRendered[-1].x - player.x) < 100 and abs(enemiesRendered[-1].y - player.y) < 100:
                enemyHealthText = font2.render(str(spawnedEnemies[x][3]), True, (30,30,30))
                enemyHealthTextRect = enemyHealthText.get_rect(center=(enemiesRendered[-1].center[0],enemiesRendered[-1].center[1] - 20))
                screen.blit(enemyHealthText, enemyHealthTextRect)
            enemyNameText = font2.render(spawnedEnemies[x][0][0], True, (30, 30, 30))
            enemyNameTextRect = enemyNameText.get_rect(center=(enemiesRendered[-1].center[0], enemiesRendered[-1].center[1]))
            screen.blit(enemyNameText, enemyNameTextRect)


itemSelected = 1



def renderInventory():
    global itemSelected, mouseNotUp, playerGridPosition, inventoryBackground
    inventoryBackground = pygame.Rect(screenWidth/2 - 100, screenHeight - 100, 200, 80)
    selectedItem1Rect = pygame.Rect(screenWidth / 2 - 100, screenHeight - 100, 100, 80)
    selectedItem2Rect = pygame.Rect(screenWidth / 2, screenHeight - 100, 100, 80)
    item1Inventory = pygame.Rect(screenWidth / 2 - 50 - 15, screenHeight - 60 - 12.5, 30, 25)
    item2Inventory = pygame.Rect(screenWidth / 2 + 50 - 15, screenHeight - 60 - 12.5, 30, 25)
    draw_rect_alpha(screen, (0,0,0,128), inventoryBackground)
    if itemSelected == 1:
        draw_rect_alpha(screen, (200,200,200,128), selectedItem1Rect)
        if pygame.mouse.get_pressed()[0] and selectedItem2Rect.collidepoint(pygame.mouse.get_pos()) and mouseNotUp == False:
            itemSelected = 2
            mouseNotUp = True
        if pygame.mouse.get_pressed()[0] and selectedItem1Rect.collidepoint(pygame.mouse.get_pos()) and mouseNotUp == False and playerInventory[0] != []:
            spawnedItems.append([playerInventory[0][0], playerInventory[0][1], (playerGridPosition[0], playerGridPosition[1])])
            print(spawnedItems[-1][2])
            playerInventory[0] = []
            mouseNotUp = True
    if itemSelected == 2:
        draw_rect_alpha(screen, (200, 200, 200, 128), selectedItem2Rect)
        if pygame.mouse.get_pressed()[0] and selectedItem1Rect.collidepoint(pygame.mouse.get_pos()) and mouseNotUp == False:
            itemSelected = 1
            mouseNotUp = True
        if pygame.mouse.get_pressed()[0] and selectedItem2Rect.collidepoint(pygame.mouse.get_pos()) and mouseNotUp == False and playerInventory[1] != []:
            spawnedItems.append([playerInventory[1][0], playerInventory[1][1], ((((screenWidth/2) - playerPosition[0])/ (tileWidth))//1, (((screenHeight/2) - playerPosition[1])/ (tileHeight))//1)])
            print(spawnedItems[-1][2])
            playerInventory[1] = []
            mouseNotUp = True
    if playerInventory[0] != []:
        print(weapons[playerInventory[0][0]][0])
        pygame.draw.rect(screen, weapons[playerInventory[0][0]][1], item1Inventory)
    if playerInventory[1] != []:
        pygame.draw.rect(screen, weapons[playerInventory[1][0]][1], item2Inventory)

def update(screen, cells, size, with_progress=False): # Procedural generation, unused.
    global map

    # Create temporary matrix of zeros
    temp = np.zeros((cells.shape[0], cells.shape[1]))

    for row, col in np.ndindex(cells.shape):
        if col == 0:
            map.append([])
        walls = np.sum(cells[row - 1:row + 2, col-1:col+2]) - cells[row, col]
        colour = FLOOR_COLOR if cells[row, col] == 0 else WALL_COLOR

        #Apply rules (if more than 4 walls create a wall, else a floor)
        if walls > 4:
            temp[row, col] = 1
            if with_progress:
                colour = WALL_COLOR
        else:
            if cells[row, col] == 1:
                if with_progress:
                    colour = FLOOR_NEXT_COL

        # Append colour to map array
        map[row].append(colour)

    # Set borders to walls
    temp[0:60, 0] = 1
    temp[0, 0:80] = 1
    temp[0:60, 79] = 1
    temp[59, 0:80] = 1

    return temp


def saveFile(): # Saves the current file, used when exiting the game
    global fileLine
    print(currentFile)
    fileLine[2] = str(playerPosition[0]) + " " + str(playerPosition[1])
    fileLine[3] = ""
    for y in range(len(map)):
        for x in range(len(map[y])):
            if map[y][x] == FLOOR_COLOR:
                map[y][x] = "FLOOR_COLOR"
            elif map[y][x] == FLOOR_NEXT_COL:
                map[y][x] = "FLOOR_NEXT_COL"
            elif map[y][x] == WALL_COLOR:
                map[y][x] = "WALL_COLOR"
            elif map[y][x] == GRID_COLOR:
                map[y][x] = "GRID_COLOR"
    for y in range(len(map)):
        mapTemp = map[y]
        map[y] = ""
        for x in range(len(mapTemp)):
            if x == len(mapTemp) - 1:
                map[y] += mapTemp[x]
            else:
                map[y] += mapTemp[x] + " "

    for x in range(len(map)):
        if x == len(map) - 1:
            fileLine[3] += map[x]
        else:
            fileLine[3] += map[x] + "  "
    for x in range(len(fileLine)):
        fileLine[x] = str(fileLine[x]) + "\n"
    with open("gamesaves/" + currentFile, 'w') as file:
        file.writelines(fileLine)

CollectItem = False

speed = 400
timeRemainingSpeedBoost = 0
timeRemainingAttackBoost = 0

def isOnGround():
    global onGround, onGroundMap
    onGround = []
    for x in range(len(map)):
        for y in range(len(map[0])):
            if y == 64:
                if map[x][y] == GRID_COLOR or map[x][y] == WALL_COLOR or map[x][y] == FLOOR_NEXT_COL:
                    pass
                else:
                    onGround.append([x,y])
            else:
                if map[x][y + 1] == FLOOR_COLOR:
                    pass
                else:
                    if map[x][y] == GRID_COLOR or map[x][y] == WALL_COLOR or map[x][y] == FLOOR_NEXT_COL:
                        pass
                    else:
                        onGround.append([x,y])
    onGroundMap = []
    for x in range(len(map)):
        onGroundMap.append([])
        for y in range(len(map)):
            if [y,x] in onGround:
                onGroundMap[x].append(1)
            else:
                onGroundMap[x].append(0)

clock = pygame.time.Clock()

while True:
    pygame.display.update()

    for event in pygame.event.get():
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
                    playerPosition = [screenWidth, 0]
                if event.key == pygame.K_e:
                    CollectItem = True
            if event.key == pygame.K_F11: # - disabled due to issues with collision and player position.
                toggleFullscreen()
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

    keys = pygame.key.get_pressed()

    if inGame:
        playGame(currentFile)

        # print(playerPosition)

        key = pygame.key.get_pressed()
        up = key[pygame.K_w] or key[pygame.K_UP]
        down = key[pygame.K_s] or key[pygame.K_DOWN]
        left = key[pygame.K_a] or key[pygame.K_LEFT]
        right = key[pygame.K_d] or key[pygame.K_RIGHT]

        if jumping:
            jump()

        move = pygame.math.Vector2(right - left, 0)
        if not jumping:
            move.y -= gravity
        if move.length_squared() > 0:
            move.scale_to_length(screenWidth / speed)

            nextPlayer_x = player.move(move.x, 0)
            for x, tileRectRow in enumerate(tileRect):
                for y, tileRectRowColumn in enumerate(tileRectRow):
                    if nextPlayer_x.colliderect(tileRect[x][y]) and (map[x][y] == GRID_COLOR or map[x][y] == WALL_COLOR or map[x][y] == FLOOR_NEXT_COL):
                        if move.x > 0:  # moving right
                            move.x = 0
                        elif move.x < 0:  # moving left
                            move.x = 0
                        # print("X collision")
                        break

            nextPlayer_y = player.move(0, move.y)
            for x, tileRectRow in enumerate(tileRect):
                for y, tileRectRowColumn in enumerate(tileRectRow):
                    if nextPlayer_y.colliderect(tileRect[x][y]) and (map[x][y] == GRID_COLOR or map[x][y] == WALL_COLOR or map[x][y] == FLOOR_NEXT_COL):
                        if move.y > 0:  # moving down
                            move.y = 0
                        elif move.y < 0:  # moving up
                            move.y = 0
                        # print("Y collision")
                        break

            if playerPosition[0] <= -3268.8:
                if move.x > 0:
                    move.x = 0
                playerPosition[0] = -3268.8
            if playerPosition[0] >= 561:
                if move.x < 0:
                    move.x = 0
                playerPosition[0] = 561
            if playerPosition[1] <= -1776:
                if move.y > 0:
                    move.y = 0
                playerPosition[1] = -1776
            if playerPosition[1] >= 315.2:
                if move.y < 0:
                    move.y = 0
                playerPosition[1] = 315.2


            playerPosition[0] -= move.x
            playerPosition[1] -= move.y
            fileLine[2] = playerPosition

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

    if displayAudioError == True and audioMessagePressed == False:
        audioErrorText = font.render("Audio Error. Press to dismiss.", True, (255, 0, 0))
        audioErrorTextRect = audioErrorText.get_rect(center=(screenWidth / 2, screenHeight - 30))
        screen.blit(audioErrorText, audioErrorTextRect)
        if pygame.mouse.get_pressed()[0] and audioErrorTextRect.collidepoint(pygame.mouse.get_pos()):
            audioMessagePressed = True

    clock.tick(60)

# FIXME: Player sometimes goes one pixel into the wall. No clue what causes it, it appears to be random. Player cannot move in other axis until moving away from the wall.
# FIXME: Game crashes after making a game file and then trying to load that game file. For some reason loading the game file that was just created does not work.
# FIXME: things can spawn in areas inaccessible to the player. this could just be an item or powerup that then cant be used, but it could also be an enemy, in which case the game cannot be won.
# FIXME: soldiers and wizards go 1 too far left and 2 too far right, which can cause many issues.

# Todo: Add enemy fighting
# Todo: Add player health
# Todo: Add death screen
# Todo: Add difficulty settings
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