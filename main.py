# importing different libraries
import sys
import pygame
from pygame.locals import QUIT
import os
import random
import pathfinding
from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder
from threading import Thread
import math

pygame.init()
pygame.joystick.init()
joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]

# defining different variables
screen = pygame.display.set_mode((1152, 648))
pygame.display.set_caption('NEA')
font = pygame.font.Font(None, 32)
font2 = pygame.font.Font(None, 24)
font3 = pygame.font.Font(None, 12)
isFullscreen = False
displayAudioError = False
audioMessagePressed = False
try:
    pygame.mixer.init() # initialising audio
except:
    displayAudioError = True
    audioMessagePressed = False

loadMenu = True
menu = 'main'
ButtonsListOffset = 0
volume = 100
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
tileWidth = screenWidth/20
tileHeight = screenHeight/20
PresetMaps = [ # the maps used in the game. "-" is the floors/walls (where the player cant pass through), and " " is empty space, where the player can pass through.
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
            ['Damage x2', (0,200,200)],
            ['+20 health', (200, 25, 25)]

]

weapons = [['Gun', (0,200,0)],
           ['Sword', (200,200,0)],
           ['Wand', (100, 255, 255)]

]

enemies = [['Knight', (200,75,0)],
           ['Wizard', (200,0,75)],
           ['Soldier', (0,0,100)]

]

inGame = False

def button(text, position, size, colour, action=None, *args):
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
    button_rect = pygame.Rect(position[0] - (size[0] / 2), position[1] - (size[1] / 2), size[0], size[1]) # creates a pygame Rect for the button
    pygame.draw.rect(screen, colour, button_rect)  # draws that rect onto the screen
    text = font.render(text, True, (0, 0, 0)) # creates the text to write on the screen
    textRect = text.get_rect(center=button_rect.center) # creates a pygame rect for the text on the screen in the middle of the button
    screen.blit(text, textRect) # draws the text on the screen
    if button_rect.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0] and mouseNotUp == False and action != None: # determines whether or not the button has been pressed
        action(*args) # does the action associated with pressing the button
        mouseNotUp = True


def menuEquals(menu_set):
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
    if menu == 'new':
        difficulty = 'Easy'
        typedText = ''
    if menu == 'play':
        if os.path.isdir('gamesaves'):
            global gameSaves
            gameSaves = os.listdir('gamesaves')
        else:
            os.mkdir('gamesaves')
    ButtonsListOffset = 0


def changeVolume():
    # changes the volume, this function is called when the volume button is pressed.
    # like the function above, this also exists due to the way the button function works.
    global volume
    volume += 10
    if volume > 100:
        volume = 0
    pygame.mixer.music.set_volume(volume / 100)


def drawTextBox(text, position, size, colour, borderColour, borderSize, typedText):
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
    if typedText != '':
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


def loadFile(file):
    # loads the chosen game file. This function closes the main menu and starts the game
    # Input:
    #   file - string, determines which file is loaded
    # Output:
    #   Starts the game

    global inGame, loadMenu, currentFile, firstTimeRun, map, playerPosition, fileLine
    inGame = True
    loadMenu = False
    currentFile = file
    firstTimeRun = True
    with open(f"gamesaves/{file}", "r") as f:
        fileLine = [line.strip() for line in f]
    if fileLine[1] == "firstPlaythroughFalse":
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


def mainMenu(menu):
    # Shows and handles almost everything related to the main menu
    # It determines which buttons to show, then displays them on the screen.
    # Input:
    #   menu - string, controls which menu is currently showing
    # Output:
    #   displays the current menu on the screen
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
    # Determines if the enemies should be moving.
    # for each enemy, it finds the players position, the enemies position, the possible paths that can be taken, and finally whether a path exists between the enemy and the player
    # It then moves the enemy in the direction of the player (or away, if that is what the pathfinding finds) if a path was found.
    # A new path for each enemy is only generated every 50 frames, however the enemy is moved every frame.
    global enemiesToMove, grid, spawnedEnemies, playerGridPosition, pathGrid, pathTicks, inThread, onGroundMap
    inThread = True
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
                if spawnedEnemies[x][0] == 'Wizard':
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
                elif spawnedEnemies[x][0] == "Knight":
                    for l in range(len(pathGrid)):
                        if 'x' in pathGrid[l] or 'se' in pathGrid[l] or 'es' in pathGrid[l]:
                            for i in reversed(range(len(pathGrid[l]))):
                                if pathGrid[l][i] == 'x' or (pathGrid[l][i] == 'e' and (pathGrid[l][i-1] == 's' or pathGrid[l][i+1] == 's')):
                                    n = playerGridPosition[0]
                            enemiesToMove.append([x, (n, l)])
        pathTicks = 50
    if enemiesToMove != []:
        for x in range(len(enemiesToMove)):
            if spawnedEnemies[enemiesToMove[x][0]][2] != enemiesToMove[x][1]:
                if spawnedEnemies[enemiesToMove[x][0]][2][0]//1 > enemiesToMove[x][1][0]//1:
                    spawnedEnemies[enemiesToMove[x][0]][2][0] -= 0.05
                if spawnedEnemies[enemiesToMove[x][0]][2][0]//1 < enemiesToMove[x][1][0]//1:
                    spawnedEnemies[enemiesToMove[x][0]][2][0] += 0.05
    pathTicks -= 1
    inThread = False

healthBoostsGone = False
timeSinceSpawnHealthBoosts = 0

attackMultiplierEnemies = 1

enemiesDefeated = False

def playGame(file): # TODO: Split into multiple functions
    # Handles most of the gameplay.
    # The main game function where most other functions are called (other than menu functions)
    # Sets up the file if it is the first time running the file
    # loads everything in the first frame
    # manages player health, enemy health, enemy/player attacks, UI elements, starting pathfinding, etc.
    # Input:
    #   file - string, the file that is currently open
    global playerPosition, enemiesDefeated, playerInventory, difficulty, attackMultiplierEnemies, healthBoostsGone, timeSinceSpawnHealthBoosts, playerGridPosition, fileLine, firstTimeRun, timeSinceGun, enemyPreviousPosition, TriggerNotUp, spawnedItems, gameLost, spawnedEnemies, timeSinceSword, timeSinceWand, playerHealth, timeSinceEnemyAttack, randomEnemyAttackTime, randomAttackTime, map, player, tileRect, tile, running, mapGenerated, cells, size, givePaths, pathTicks, enemiesToMove, grid, inThread, ButtonNotUp, mouseNotUp
    if firstTimeRun == True:
        playerInventory = [[], []]
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
            playerPosition = [90, -10]
            fileLine[2] = playerPosition
            map = []
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
        if difficulty == 1:
            for x in range(10):
                spawnItem("powerup", True)
        elif difficulty == 2:
            for x in range(5):
                spawnItem("powerup", True)
        spawnEnemies()
        timeSinceEnemyAttack = []
        for x in range(len(spawnedEnemies)):
            timeSinceEnemyAttack.append(0)
            timeSinceWand.append(0)
        playerHealth = 100
        randomEnemyAttackTime = 50
        enemyPreviousPosition = []
        for x in range(len(spawnedEnemies)):
            enemyPreviousPosition.append(spawnedEnemies[x][2])
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
    if not gameLost and not enemiesDefeated:
        if 'pathfindingThread' in globals():
            # noinspection PyUnboundLocalVariable
            if not pathfindingThread.is_alive():
                pathfindingThread.start()
        else:
            pathfindingThread = Thread(target=pathfinding)
            pathfindingThread.start()
        if not inventoryBackground.collidepoint(pygame.mouse.get_pos()) and ((pygame.mouse.get_pressed()[
            0] and mouseNotUp == False) or ((joysticks and joysticks[0].get_axis(5) > 0.5) and TriggerNotUp == False)) and ((itemSelected == 1 and playerInventory[0] != []) or (itemSelected == 2 and playerInventory[1] != [])):

            if pygame.mouse.get_pressed()[0]:
                mouseNotUp = True
                Attack(playerInventory[itemSelected - 1][0], player)
            if (joysticks and joysticks[0].get_axis(5) > 0.5):
                TriggerNotUp = True
                Attack(playerInventory[itemSelected - 1][0], player, True)
        timeSinceSword += 1
        timeSinceGun += 1
        for x in range(len(timeSinceWand)):
            timeSinceWand[x] += 1
        for x in range(len(spawnedEnemies)):
            if abs(enemiesRendered[x].x - player.x) < 30 and abs(enemiesRendered[x].y - player.y) < 40 and timeSinceEnemyAttack[x] > randomEnemyAttackTime:
                if spawnedEnemies[x][0] == 'Knight':
                    timeSinceEnemyAttack[x] = 0
                    playerHealth -= random.randint(2, 5) * attackMultiplierEnemies
                    criticalHit = random.randint(0, 100)
                    if criticalHit == 99:
                        playerHealth -= 5 * attackMultiplierEnemies
            distance = pygame.math.Vector2(abs(enemiesRendered[x].x - player.x), abs(enemiesRendered[x].y - player.y))
            if distance.length() < 300:
                if spawnedEnemies[x][0] == 'Wizard':
                    Attack(2, x)
                if spawnedEnemies[x][0] == 'Soldier':
                    Attack(0, x)
                randomEnemyAttackTime = random.randint(60, 85)
        for x in range(len(timeSinceEnemyAttack)):
            timeSinceEnemyAttack[x] += 1
        if not healthBoostsGone:
            noHealthBoosts = True
            for x in range(len(spawnedItems)):
                if spawnedItems[x][0] == 2 and spawnedItems[x][1] == 'powerup':
                    noHealthBoosts = False
            if noHealthBoosts == True:
                healthBoostsGone = True
        else:
            if timeSinceSpawnHealthBoosts >= 600:
                spawnItem("powerup", True)
                timeSinceSpawnHealthBoosts = 0
            z = 0
            for x in range(len(spawnedItems)):
                if spawnedItems[x][0] == 2 and spawnedItems[x][1] == 'powerup':
                    z += 1
            if z >= 10:
                healthBoostsGone = False
        timeSinceSpawnHealthBoosts += 1
    if playerHealth <= 0:
        gameLost = True
    if gameLost:
        lostGame()
    if enemiesDefeated:
        wonGame()
    manageBullets()
    if not spawnedEnemies:
        enemiesDefeated = True
    playerHealthRect = pygame.Rect(20, 20, 200 * (playerHealth / 100), 20)
    playerHealthText = font2.render(str(playerHealth), True, (0, 0, 0))
    playerHealthTextRect = playerHealthText.get_rect(left=20, top=playerHealthRect.bottom + 5)
    if playerHealth > 0:
        pygame.draw.rect(screen, (200, 25, 25), playerHealthRect)
        screen.blit(playerHealthText, playerHealthTextRect)
    if len(spawnedEnemies) > 0:
        enemiesRemainingRect = pygame.Rect(20, playerHealthTextRect.bottom + 5, 200 * (len(spawnedEnemies) / 40), 20)
        pygame.draw.rect(screen, (128, 128, 128), enemiesRemainingRect)
        enemiesRemainingText = font2.render(str(len(spawnedEnemies)) + " enemies remaining", True, (0, 0, 0))
        enemiesRemainingTextRect = enemiesRemainingText.get_rect(left=20, top=enemiesRemainingRect.bottom + 5)
        screen.blit(enemiesRemainingText, enemiesRemainingTextRect)
    if timeRemainingSpeedBoost > 0:
        timeRemainingSpeedRect = pygame.Rect(20, enemiesRemainingTextRect.bottom + 5, 200 * (timeRemainingSpeedBoost / 1000), 20)
        pygame.draw.rect(screen, (50, 50, 255), timeRemainingSpeedRect)
        timeRemainingText = font2.render("Speed Boost", True, (0, 0, 0))
        timeRemainingTextRect = timeRemainingText.get_rect(left=20, top=timeRemainingSpeedRect.bottom + 5)
        screen.blit(timeRemainingText, timeRemainingTextRect)
    if timeRemainingAttackBoost > 0:
        if timeRemainingSpeedBoost > 0:
            timeRemainingAttackRect = pygame.Rect(20, timeRemainingTextRect.bottom + 5, 200 * (timeRemainingAttackBoost / 1000), 20)
            pygame.draw.rect(screen, (0, 200, 255), timeRemainingAttackRect)
            timeRemainingText = font2.render("Damage x2", True, (0, 0, 0))
            timeRemainingTextRect = timeRemainingText.get_rect(left=20, top=timeRemainingAttackRect.bottom + 5)
            screen.blit(timeRemainingText, timeRemainingTextRect)
        else:
            timeRemainingAttackRect = pygame.Rect(20, enemiesRemainingTextRect.bottom + 5, 200 * (timeRemainingAttackBoost / 1000), 20)
            pygame.draw.rect(screen, (0, 200, 255), timeRemainingAttackRect)
            timeRemainingText = font2.render("Damage x2", True, (0, 0, 0))
            timeRemainingTextRect = timeRemainingText.get_rect(left=20, top=timeRemainingAttackRect.bottom + 5)
            screen.blit(timeRemainingText, timeRemainingTextRect)

def lostGame():
    # If the player has died, this function is called and displays this screen which creates a gray translucent background, and displays "GAME OVER!" and two buttons to respawn or go to the menu.
    lostGameRect = pygame.Rect(0, 0, screenWidth, screenHeight)
    draw_rect_alpha(screen, (50,50,50, 128), lostGameRect)
    lostGameText = font.render("GAME OVER!", True, (255, 0, 0))
    lostGameTextRect = lostGameText.get_rect(center=(screenWidth / 2, screenHeight / 6))
    screen.blit(lostGameText, lostGameTextRect)
    button('Respawn',(menuNameTextRect.centerx, menuNameTextRect.centery + 100),(150, 37.5), (100, 100, 100), respawn)
    button('Menu', (menuNameTextRect.centerx, menuNameTextRect.centery + 150), (150, 37.5), (100, 100, 100), toMenu)

def wonGame():
    # If the player has killed all enemies (and therefore won), this function is called and displays this screen which creates a gray translucent background, and displays "YOU WON!" and two buttons to play again or go to the menu.
    lostGameRect = pygame.Rect(0, 0, screenWidth, screenHeight)
    draw_rect_alpha(screen, (50, 50, 50, 128), lostGameRect)
    lostGameText = font.render("YOU WON!", True, (255, 0, 0))
    lostGameTextRect = lostGameText.get_rect(center=(screenWidth / 2, screenHeight / 6))
    screen.blit(lostGameText, lostGameTextRect)
    button('Play again', (menuNameTextRect.centerx, menuNameTextRect.centery + 100), (150, 37.5), (100, 100, 100), respawn)
    button('Menu', (menuNameTextRect.centerx, menuNameTextRect.centery + 150), (150, 37.5), (100, 100, 100), toMenu)

def respawn():
    global gameLost, firstTimeRun, mapGenerated
    gameLost = False
    firstTimeRun = True
    mapGenerated = False
    loadFile(currentFile)

def toMenu():
    # takes the user back to the main menu. This function is called when the player presses the button to go to the menu on the game over screen.
    global mapGenerated, inGame, loadMenu, firstTimeRun
    menuEquals('main')
    mapGenerated = False
    inGame = False
    loadMenu = True
    firstTimeRun = True

def draw_rect_alpha(surface, color, rect):
    # sourced from https://stackoverflow.com/questions/6339057/draw-a-transparent-rectangles-and-polygons-in-pygame
    # draws a translucent rectangle on the screen
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
timeSinceGun = 0
randomWandAttackTime = 120
randomEnemyWandAttackTime = 120
randomGunAttackTime = 60

def Attack(weaponType, origin, controller=False):
    # called when the player or an enemy uses a weapon. Checks to see who fired the weapon, which weapon was used and whether the player is close enough to use the weapon.
    # If all conditions are met, it then either lowers the enemy/player health (if it is a sword being used) or spawns a bullet/magic
    # Input:
    #   weaponType - string, determines which weapon is being used (sword, gun, wand)
    #   origin - integer (if it is an enemy) or pygame.Rect (if it is the player), determines who fired the weapon
    # Output:
    #   if it is a gun or wand being fired, it appends to the wandFired or bulletsFired array
    global timeSinceSword, randomAttackTime, timeSinceGun, timeSinceWand, randomWandAttackTime, randomEnemyWandAttackTime, randomGunAttackTime
    if weaponType == 0:
        if origin == player:
            if timeSinceGun > randomAttackTime:
                if controller == False:
                    bulletsFired.append([playerGridPosition, pygame.Rect(player.x + (player.width/2), player.y + player.height - (player.height * (1/3)), player.width * (4/5), player.height * (1/3)), math.atan2((pygame.mouse.get_pos()[1] - player.y), (pygame.mouse.get_pos()[0] - player.x)), origin])
                else:
                    bulletsFired.append([playerGridPosition, pygame.Rect(player.x + (player.width / 2), player.y + player.height - (player.height * (1 / 3)), player.width * (4 / 5), player.height * (1 / 3)), math.atan2(joysticks[0].get_axis(3),joysticks[0].get_axis(2)), origin])
                timeSinceGun = 0
                randomAttackTime = random.randint(10, 15)
        else:
            if timeSinceWand[origin+1] > randomGunAttackTime:
                bulletsFired.append([spawnedEnemies[origin][2], pygame.Rect(enemiesRendered[origin].x + (enemiesRendered[origin].width / 2), enemiesRendered[origin].y + enemiesRendered[origin].height - (player.height * (1 / 3)),player.width * (4 / 5), player.height * (1 / 3)), math.atan2((player.y - enemiesRendered[origin].y), (player.x - enemiesRendered[origin].x)), origin])
                timeSinceWand[origin+1] = 0
                colliding = False
                for y, tileRectRow in enumerate(tileRect):
                    for z, tileRectRowColumn in enumerate(tileRectRow):
                        if enemiesRendered[origin].colliderect(tileRect[y][z]) and (
                                map[y][z] == GRID_COLOR or map[y][z] == WALL_COLOR or map[y][z] == FLOOR_NEXT_COL):
                                    randomGunAttackTime = 10
                                    colliding = True
                if not colliding:
                    randomGunAttackTime = random.randint(45, 60)
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
                    if distanceToX.length() < shortestDistance[1].length():
                        shortestDistance = x, pygame.math.Vector2(abs(enemiesRendered[x].x - player.x), abs(enemiesRendered[x].y - player.y))
                if shortestDistance[1].length() < 300:
                    wandFired.append([playerGridPosition, shortestDistance, pygame.Rect(player.x + (player.width/2), player.y - (player.height/2), player.width/4, player.width/4)])
                    timeSinceWand[0] = 0
                    randomWandAttackTime = random.randint(100, 150)
        else:
            if timeSinceWand[origin+1] > randomEnemyWandAttackTime:
                distance = player, pygame.math.Vector2(abs(player.x - enemiesRendered[origin].x), abs(player.y - enemiesRendered[origin].y))
                wandFired.append([spawnedEnemies[origin][2], distance, pygame.Rect(enemiesRendered[origin].x + (player.width/2), enemiesRendered[origin].y - (player.height/2), player.width/4, player.width/4), 0])
                timeSinceWand[origin+1] = 0
                randomEnemyWandAttackTime = random.randint(300, 500)


def manageBullets():
    # is called every frame.
    # manages any current bullets; moves them, checks if they are colliding with an enemy/the player (if it is, it reduces the health of the player/enemy and removes the bullet), checks if it has been alive too long (if it is magic), checks if it has collided with any walls (if it is a bullet. if so, it removes it)
    global playerHealth, AttackMultiplier, spawnedEnemies
    breakForLoop = False
    if wandFired:
        for x in range(len(wandFired) -1, 0, -1):
            if wandFired[x][1][0] == player:
                dx, dy = (playerGridPosition[0] - (wandFired[x][0][0]),playerGridPosition[1] - (wandFired[x][0][1]))
                stepx, stepy = (dx / 25, dy / 25)
                wandFired[x][0] = [wandFired[x][0][0] + stepx, wandFired[x][0][1] + stepy]
                wandFired[x][2] = pygame.Rect(((tileWidth) * (wandFired[x][0][0])) + playerPosition[0] + 20, ((tileHeight) * (wandFired[x][0][1])) + playerPosition[1] + 20, player.width / 4, player.width / 4)
                pygame.draw.circle(screen, (100, 255, 255), wandFired[x][2].center, wandFired[x][2].width)
                wandFired[x][3] += 1
                if wandFired[x][3] >= 250:
                    wandFired.pop(x)
                    continue
                if wandFired[x][2].colliderect(player):
                    if playerHealth <= 1:
                        playerHealth = 0
                    else:
                        playerHealth = int((playerHealth * ((5/6) + ((1/20) * (1/attackMultiplierEnemies))))//1)
                    wandFired.pop(x)
            else:
                dx, dy = (spawnedEnemies[wandFired[x][1][0]][2][0] - (wandFired[x][0][0]), spawnedEnemies[wandFired[x][1][0]][2][1] - (wandFired[x][0][1]))
                stepx, stepy = (dx / 25, dy / 25)
                wandFired[x][0] = [wandFired[x][0][0] + stepx, wandFired[x][0][1] + stepy]
                wandFired[x][2] = pygame.Rect(((tileWidth) * (wandFired[x][0][0])) + playerPosition[0] + 20,((tileHeight) * (wandFired[x][0][1])) + playerPosition[1] + 20, player.width/4, player.width/4)
                pygame.draw.circle(screen, (100, 255, 255), wandFired[x][2].center, wandFired[x][2].width)
                if wandFired[x][2].colliderect(enemiesRendered[wandFired[x][1][0]]):
                    if spawnedEnemies[wandFired[x][1][0]][3] <= 1:
                        spawnedEnemies.pop(wandFired[x][1][0])
                    else:
                        if attackMultiplier == 2:
                            spawnedEnemies[wandFired[x][1][0]][3] = int((spawnedEnemies[wandFired[x][1][0]][3] * (2/4))//1)
                        else:
                            spawnedEnemies[wandFired[x][1][0]][3] = int((spawnedEnemies[wandFired[x][1][0]][3] * (3/4))//1)
                    wandFired.pop(x)
    if bulletsFired:
        for x in range(len(bulletsFired)-1, 0, -1):
            bulletRect = pygame.Rect(((tileWidth) * (bulletsFired[x][0][0])) + playerPosition[0] + 20,
                                     ((tileHeight) * (bulletsFired[x][0][1])) + playerPosition[1] + 20,
                                     bulletsFired[x][1].width, bulletsFired[x][1].height)
            bulletSurface = pygame.Surface((bulletRect.width, bulletRect.height))
            bulletSurface = pygame.transform.rotate(bulletSurface, math.degrees(bulletsFired[x][2]))
            bulletSurfaceRect = bulletSurface.get_rect()
            bulletSurfaceRect.center = bulletRect.center
            if bulletsFired[x][3] == player:
                pygame.draw.rect(screen, (255, 164, 0), bulletSurfaceRect)
            bulletsFired[x][0][0] += 0.2 * math.sin(bulletsFired[x][2] + (math.pi / 2))
            bulletsFired[x][0][1] -= 0.2 * math.cos(bulletsFired[x][2] + (math.pi / 2))
            if bulletsFired[x][3] == player:
                for y in range(len(enemiesRendered)):
                    if bulletSurfaceRect.colliderect(enemiesRendered[y]):
                        if spawnedEnemies[y][3] <= 15:
                            spawnedEnemies.pop(y)
                        else:
                            spawnedEnemies[y][3] -= 15 * attackMultiplier
                        bulletsFired.pop(x)
                        breakForLoop = True
                        break
                if breakForLoop:
                    breakForLoop = False
                    break
            else:
                if bulletSurfaceRect.colliderect(player):
                    playerHealth -= 1 * attackMultiplierEnemies
                    if spawnedEnemies[bulletsFired[x][3]][3] <= 10:
                        spawnedEnemies.pop(bulletsFired[x][3])
                    else:
                        spawnedEnemies[bulletsFired[x][3]][3] -= 10
                    break
            for y, tileRectRow in enumerate(tileRect):
                for z, tileRectRowColumn in enumerate(tileRectRow):
                    if bulletSurfaceRect.colliderect(tileRect[y][z]) and (
                            map[y][z] == GRID_COLOR or map[y][z] == WALL_COLOR or map[y][z] == FLOOR_NEXT_COL):
                        bulletsFired.pop(x)
                        breakForLoop = True
                        break
                if breakForLoop:
                    break
            if breakForLoop:
                breakForLoop = False
                break
            if bulletsFired[x][0][0] <= 0:
                bulletsFired.pop(x)
                break
            if bulletsFired[x][0][0] >= 66:
                bulletsFired.pop(x)
                break
            if bulletsFired[x][0][1] <= 0:
                bulletsFired.pop(x)
                break
            if bulletsFired[x][0][1] >= 67:
                bulletsFired.pop(x)
                break



spawnedItems = []
def spawnItem(type, healthBoost=False):
    # called when the game is started. spawns a random item.
    # Inputs:
    #   type - string, determines whether it is a weapon or a powerup that is spawned.
    # Outputs:
    #   appends a weapon/powerup to the list of weapons/powerups spawned in a random location on the floor
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
        if healthBoost:
            spawnedItems.append([2, type, location])
        else:
            spawnedItems.append([random.randint(0, len(powerups)-1), type, location])
    elif type == "weapon":
        spawnedItems.append([random.randint(0, len(weapons)-1), type, location])

def renderItem(spawnedItems, amount):
    # Is called every frame. Shows the items on screen. If the player is close, it shows text saying the name of the item/powerup and tells the user to press E to pick up.
    # Input:
    #   spawnedItems - array, the list of items to be rendered. It includes which item it is and where it is
    #   amount - the amount of items
    # Output:
    #   a bunch of pygame.Rects which are displayed on screen; the items.
    global speed, timeRemainingSpeedBoost, attackMultiplier, timeRemainingAttackBoost, playerHealth
    itemsRendered = []
    width = screenWidth / 30
    height = screenHeight / 30
    for x in range(amount-1, 0, -1):
        itemsRendered.append(pygame.Rect(((tileWidth) * (spawnedItems[x][2][0])) + playerPosition[0],((tileHeight) * (spawnedItems[x][2][1])) + playerPosition[1] + tileHeight - height +1,width,height))
        if spawnedItems[x][1] == "powerup":
            pygame.draw.rect(screen,powerups[spawnedItems[x][0]][1],itemsRendered[-1])
            if spawnedItems[x][0] == 2:
                enemyNameText = font2.render("+", True, (255, 255, 255))
                enemyNameTextRect = enemyNameText.get_rect(center=(itemsRendered[-1].center[0], itemsRendered[-1].center[1]))
                screen.blit(enemyNameText, enemyNameTextRect)
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
                if spawnedItems[x][1] == "weapon":
                    if playerInventory[0] == []:
                        playerInventory[0] = spawnedItems[x]
                        spawnedItems.pop(x)
                        break
                    elif playerInventory[1] == []:
                        playerInventory[1] = spawnedItems[x]
                        spawnedItems.pop(x)
                        break
                if spawnedItems[x][1] == "powerup" and spawnedItems[x][0] == 0:
                    if speed == 400:
                        speed = 300
                        timeRemainingSpeedBoost = 1000
                        spawnedItems.pop(x)
                        break
                if spawnedItems[x][1] == "powerup" and spawnedItems[x][0] == 1:
                    if attackMultiplier == 1:
                        attackMultiplier = 2
                        timeRemainingAttackBoost = 1000
                        spawnedItems.pop(x)
                        break
                if spawnedItems[x][1] == "powerup" and spawnedItems[x][0] == 2:
                    if playerHealth == 100:
                        pass
                    else:
                        if playerHealth < 80:
                            playerHealth += 20
                        else:
                            playerHealth = 100
                        spawnedItems.pop(x)
                        break



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
    nextPlayer_y = player.move(0, move.y)
    for x, tileRectRow in enumerate(tileRect):
        for y, tileRectRowColumn in enumerate(tileRectRow):
            if nextPlayer_y.colliderect(tileRect[x][y]) and (map[x][y] == GRID_COLOR or map[x][y] == WALL_COLOR or map[x][y] == FLOOR_NEXT_COL) and tileRect[x][y].top < nextPlayer_y.top:
                if move.y > 0:  # moving down
                    move.y = 0
                elif move.y < 0:  # moving up
                    move.y = 0
                break

    if playerPosition[1] <= -1776:
        if move.y > 0:
            move.y = 0
        playerPosition[1] = -1776

    if playerPosition[1] >= 315.2:
        if move.y < 0:
            move.y = 0
        playerPosition[1] = 315.2

    playerPosition[1] -= move.y
    jumpCount += 1


playerPosition = []
jumping = False

spawnedEnemies = []
def spawnEnemies():
    # called at the beginning of the game. spawns 40 enemies.
    # makes sure they are on the ground and not in a wall
    # Output:
    #   appends a random enemy and its location to spawnedEnemies
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
    # called every frame. shows the enemies on screen.
    # if the player is nearby, it shows the enemy's health
    # Output:
    #   a bunch of pygame.Rects that are showed on the screen
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
            if spawnedEnemies[x][0] != "Soldier":
                enemyNameText = font2.render(spawnedEnemies[x][0][0], True, (30, 30, 30))
            else:
                enemyNameText = font2.render("W", True, (255, 255, 255))
            enemyNameTextRect = enemyNameText.get_rect(center=(enemiesRendered[-1].center[0], enemiesRendered[-1].center[1]))
            screen.blit(enemyNameText, enemyNameTextRect)

itemSelected = 1
def renderInventory():
    # shows the inventory at the bottom of the screen. shows which item is currenly selected, and checks to see if either inventory slot is clicked
    # If an inventory slot is clicked, if it is the currently selected slot, it drops the item in the slot, if not, it switches to that item
    # Output:
    #   some rects which are displayed and show the inventory and items
    global itemSelected, mouseNotUp, ButtonNotUp, playerGridPosition, inventoryBackground
    inventoryBackground = pygame.Rect(screenWidth/2 - 100, screenHeight - 100, 200, 80)
    selectedItem1Rect = pygame.Rect(screenWidth / 2 - 100, screenHeight - 100, 100, 80)
    selectedItem2Rect = pygame.Rect(screenWidth / 2, screenHeight - 100, 100, 80)
    item1Inventory = pygame.Rect(screenWidth / 2 - 50 - 15, screenHeight - 60 - 12.5, 30, 25)
    item2Inventory = pygame.Rect(screenWidth / 2 + 50 - 15, screenHeight - 60 - 12.5, 30, 25)
    draw_rect_alpha(screen, (0,0,0,128), inventoryBackground)
    if itemSelected == 1:
        draw_rect_alpha(screen, (200,200,200,128), selectedItem1Rect)
        if (pygame.mouse.get_pressed()[0] and selectedItem2Rect.collidepoint(pygame.mouse.get_pos()) and mouseNotUp == False) or ((joysticks and joysticks[0].get_button(5)) and ButtonNotUp == False):
            itemSelected = 2
            if pygame.mouse.get_pressed()[0]:
                mouseNotUp = True
            if (joysticks and joysticks[0].get_button(5)):
                ButtonNotUp = True
        if (pygame.mouse.get_pressed()[0] and selectedItem1Rect.collidepoint(pygame.mouse.get_pos()) and mouseNotUp == False) or ((joysticks and joysticks[0].get_button(4)) and ButtonNotUp == False) and playerInventory[0] != []:
            spawnedItems.append([playerInventory[0][0], playerInventory[0][1], (playerGridPosition[0], playerGridPosition[1])])
            playerInventory[0] = []
            if pygame.mouse.get_pressed()[0]:
                mouseNotUp = True
            if (joysticks and joysticks[0].get_button(4)):
                ButtonNotUp = True
    if itemSelected == 2:
        draw_rect_alpha(screen, (200, 200, 200, 128), selectedItem2Rect)
        if (pygame.mouse.get_pressed()[0] and selectedItem1Rect.collidepoint(pygame.mouse.get_pos()) and mouseNotUp == False) or ((joysticks and joysticks[0].get_button(4)) and ButtonNotUp == False):
            itemSelected = 1
            if pygame.mouse.get_pressed()[0]:
                mouseNotUp = True
            if (joysticks and joysticks[0].get_button(4)):
                ButtonNotUp = True
        if (pygame.mouse.get_pressed()[0] and selectedItem2Rect.collidepoint(pygame.mouse.get_pos()) and mouseNotUp == False) or ((joysticks and joysticks[0].get_button(5)) and ButtonNotUp == False) and playerInventory[1] != []:
            spawnedItems.append([playerInventory[1][0], playerInventory[1][1], ((((screenWidth/2) - playerPosition[0])/ (tileWidth))//1, (((screenHeight/2) - playerPosition[1])/ (tileHeight))//1)])
            playerInventory[1] = []
            if pygame.mouse.get_pressed()[0]:
                mouseNotUp = True
            if (joysticks and joysticks[0].get_button(5)):
                ButtonNotUp = True
    if playerInventory[0] != []:
        pygame.draw.rect(screen, weapons[playerInventory[0][0]][1], item1Inventory)
    if playerInventory[1] != []:
        pygame.draw.rect(screen, weapons[playerInventory[1][0]][1], item2Inventory)


def saveFile():
    # Saves the current file, called when exiting the game
    # Input:
    #   currentFile - string, the name of the file to be saved
    # Output:
    # writes the player location, the map details, and the fact that the file has been played to the file.
    global fileLine
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
    # Called at the beginning of the game. Determines which tiles are just above the ground.
    # used when spawning enemies and items, and in enemy pathfinding.
    # Output:
    #   onGround - array, list of tiles which are just above the ground
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
                    playerPosition = [screenWidth, 0]
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
    keys = pygame.key.get_pressed()

    if inGame:
        playGame(currentFile)

        key = pygame.key.get_pressed()

        left = 0
        right = 0

        for x in range(len(joysticks)):
            if joysticks[x].get_axis(0) > 0.25:
                right = (abs(joysticks[x].get_axis(0))-0.25)*(4/3)
            if joysticks[x].get_axis(0) < -0.5:
                left = (abs(joysticks[x].get_axis(0))-0.25)*(4/3)

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
        elif (joysticks and joysticks[0].get_axis(4) < 0.5) and not joysticks[0].get_button(0) and not key[pygame.K_SPACE]:
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

                nextPlayer_x = player.move(move.x, 0)
                for x, tileRectRow in enumerate(tileRect):
                    for y, tileRectRowColumn in enumerate(tileRectRow):
                        if nextPlayer_x.colliderect(tileRect[x][y]) and (map[x][y] == GRID_COLOR or map[x][y] == WALL_COLOR or map[x][y] == FLOOR_NEXT_COL):
                            if move.x > 0:  # moving right
                                move.x = 0
                            elif move.x < 0:  # moving left
                                move.x = 0
                            break

                nextPlayer_y = player.move(0, move.y)
                for x, tileRectRow in enumerate(tileRect):
                    for y, tileRectRowColumn in enumerate(tileRectRow):
                        if nextPlayer_y.colliderect(tileRect[x][y]) and (map[x][y] == GRID_COLOR or map[x][y] == WALL_COLOR or map[x][y] == FLOOR_NEXT_COL):
                            if move.y > 0:  # moving down
                                move.y = 0
                            elif move.y < 0:  # moving up
                                move.y = 0
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