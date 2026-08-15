from pathlib import Path
from typing import Callable, Any

import pygame
import tkinter as tk
from tkinter import filedialog

import consts
from file import GameFile, load_save, new_save
from game import Difficulty

root = tk.Tk()
root.withdraw()

class Menu:
    title: str
    button_list: list[Button | TextBox]

    def __init__(self, title: str, button_list: list[Button | TextBox]):
        self.title = title
        self.button_list = button_list

    def render(self, screen: pygame.Surface) -> None:
        menu_name = pygame.font.Font(None, 32).render(self.title, True, (255, 255, 255))
        menu_name_rect = menu_name.get_rect(center=(consts.screen_width / 2, consts.screen_height / 6))
        screen.blit(menu_name, menu_name_rect)
        for button in self.button_list:
            button.render(screen)

    def handle_input(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN:
            for button in self.button_list:
                if button.rect.collidepoint(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1]):
                    button.on_click()
                else:
                    if isinstance(button, TextBox): button.active = False
        if event.type == pygame.KEYDOWN:
            for button in self.button_list:
                if isinstance(button, TextBox) and button.active:
                    if event.type == pygame.K_BACKSPACE:
                        button.set_text(button.text[:-1])
                        return
                    button.set_text(button.text + event.unicode)
                    

class TextBox:
    text: str
    placeholder_text: str
    colour: tuple[int, int, int]
    border_colour: tuple[int, int, int]
    border_size: int
    position: tuple[int, int]
    rect: pygame.Rect

    active: bool = False

    def __init__(self, text: str, placeholder_text: str, colour: tuple[int, int, int], border_colour: tuple[int, int, int], border_size: int, position: tuple[int, int]):
        self.text = text
        self.placeholder_text = placeholder_text
        self.colour = colour
        self.border_colour = border_colour
        self.border_size = border_size
        self.position = position
        self.rect = pygame.font.Font(None, 32).render(self.placeholder_text, True, (0, 0, 0)).get_rect(center=self.position)

    def render(self, screen: pygame.Surface) -> None:
        if self.text == "":
            rendered_text = pygame.font.Font(None, 32).render(self.placeholder_text, True, (0, 0, 0))
        else:
            rendered_text = pygame.font.Font(None, 32).render(self.text, True, (0, 0, 0))
        text_rect = rendered_text.get_rect(center=self.position)
        pygame.draw.rect(screen, self.colour, text_rect)
        pygame.draw.rect(screen, self.border_colour, (
            text_rect.x - self.border_size, text_rect.y - self.border_size, text_rect.width + self.border_size * 2,
            text_rect.height + self.border_size * 2), self.border_size)
        screen.blit(rendered_text, text_rect)

    def set_text(self, text: str) -> None:
        self.text = text
        self.rect = pygame.font.Font(None, 32).render(self.text, True, (0, 0, 0)).get_rect(center=self.position)

    def on_click(self) -> None:
        self.active = True

class Button:
    text: str
    position: tuple[int, int]
    size: tuple[float, float]
    colour: tuple[int, int, int]
    action: Callable[..., Any]

    rect: pygame.Rect

    def __init__(self, text: str, position: tuple[int, int], size: tuple[float, float], colour: tuple[int, int, int], action: Callable[..., Any]):
        self.text = text
        self.position = position
        self.size = size
        self.colour = colour
        self.action = action
        self.rect = pygame.Rect(self.position[0] - (self.size[0] / 2), self.position[1] - (self.size[1] / 2),
                                self.size[0],
                                self.size[1])

    def render(self, screen: pygame.Surface) -> None:
         # creates a pygame Rect for the button
        pygame.draw.rect(screen, self.colour, self.rect)  # draws that rect onto the screen
        rendered_text = pygame.font.Font(None, 32).render(self.text, True, (0, 0, 0))  # creates the text to write on the screen
        textRect = rendered_text.get_rect(
            center=self.rect.center)  # creates a pygame rect for the text on the screen in the middle of the button
        screen.blit(rendered_text, textRect)  # draws the text on the screen

    def on_click(self) -> None:
        if self.action is not None: self.action()

    @classmethod
    def inline_button(cls, text: str, position: tuple[int, int], size: tuple[float, float], colour: tuple[int, int, int], action: Callable[..., Any], screen: pygame.Surface) -> None:
        button = Button(text, position, size, colour, action)
        button.render(screen)
        if button.rect.collidepoint(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1]):
            button.on_click()


class MainMenu:
    menus: dict[str, Menu]
    menu: Menu

    difficulty_selected: Difficulty = Difficulty.Easy

    file_opened: GameFile | None = None

    def def_menus(self) -> None:
        self.menus: dict[str, Menu] = {
            "Main": Menu("Main Menu", [
                Button("Play", (100, 100), (100, 50), (20, 20, 20), lambda: self.set_menu("Play")),
                Button("Settings", (100, 200), (100, 50), (20, 20, 20), lambda: self.set_menu("Settings")),
                Button("Quit", (100, 300), (100, 50), (20, 20, 20), lambda: quit())
            ]),
            "Play": Menu("Play", [
                Button("New Game", (100, 100), (100, 50), (20, 20, 20), lambda: self.set_menu("New")),
                Button("Open File", (100, 200), (100, 50), (20, 20, 20), lambda: load_save(Path(filedialog.askopenfilename()))),
                Button("Back", (100, 300), (100, 50), (20, 20, 20), lambda: self.set_menu("Main"))
            ]),
            "New": Menu("New Game", [
                TextBox("", "Enter the file name here", (20, 20, 20), (40, 40, 40), 5, (100, 100)),
                Button(f"Difficulty: {self.difficulty_selected}", (100, 200), (100, 50), (20, 20, 20), lambda: self.cycle_difficulty()),
                Button("Create Game", (100, 200), (100, 50), (20, 20, 20), lambda: setattr(self, 'file_opened', new_save(Path(filedialog.asksaveasfilename()), self.difficulty_selected))),
                Button("Back", (100, 300), (100, 50), (20, 20, 20), lambda: self.set_menu("Play"))
            ]),
            "Settings": Menu("Settings", [
                Button("Back", (100, 300), (100, 50), (20, 20, 20), lambda: self.set_menu("Main"))
            ])
        }

    def set_menu(self, menu: str) -> None:
        self.menu = self.menus[menu]

    def __init__(self) -> None:
        self.def_menus()
        self.set_menu("Main")

    def render(self, screen: pygame.Surface) -> None:
        self.menu.render(screen)

    def cycle_difficulty(self) -> None:
        difficulties = list(Difficulty)
        current_index = difficulties.index(self.difficulty_selected)
        next_index = (current_index + 1) % len(difficulties)
        self.difficulty_selected = difficulties[next_index]

    def handle_input(self, event: pygame.event.Event) -> None:
        self.menu.handle_input(event)

    def get_game(self) -> GameFile | None:
        return self.file_opened