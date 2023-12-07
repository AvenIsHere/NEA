import sys

import pygame
from pygame.locals import QUIT

pygame.init()
DISPLAYSURF = pygame.display.set_mode((400, 300), pygame.RESIZABLE)
pygame.display.set_caption('NEA')
font = pygame.font.Font(None, 32)

menu = True

def button(text, position, size, colour, action=None):
  button_rect = pygame.Rect(position[0] - (size[0]/2), position[1] - (size[1]/2), size[0], size[1])
  pygame.draw.rect(DISPLAYSURF, colour, button_rect)
  text = font.render(text, True, (0, 0, 0))
  textRect = text.get_rect(center=button_rect.center)
  DISPLAYSURF.blit(text, textRect)

def mainMenu():
  GameNameText = font.render("Game Name", True, (255, 255, 255))
  GameNameTextRect = GameNameText.get_rect(center=(DISPLAYSURF.get_width() / 2, DISPLAYSURF.get_height() / 6))
  DISPLAYSURF.blit(GameNameText, GameNameTextRect)
  button('Play', (GameNameTextRect.centerx, GameNameTextRect.centery + 100), (100, 50), (100, 100, 100))
  

while True:
  for event in pygame.event.get():
    if event.type == QUIT:
      pygame.quit()
      sys.exit()

  DISPLAYSURF.fill((20,20,20))

  if menu == True:
    mainMenu()
  
  pygame.display.update() 