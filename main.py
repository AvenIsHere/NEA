import sys

import pygame
from pygame.locals import QUIT
import os

pygame.init()

DISPLAYSURF = pygame.display.set_mode((400, 300), pygame.RESIZABLE)
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

menu = 'main'
ButtonsListOffset = 0
volume = 100
mouseNotUp = False

def button(text, position, size, colour, action=None, *args):
  global mouseNotUp
  button_rect = pygame.Rect(position[0] - (size[0]/2), position[1] - (size[1]/2), size[0], size[1])
  pygame.draw.rect(DISPLAYSURF, colour, button_rect)
  text = font.render(text, True, (0, 0, 0))
  textRect = text.get_rect(center=button_rect.center)
  DISPLAYSURF.blit(text, textRect)
  if button_rect.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0] and mouseNotUp == False and action != None:
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
  if isFullscreen == False:
    pygame.display.set_mode((pygame.display.list_modes()[0][0], pygame.display.list_modes()[0][1]))
    pygame.display.toggle_fullscreen()
    isFullscreen = True
  else:
    pygame.display.toggle_fullscreen()
    pygame.display.set_mode((400, 300), pygame.RESIZABLE)
    isFullscreen = False

def drawTextBox(text, position, size, colour, borderColour, borderSize, typedText):
  if typedText == '':
    text = font.render(text, True, (0, 0, 0))
    textRect = text.get_rect(center=position)
  if typedText != '':
    text = font.render(typedText, True, (0, 0, 0))
    textRect = text.get_rect(center=position)
  pygame.draw.rect(DISPLAYSURF, colour, textRect)
  pygame.draw.rect(DISPLAYSURF, borderColour, (textRect.x - borderSize, textRect.y - borderSize, textRect.width + borderSize * 2, textRect.height + borderSize * 2), borderSize)
  DISPLAYSURF.blit(text, textRect)

def setDifficulty():
  global difficulty
  difficulties = {
  'Easy': 'Medium',
  'Medium': 'Difficult',
  'Difficult': 'Very difficult',
  'Very difficult': 'Easy'
  }
  difficulty = difficulties.get(difficulty, 'Easy')

def createGame():
  global fileName
  global difficulty
  global gameSaves
  file = open(f'gamesaves/{typedText}.txt', 'w')
  file.write(f'Difficulty: {difficulty}\n')

def loadFile(file):
  print(f'load {file}')

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
  menuNameTextRect = menuNameText.get_rect(center=(DISPLAYSURF.get_width() / 2, DISPLAYSURF.get_height() / 6))
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
        buttonsList.append([savefile[:len(savefile)-4], loadFile, savefile])
    if len(buttonsList) < 4:
      button('Back',(menuNameTextRect.centerx, menuNameTextRect.centery + 200), (150, 37.5), (100, 100, 100), menuEquals, 'main')
    else:
      buttonsList.append(['Back', menuEquals, 'main'])
  elif menu == 'new':
    drawTextBox(f'Enter a name for your new game', (menuNameTextRect.centerx, menuNameTextRect.centery + 50), (150, 37.5), (100, 100, 100), (0, 0, 0), 2, typedText)
    buttonsList = [None, [f'Difficulty: {difficulty}', setDifficulty], ['Start', createGame], ['Back', menuEquals, 'play']]
  if menu !="main" and menu !='play' and menu !='new':
      button('Back', (menuNameTextRect.centerx, menuNameTextRect.centery + 200), (150, 37.5), (100, 100, 100), menuEquals, 'main')
  for i in range(len(buttonsList)):
    if buttonsList[i] == None:
      pass
    elif len(buttonsList[i]) == 1:
      button(buttonsList[i][0], (menuNameTextRect.centerx, menuNameTextRect.centery + ButtonsListOffset + (50 + (i * 50))), (150, 37.5),(100, 100, 100))
    elif len(buttonsList[i]) == 2:
      button(buttonsList[i][0],(menuNameTextRect.centerx, menuNameTextRect.centery + ButtonsListOffset + (50 + (i * 50))), (150, 37.5), (100, 100, 100), buttonsList[i][1])
    elif len(buttonsList[i]) == 3:
      button(buttonsList[i][0],(menuNameTextRect.centerx, menuNameTextRect.centery + ButtonsListOffset + (50 + (i * 50))), (150, 37.5), (100, 100, 100), buttonsList[i][1], buttonsList[i][2])
  TextBackground = pygame.Rect(0, 0, DISPLAYSURF.get_width(), menuNameTextRect.centery + 15)
  pygame.draw.rect(DISPLAYSURF, (20, 20, 20), TextBackground)
  DISPLAYSURF.blit(menuNameText, menuNameTextRect)


while True:
  pygame.display.update()

  for event in pygame.event.get():
    if event.type == QUIT:
      pygame.quit()
    if event.type == pygame.MOUSEBUTTONUP:
      mouseNotUp = False
    if event.type == pygame.KEYDOWN:
      if menu == 'new':
        if event.key == pygame.K_BACKSPACE:
          typedText = typedText[:-1]
        else:
          typedText += event.unicode
    if event.type == pygame.MOUSEWHEEL:
      if menu == 'play' and menuNameTextRect.centery + (50 + ((len(buttonsList) - 1) * 50)) > DISPLAYSURF.get_height():
        ButtonsListOffset += event.y * 10
        if ButtonsListOffset > 0:
          ButtonsListOffset = 0
        if ButtonsListOffset <

  DISPLAYSURF.fill((20,20,20))

  mainMenu(menu)

  if displayAudioError == True and audioMessagePressed == False:
    audioErrorText = font.render("Audio Error. Press to dismiss.", True, (255, 0, 0))
    audioErrorTextRect = audioErrorText.get_rect(center=(DISPLAYSURF.get_width() / 2, DISPLAYSURF.get_height() - 30))
    DISPLAYSURF.blit(audioErrorText, audioErrorTextRect)
    if pygame.mouse.get_pressed()[0] and audioErrorTextRect.collidepoint(pygame.mouse.get_pos()):
      audioMessagePressed = True

# To do:
# watch https://www.youtube.com/watch?v=GMBqjxcKogA - video on how to make a menu in pygame