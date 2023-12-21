import sys
import pygame
from pygame.locals import QUIT
import os

pygame.init()

screen = pygame.display.set_mode((1152, 648), pygame.RESIZABLE)
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

inGame = False


def button(text, position, size, colour, action=None, *args):
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


def menuEquals(menu_set):
    global menu
    global difficulty
    global typedText
    global ButtonsListOffset
    menu = menu_set
    if menu == 'new':
        difficulty = 'Easy'
        typedText = ''
    ButtonsListOffset = 0


def changeVolume():
    global volume
    volume += 10
    if volume > 100:
        volume = 0
    pygame.mixer.music.set_volume(volume / 100)


def toggleFullscreen():
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


def drawTextBox(text, position, size, colour, borderColour, borderSize, typedText):
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
    global difficulty
    difficulties = {
        'Easy': 'Medium',
        'Medium': 'Difficult',
        'Difficult': 'Very difficult',
        'Very difficult': 'Easy'
    }
    difficulty = difficulties.get(difficulty, 'Easy')


def createFile():
    global fileName
    global difficulty
    global gameSaves
    file = open(f'gamesaves/{typedText}.txt', 'w')
    file.write(f'Difficulty{difficulty}\n')
    file.write(f'firstplaythroughTrue\n')
    for x in range(2):
        file.write(f'None\n')


def loadFile(file):
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


def mainMenu(menu):
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
            buttonsList = [['Fullscreen', toggleFullscreen], [f'Volume: {volume}%', changeVolume]]
        else:
            buttonsList = [['Fullscreen', toggleFullscreen]]
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


def playGame(file):
    global playerPosition
    global fileLine
    global firstTimeRun
    global map
    global player
    global tileRect
    global tile
    if firstTimeRun == True:
        with open(f"gamesaves/{file}", "r") as f:
            fileLine = [line.strip() for line in f]
        firstTimeRun = False
        player = pygame.Rect(screen.get_width() / 2 - (screen.get_width() / 2) / 40,
                             screen.get_height() / 2 - (screen.get_height() / 2) / 40, (screen.get_width() / 2) / 20,
                             (screen.get_height() / 2) / 20)
    if fileLine[1] == "firstplaythroughTrue":
        playerPosition = [0, 0]
        print("Oh.")
        fileLine[2] = playerPosition
        map = []
        for x in range(20):
            map.append([])
            for y in range(20):
                if (x + y) % 2 == 0:
                    map[x].append('blue')
                else:
                    map[x].append('red')
        fileLine[3] = map
        fileLine[1] = 'firstplaythroughFalse'
    backgroundImage = pygame.image.load(
        'Seasonal Tilesets/1 - Grassland/Background parts/_Complete_static_BG_(288 x ''208).png')
    backgroundImage = pygame.transform.scale(backgroundImage, (screen.get_width(), screen.get_height()))
    screen.blit(backgroundImage, (0, 0))
    tileRect = []
    tile = []
    for x, colour in enumerate(map, start=0):
        tileRect.append([])
        tile.append([])
        for y, tileColour in enumerate(colour, start=0):
            if tileColour == 'blue':
                tileRect[x].append(pygame.Rect(((screen.get_width() / 20) * (x)) + playerPosition[0],
                                               ((screen.get_height() / 20) * (y)) + playerPosition[1],
                                               screen.get_width() / 20, screen.get_height() / 20))
                tile[x].append([pygame.draw.rect(screen, (0, 0, 255), tileRect[x][y]), (255, 0, 0)])
            elif tileColour == 'red':
                tileRect[x].append(pygame.Rect(((screen.get_width() / 20) * (x)) + playerPosition[0],
                                               ((screen.get_height() / 20) * (y)) + playerPosition[1],
                                               screen.get_width() / 20, screen.get_height() / 20))
                tile[x].append([pygame.draw.rect(screen, (255, 0, 0), tileRect[x][y]), (255, 0, 0)])
    pygame.draw.rect(screen, (0, 255, 0), player)


def jump():
    global player
    global jumpCount
    global playerPosition
    global jumping
    if jumpCount >= -10:
        neg = 1
        if jumpCount < 0:
            neg = -1
        player = player.move(0, -(jumpCount ** 2 * 0.1 * neg))
        print('working')
        jumpCount -= 1
    else:
        jumping = False
        jumpCount = 10
        player = pygame.Rect(screen.get_width() / 2 - (screen.get_width() / 2) / 40,
                             screen.get_height() / 2 - (screen.get_height() / 2) / 40, (screen.get_width() / 2) / 20,
                             (screen.get_height() / 2) / 20)


playerPosition = []
jumping = False

while True:
    pygame.display.update()

    for event in pygame.event.get():
        if event.type == QUIT:
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
            if inGame == True:
                if event.key == pygame.K_ESCAPE:
                    with open(currentFile, 'w') as file:
                        file.writelines(str(fileLine))
                    pygame.quit()
                if event.key == pygame.K_SPACE:
                    if jumping == False:
                        jumping = True
                        jumpCount = 10
            if event.key == pygame.K_F11:
                toggleFullscreen()

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
        key = pygame.key.get_pressed()
        up = key[pygame.K_w] or key[pygame.K_UP]
        down = key[pygame.K_s] or key[pygame.K_DOWN]
        left = key[pygame.K_a] or key[pygame.K_LEFT]
        right = key[pygame.K_d] or key[pygame.K_RIGHT]

        move = pygame.math.Vector2(right - left, down - up)
        if move.length_squared() > 0:
            move.scale_to_length(screen.get_width() / 1000)
            playerPosition[0] -= move.x
            playerPosition[1] -= move.y

            for x, tileRectRow in enumerate(tileRect):
                for y, tileRectRowColumn in enumerate(tileRectRow):
                    if tile[x][y][1] == (255, 0, 0) and player.colliderect(tile[x][y][0]):
                        playerPosition[0] += move.x
                        playerPosition[1] += move.y

        for x, tileRectRow in enumerate(tileRect):
            for y, tileRectRowColumn in enumerate(tileRectRow):
                if tile[x][y][1] == (255, 0, 0) and player.colliderect(tile[x][y][0]):
                    jumping = False

        if jumping:
            jump()

    if displayAudioError == True and audioMessagePressed == False:
        audioErrorText = font.render("Audio Error. Press to dismiss.", True, (255, 0, 0))
        audioErrorTextRect = audioErrorText.get_rect(center=(screen.get_width() / 2, screen.get_height() - 30))
        screen.blit(audioErrorText, audioErrorTextRect)
        if pygame.mouse.get_pressed()[0] and audioErrorTextRect.collidepoint(pygame.mouse.get_pos()):
            audioMessagePressed = True

# To do:
# watch https://www.youtube.com/watch?v=GMBqjxcKogA - video on how to make a menu in pygame
