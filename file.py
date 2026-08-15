# file.py

from pathlib import Path

import jsonpickle  # type: ignore[import-untyped]

from game import GameState, Difficulty


class GameFile:
    file_location: Path
    game_state: GameState

    def __init__(self, file_location: Path, game_state: GameState):
        self.game_state = game_state
        self.file_location = file_location

    @classmethod
    def new_game(cls, file_location: Path, difficulty: Difficulty) -> GameFile:
        return GameFile(file_location, GameState.new_game(difficulty))


def new_save(file_location: Path, difficulty: Difficulty) -> GameFile:
    game = GameFile.new_game(file_location, difficulty)
    with open(file_location, 'w') as file:
        file.write(jsonpickle.encode(game.game_state))
    return game

def load_save(file_location: Path) -> GameFile:
    with open(file_location, 'r') as file:
        game = jsonpickle.decode(file.read())
    if not isinstance(game, GameState): raise ValueError("This file is not a valid save!")
    game_file = GameFile(file_location, game)
    return game_file

def save_game(game_file: GameFile) -> None:
    with open(game_file.file_location, 'w') as file:
        file.write(jsonpickle.encode(game_file.game_state))