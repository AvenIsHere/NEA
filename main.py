import sys

import pygame
from pygame.locals import QUIT

pygame.init()
DISPLAYSURF = pygame.display.set_mode((400, 300), pygame.RESIZABLE)
pygame.display.set_caption('NEA')
font = pygame.font.Font(None, 32)

menu = 'main'

def button(text, position, size, colour, action=None, actionParameters=None):
  button_rect = pygame.Rect(position[0] - (size[0]/2), position[1] - (size[1]/2), size[0], size[1])
  pygame.draw.rect(DISPLAYSURF, colour, button_rect)
  text = font.render(text, True, (0, 0, 0))
  textRect = text.get_rect(center=button_rect.center)
  DISPLAYSURF.blit(text, textRect)
  if button_rect.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0] and action != None:
    if actionParameters != None:
      action(actionParameters)
    else:
      action()

def menuEquals(menu_set):
  global menu
  menu = menu_set

def mainMenu(menu):
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
    button('Fullscreen', (menuNameTextRect.centerx, menuNameTextRect.centery + 50), (150, 37.5), (100, 100, 100), pygame.display.toggle_fullscreen)
    button('Back', (menuNameTextRect.centerx, menuNameTextRect.centery + 100), (150, 37.5), (100, 100, 100), menuEquals, 'main')


while True:
  for event in pygame.event.get():
    if event.type == QUIT:
      pygame.quit()
      sys.exit()

  DISPLAYSURF.fill((20,20,20))

  mainMenu(menu)
  
  pygame.display.update() 