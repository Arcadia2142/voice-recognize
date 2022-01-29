from abc import ABC

import os
from ...Abstracts import AbstractCommand
from ...Classes.Listener import ListenData

from ...Modules.CommandModule.CommandModule import CommandModule


class FocusCommand(AbstractCommand, ABC):
    ACTION_CHANGE_FOCUS = "changeFocus"
    ACTION_CLOSE_WINDOW = "closeWindow"

    @staticmethod
    def get_modules() -> list:
        return [
            CommandModule.get_identifier()
        ]

    @staticmethod
    def _get_commands_file() -> str:
        return os.path.dirname(os.path.realpath(__file__)) + "/commands.txt"

    def process_command(self, command: str, language: str, reg_exp_args: list, listen_data: ListenData) -> None:
        if command == self.ACTION_CHANGE_FOCUS:
            self.command_change_focus(reg_exp_args[0], language)
        elif command == self.ACTION_CLOSE_WINDOW:
            self.command_close_window(language)

    def command_change_focus(self, window_name: str, language: str) -> None:
        print("Switching on window " + window_name)

        # Type text to window.
        self._run_shell_command('xdotool search "${TEXT}" windowactivate', {'TEXT': window_name})

    def command_close_window(self, language: str) -> None:
        print("Closing window")

        # Type text to window.
        self._run_shell_command('xdotool windowkill `xdotool getactivewindow`')
