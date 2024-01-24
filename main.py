import sys
import pygame
from pygame.locals import QUIT
import numpy as np
import time
import os
import random

pygame.init()

screen = pygame.display.set_mode((1152, 648))
pygame.display.set_caption('NEA')
font = pygame.font.Font(None, 32)
isFullscreen = False
displayAudioError = False
audioMessagePressed = False
try:
    pygame.mixer.init()
except:
    displayAudioError = True
    audioMessagePressed = False

if os.path.isdir('gamesaves'):
    global gameSaves
    gameSaves = os.listdir('gamesaves')
    print(gameSaves)
else:
    os.mkdir('gamesaves')

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

powerups = [['Increased speed', (0,0,200)]

]

weapons = [['Gun', (200,0,0)]

]

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
        player = pygame.Rect(screen.get_width() / 2 - (screen.get_width() / 2) / 40,
                             screen.get_height() / 2 - (screen.get_height() / 2) / 40, (screen.get_width() / 2) / 20,
                             (screen.get_height() / 2) / 20)


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


def loadFile(file): # loads the chosen game file
    global inGame
    global loadMenu
    global currentFile
    global currentFile
    global firstTimeRun
    print(f'load {file}')
    inGame = True
    loadMenu = False
    currentFile = file
    firstTimeRun = True


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
    menuNameTextRect = menuNameText.get_rect(center=(screen.get_width() / 2, screen.get_height() / 6))
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
    TextBackground = pygame.Rect(0, 0, screen.get_width(), menuNameTextRect.centery + 15)
    pygame.draw.rect(screen, (20, 20, 20), TextBackground)
    screen.blit(menuNameText, menuNameTextRect)

mapGenerated = False

def playGame(file): # Handles most of the gameplay TODO: Split into multiple functions
    global playerPosition, fileLine, firstTimeRun, map, player, tileRect, tile, running, mapGenerated, cells, size
    if firstTimeRun == True:
        mapGenerated = False
        with open(f"gamesaves/{file}", "r") as f:
            fileLine = [line.strip() for line in f]
        firstTimeRun = False
        player = pygame.Rect(screen.get_width() / 2 - (screen.get_width() / 2) / 40,
                             screen.get_height() / 2 - (screen.get_height() / 2) / 40, (screen.get_width() / 2) / 20,
                             (screen.get_height() / 2) / 20)
        size = 10
        map = []
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
            mapGenerated = True
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

        else:
            playerPosition = [float(fileLine[2].split(" ")[0]), float(fileLine[2].split(" ")[1])]
            map = []
            mapTemp = fileLine[3].split("  ")
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
    #    running = 34
    # if mapGenerated:
        # if running > 0:
        #     map = []
        #     cells = update(screen, cells, size, with_progress=True)
        #     running -= 1
    # backgroundImage = pygame.image.load('Seasonal Tilesets/1 - Grassland/Background parts/_Complete_static_BG_(288 x ''208).png')
    # backgroundImage = pygame.transform.scale(backgroundImage, (screen.get_width(), screen.get_height()))
    # screen.blit(backgroundImage, (0, 0))
    screen.fill((50, 50, 50))
    tileRect = []
    tile = []
    for x, colour in enumerate(map, start=0):
        tileRect.append([])
        tile.append([])
        for y, tileColour in enumerate(colour, start=0):
            tileRect[x].append(pygame.Rect(((screen.get_width() / 20) * (x)) + playerPosition[0],
                                           ((screen.get_height() / 20) * (y)) + playerPosition[1],
                                           screen.get_width() / 20 + 1, screen.get_height() / 20 + 1))
            tile[x].append([pygame.draw.rect(screen, tileColour, tileRect[x][y]), (255, 0, 0)])
    pygame.draw.rect(screen, (0, 255, 0), player)

spawnedItems = []
def spawnItem(type):
    global spawnedItems
    location = (random.randint(0,15*5),random.randint(0,13*5))
    print(location)
    print("map len "+str(len(map))+" "+str(len(map[0])))
    while map[location[0]][location[1]] == GRID_COLOR or map[location[0]][location[1]] == WALL_COLOR or map[location[0]][location[1]] == FLOOR_NEXT_COL:
        location = (random.randint(0, 15 * 5), random.randint(0, 13 * 5))
    if type == "powerup":
        spawnedItems.append([random.randint(0, len(powerups)), type, location])
    elif type == "weapon":
        spawnedItems.append([random.randint(0, len(weapons)), type, location])

itemsRendered = []
def renderItem(spawnedItems, amount):
    itemsRendered = []
    for x in range(amount):
        itemsRendered.append(pygame.Rect(spawnedItems[x][2][0],spawnedItems[x][2][1],screen.get_width()/30,screen.get_height()/30))
        if spawnedItems[x][1] == "powerup":
            pygame.draw.rect(screen,powerups[spawnedItems[x][0]][1],itemsRendered[-1])
        elif spawnedItems[x][1] == "weapon":
            pygame.draw.rect(screen, weapons[spawnedItems[x][0]][1], itemsRendered[-1])

def jump(): # Is called when the player jumps, calculates the player movement up and down when jumping, as well as stopping the jump when landing.
    global player
    global jumpCount
    global playerPosition
    global jumping
    if jumpCount >= -10:
        neg = 1
        if jumpCount < 0:
            neg = -1

        move = pygame.math.Vector2(0, -(jumpCount ** 2 * 0.1 * neg))
        nextPlayer_y = player.move(0, move.y)
        for x, tileRectRow in enumerate(tileRect):
            for y, tileRectRowColumn in enumerate(tileRectRow):
                if nextPlayer_y.colliderect(tileRect[x][y]) and (map[x][y] == GRID_COLOR or map[x][y] == WALL_COLOR or map[x][y] == FLOOR_NEXT_COL) and tileRect[x][y].top < nextPlayer_y.top:
                    jumpCount = -1

                if nextPlayer_y.colliderect(tileRect[x][y]) and (map[x][y] == GRID_COLOR or map[x][y] == WALL_COLOR or map[x][y] == FLOOR_NEXT_COL) and tileRect[x][y].bottom > nextPlayer_y.bottom:
                    if move.y > 0:  # moving down
                        move.y = 0
                    elif move.y < 0:  # moving up
                        move.y = 0
                    break

        playerPosition[1] -= move.y
        jumpCount -= 1
    else:
        jumping = False
        jumpCount = 10


playerPosition = []
jumping = False


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
    print(currentFile)
    fileLine[1] = 'firstplaythroughFalse'
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
                        jumpCount = 10
                if event.key == pygame.K_h:
                    playerPosition = [screen.get_width(), 0]
            # if event.key == pygame.K_F11: - disabled due to issues with collision and player position.
            #     toggleFullscreen()

        if event.type == pygame.MOUSEWHEEL:
            if menu == 'play' and loadMenu == True and menuNameTextRect.centery + (
                    50 + ((len(buttonsList) - 1) * 50)) > screen.get_height():
                ButtonsListOffset += event.y * 10
                if ButtonsListOffset > 0:
                    ButtonsListOffset = 0
                if menuNameTextRect.centery + ButtonsListOffset + (
                        50 + ((len(buttonsList) - 1) * 50)) + 30 < screen.get_height():
                    ButtonsListOffset -= event.y * 10
    screen.fill((20, 20, 20))

    if loadMenu:
        mainMenu(menu)

    keys = pygame.key.get_pressed()

    if inGame:
        playGame(currentFile)

        print(playerPosition)

        key = pygame.key.get_pressed()
        up = key[pygame.K_w] or key[pygame.K_UP]
        down = key[pygame.K_s] or key[pygame.K_DOWN]
        left = key[pygame.K_a] or key[pygame.K_LEFT]
        right = key[pygame.K_d] or key[pygame.K_RIGHT]

        if jumping:
            jump()

        # for x in range(20):
        #     spawnItem("powerup")
        #     spawnItem("weapon")
        # renderItem(spawnedItems, 20)

        move = pygame.math.Vector2(right - left, down - up)
        if not jumping:
            move.y -= gravity
        if move.length_squared() > 0:
            move.scale_to_length(screen.get_width() / 800)

            nextPlayer_x = player.move(move.x, 0)
            for x, tileRectRow in enumerate(tileRect):
                for y, tileRectRowColumn in enumerate(tileRectRow):
                    if nextPlayer_x.colliderect(tileRect[x][y]) and (map[x][y] == GRID_COLOR or map[x][y] == WALL_COLOR or map[x][y] == FLOOR_NEXT_COL):
                        if move.x > 0:  # moving right
                            move.x = 0
                        elif move.x < 0:  # moving left
                            move.x = 0
                        print("X collision")
                        break

            nextPlayer_y = player.move(0, move.y)
            for x, tileRectRow in enumerate(tileRect):
                for y, tileRectRowColumn in enumerate(tileRectRow):
                    if nextPlayer_y.colliderect(tileRect[x][y]) and (map[x][y] == GRID_COLOR or map[x][y] == WALL_COLOR or map[x][y] == FLOOR_NEXT_COL):
                        if move.y > 0:  # moving down
                            move.y = 0
                        elif move.y < 0:  # moving up
                            move.y = 0
                        print("Y collision")
                        break

            if playerPosition[0] < -3268.8:
                if move.x > 0:
                    move.x = 0
                playerPosition[0] = -3268.8
            if playerPosition[0] > 561:
                if move.x < 0:
                    move.x = 0
                playerPosition[0] = 561
            if playerPosition[1] < -1776:
                if move.y > 0:
                    move.y = 0
                playerPosition[1] = -1776
            if playerPosition[1] > 315.2:
                if move.y < 0:
                    move.y = 0
                playerPosition[1] = 315.2


            playerPosition[0] -= move.x
            playerPosition[1] -= move.y
            fileLine[2] = playerPosition

    if displayAudioError == True and audioMessagePressed == False:
        audioErrorText = font.render("Audio Error. Press to dismiss.", True, (255, 0, 0))
        audioErrorTextRect = audioErrorText.get_rect(center=(screen.get_width() / 2, screen.get_height() - 30))
        screen.blit(audioErrorText, audioErrorTextRect)
        if pygame.mouse.get_pressed()[0] and audioErrorTextRect.collidepoint(pygame.mouse.get_pos()):
            audioMessagePressed = True

# FIXME: Player sometimes goes one pixel into the wall. No clue what causes it, it appears to be random. Player cannot move in other axis until moving away from the wall.
# FIXME: Player moves up and down when at the bottom of the map. Just visual, causes no gameplay issues.

# Todo: Make sure all platforms are accessible
# Todo: Properly adjust player speed, jump height, then remove up/down movement.
# Todo: Add sprites/assets
# Todo: Add levels
# Todo: Add items
# Todo: Add Enemies
# Todo: Add pathfinding for enemies
# Todo: Add health
# Todo: Add death screen
# Todo: Add doors

# Considerations for V2:
# Add random player spawning
