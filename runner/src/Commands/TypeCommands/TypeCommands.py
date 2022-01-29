import os

from ...Abstracts import AbstractCommand
from ...Classes.Listener import ListenData


class TypeCommands(AbstractCommand):
    ACTION_TYPE = 'type'
    ACTION_ENTER = 'enter'

    @staticmethod
    def _get_commands_file() -> str:
        return os.path.dirname(os.path.realpath(__file__)) + "/commands.txt"

    @staticmethod
    def use_for_all_modules() -> bool:
        return True

    def process_command(self, action: str, language: str, reg_exp_args: list, listen_data: ListenData) -> None:
        if action == self.ACTION_TYPE:
            self.action_type(reg_exp_args[0])
        elif action == self.ACTION_ENTER:
            self.action_enter()

    # Type text by keyboard.
    def action_type(self, text: str) -> None:
        print('Typing: ' + text)

        # Type text to window.
        self._run_shell_command(
            self._get_shell_command(self.ACTION_TYPE, 'xdotool type "${TEXT}"'),
            {"TEXT": text}
        )

    # Type text by keyboard.
    def action_enter(self) -> None:
        print('Using enter')

        # Type text to window.
        self._run_shell_command(
            self._get_shell_command(self.ACTION_ENTER, 'xdotool key Return')
        )
