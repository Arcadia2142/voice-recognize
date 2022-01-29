from abc import ABC

import os
from ...Abstracts import AbstractCommand
from ...Classes.Listener import ListenData

from ...Modules.CommandModule.CommandModule import CommandModule
from ...Classes.Utils import Utils


class FocusCommands(AbstractCommand, ABC):
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

    def process_command(self, action: str, language: str, reg_exp_args: list, listen_data: ListenData) -> None:
        if action == self.ACTION_CHANGE_FOCUS:
            self.action_change_focus(reg_exp_args[0], language)
        elif action == self.ACTION_CLOSE_WINDOW:
            self.action_close_window(language)

    def action_change_focus(self, window_name: str, language: str) -> None:
        print("Switching on window " + window_name)

        # Type text to window.
        Utils.run_shell_command(
            self._get_shell_command(self.ACTION_CHANGE_FOCUS, 'xdotool search "${WINDOW}" windowactivate'),
            {'WINDOW': window_name}
        )

    def action_close_window(self, language: str) -> None:
        print("Closing window")

        # Type text to window.
        Utils.run_shell_command(
            self._get_shell_command(self.ACTION_CLOSE_WINDOW, 'xdotool windowkill `xdotool getactivewindow`')
        )
