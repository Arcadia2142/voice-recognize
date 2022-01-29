import os, subprocess

from ...Abstracts import AbstractModule, AbstractCommand, AbstractResolver
from ...Classes.Listener import ListenData
from ...Commands.TypeCommands.TypeCommands import TypeCommands


class TextModule(AbstractModule):

    def __init__(self, resolver: AbstractResolver, type_commands: TypeCommands) -> None:
        super().__init__(resolver)
        self._type_commands = type_commands

    @staticmethod
    def get_identifier() -> str:
        return "text"

    @staticmethod
    def _get_config_file() -> str:
        return os.path.dirname(os.path.realpath(__file__)) + "/module.txt"

    def process_unrecognized_command(self, language: str, text: str, listen_data: ListenData) -> None:
        self._type_commands.action_type(text)