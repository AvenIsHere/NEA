import pygame

class WorldGridPoint:
    colour: pygame.Color
    collision: bool

class World:
    grid: list[list[WorldGridPoint]]

