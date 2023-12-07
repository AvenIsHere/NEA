import sys

import pygame
from pygame.locals import QUIT

pygame.init()

DISPLAYSURF = pygame.display.set_mode((400, 300), pygame.SCALED, pygame.RESIZABLE)
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
  

menu = 'main'
volume = 100
mouseNotUp = False

def button(text, position, size, colour, action=None, actionParameters1=None, actionPerameters2=None):
  global mouseNotUp
  button_rect = pygame.Rect(position[0] - (size[0]/2), position[1] - (size[1]/2), size[0], size[1])
  pygame.draw.rect(DISPLAYSURF, colour, button_rect)
  text = font.render(text, True, (0, 0, 0))
  textRect = text.get_rect(center=button_rect.center)
  DISPLAYSURF.blit(text, textRect)
  if button_rect.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0] and mouseNotUp == False and action != None:
    if actionParameters1 != None and actionPerameters2 != None:
      action(actionParameters1, actionPerameters2)
    elif actionParameters1 != None:
      action(actionParameters1)
    else:
      action()
    mouseNotUp = True

def menuEquals(menu_set):
  global menu
  menu = menu_set

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
    pygame.display.set_mode((400, 300), pygame.SCALED, pygame.RESIZABLE)
    pygame.display.toggle_fullscreen()
    isFullscreen = False

def mainMenu(menu):
  global volume
  if menu == 'main':
    menuNameText = font.render("Game Name", True, (255, 255, 255))
  elif menu == 'settings':
    menuNameText = font.render("Settings", True, (255, 255, 255))
  menuNameTextRect = menuNameText.get_rect(center=(DISPLAYSURF.get_width() / 2, DISPLAYSURF.get_height() / 6))
  DISPLAYSURF.blit(menuNameText, menuNameTextRect)
  if menu == 'main':
    button('Play', (menuNameTextRect.centerx, menuNameTextRect.centery + 50), (150, 37.5), (100, 100, 100))
    button('Settings', (menuNameTextRect.centerx, menuNameTextRect.centery + 100), (150, 37.5), (100, 100, 100), menuEquals, 'settings')
    button('Leaderboard', (menuNameTextRect.centerx, menuNameTextRect.centery + 150), (150, 37.5), (100, 100, 100))
    button('Quit', (menuNameTextRect.centerx, menuNameTextRect.centery + 200), (150, 37.5), (100, 100, 100), pygame.quit)
  if menu == 'settings':
    button('Fullscreen', (menuNameTextRect.centerx, menuNameTextRect.centery + 50), (150, 37.5), (100, 100, 100), toggleFullscreen)
    if not displayAudioError:
      button(f'volume: {volume}%' , (menuNameTextRect.centerx, menuNameTextRect.centery + 100), (150, 37.5), (100, 100, 100), changeVolume)
      button('Back', (menuNameTextRect.centerx, menuNameTextRect.centery + 150), (150, 37.5), (100, 100, 100), menuEquals, 'main')
    else:
      button('Back', (menuNameTextRect.centerx, menuNameTextRect.centery + 100), (150, 37.5), (100, 100, 100), menuEquals, 'main')


while True:
  for event in pygame.event.get():
    if event.type == QUIT:
      pygame.quit()
      sys.exit()
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
  
  pygame.display.update()