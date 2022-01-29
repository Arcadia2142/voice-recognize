from abc import ABC

import os, subprocess

from ...Abstracts import AbstractCommand
from ...Classes.Listener import ListenData
from ...Modules.RepairModule.RepairModule import RepairModule


class RepairCommands(AbstractCommand, ABC):
    ACTION_REPAIR = "repair"

    @staticmethod
    def get_modules() -> list:
        return [RepairModule.get_identifier()]

    @staticmethod
    def _get_commands_file() -> str:
        return os.path.dirname(os.path.realpath(__file__)) + "/commands.txt"

    def process_command(self, command: str, language: str, reg_exp_args: list, listen_data: ListenData) -> None:
        if command == self.ACTION_REPAIR:
            self.command_repair()

    def command_repair(self) -> None:
        last_messages = self._resolver.get_last_messages()
        invalid_command = last_messages[-2]

        subprocess.call(
            'kwrite "$FILE"',
            shell=True,
            stdout=subprocess.PIPE,
            env={
                "DISPLAY": os.getenv('DISPLAY'),
                "LANG": os.getenv('LANG'),
                "FILE": invalid_command.csv_file_path
            }
        )

