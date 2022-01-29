import os

from ...Abstracts import AbstractModule
from ...Classes.Listener import ListenData


class CommandModule(AbstractModule):

    @staticmethod
    def get_identifier() -> str:
        return "command"

    @staticmethod
    def _get_config_file() -> str:
        return os.path.dirname(os.path.realpath(__file__)) + "/module.txt"

    def process_unrecognized_command(self, language: str, text: str, listen_data: ListenData) -> None:
        print(text)