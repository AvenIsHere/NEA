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
  global fileName
  global menu
  global difficulty
  menu = menu_set
  if menu == 'play':
    try:
      fileName = f'game{len(os.listdir(gamesaves))+1}'
      difficulty = 'Easy'
    except:
      fileName = 'game0'
      difficulty = 'Easy'

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

def setDifficulty(file):
  global difficulty
  if difficulty == 'Easy':
    difficulty = "Medium"
  elif difficulty == 'Medium':
    difficulty = "Difficult"
  elif difficulty == 'Difficult':
    difficulty = 'Very difficult'
  else:
    difficulty = 'Easy'
def mainMenu(menu):
  global volume
  if menu == 'main' or menu == 'play':
    menuNameText = font.render("Game Name", True, (255, 255, 255))
  elif menu == 'settings':
    menuNameText = font.render("Settings", True, (255, 255, 255))
  elif menu == 'new':
    menuNameText = font.render("New Game", True, (255, 255, 255))
  menuNameTextRect = menuNameText.get_rect(center=(DISPLAYSURF.get_width() / 2, DISPLAYSURF.get_height() / 6))
  DISPLAYSURF.blit(menuNameText, menuNameTextRect)
  if menu == 'main':
    buttonsList = [['Play', menuEquals, 'play'], ['Settings', menuEquals, 'settings'], ['Quit', pygame.quit]]
  elif menu == 'settings':
    if not displayAudioError:
      buttonsList = [['Fullscreen', toggleFullscreen], [f'Volume: {volume}%', changeVolume]]
    else:
      buttonsList = [['Fullscreen', toggleFullscreen]]
  elif menu == 'play':
    buttonsList = [['New Game', menuEquals, 'new']]
    for x in range(len(gameSaves)):
      buttonsList.append(gameSaves[x])
    if len(buttonsList) < 4:
      button('Back',(menuNameTextRect.centerx, menuNameTextRect.centery + 200), (150, 37.5), (100, 100, 100), menuEquals, 'main')
    else:
      buttonsList.append('Back', menuEquals, 'main')
  elif menu == 'new':
    buttonsList = [None, [f'Difficulty: {difficulty}', setDifficulty, fileName], None, ['Back', menuEquals, 'play']]
  if menu !="main" and menu !='play' and menu !='new':
      button('Back', (menuNameTextRect.centerx, menuNameTextRect.centery + 200), (150, 37.5), (100, 100, 100), menuEquals, 'main')
  for i in range(len(buttonsList)):
    try:
      button(buttonsList[i][0],(menuNameTextRect.centerx, menuNameTextRect.centery + (50 + (i * 50))), (150, 37.5), (100, 100, 100), buttonsList[i][1], buttonsList[i][2])
    except IndexError:
      try:
        button(buttonsList[i][0],(menuNameTextRect.centerx, menuNameTextRect.centery + (50 + (i * 50))), (150, 37.5), (100, 100, 100), buttonsList[i][1])
      except IndexError:
        button(buttonsList[i][0], (menuNameTextRect.centerx, menuNameTextRect.centery + (50 + (i * 50))), (150, 37.5),(100, 100, 100))
    except TypeError:
      pass


while True:
  pygame.display.update()

  for event in pygame.event.get():
    if event.type == QUIT:
      pygame.quit()
    if event.type == pygame.MOUSEBUTTONUP:
      mouseNotUp = False

  DISPLAYSURF.fill((20,20,20))

  mainMenu(menu)

  if displayAudioError == True and audioMessagePressed == False:
    audioErrorText = font.render("Audio Error. Press to dismiss.", True, (255, 0, 0))
    audioErrorTextRect = audioErrorText.get_rect(center=(DISPLAYSURF.get_width() / 2, DISPLAYSURF.get_height() - 30))
    DISPLAYSURF.blit(audioErrorText, audioErrorTextRect)
    if pygame.mouse.get_pressed()[0] and audioErrorTextRect.collidepoint(pygame.mouse.get_pos()):
      audioMessagePressed = True