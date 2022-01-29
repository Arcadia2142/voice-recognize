from abc import ABC

import os
from ...Abstracts import AbstractCommand, ModuleDict
from ...Classes.Listener import ListenData


class ModulesChange(AbstractCommand, ABC):
    ACTION_CHANGE_MODULE = "changeModule"

    @staticmethod
    def use_for_all_modules() -> bool:
        return True

    @staticmethod
    def _get_commands_file() -> str:
        return os.path.dirname(os.path.realpath(__file__)) + "/commands.txt"

    def process_command(self, command: str, language: str, reg_exp_args: list, listen_data: ListenData) -> None:
        if command == self.ACTION_CHANGE_MODULE:
            self.command_change_module(reg_exp_args[0], language)

    def command_change_module(self, module_name: str, language: str) -> None:
        modules: ModuleDict = self._resolver.get_modules()

        for module_identifier in modules:
            module = modules[module_identifier]
            if module.get_name(language) == module_name:
                print("Module set to " + module_name)
                self._resolver.set_active_module(module)
                return

        print("Unrecognized module " + module_name)
