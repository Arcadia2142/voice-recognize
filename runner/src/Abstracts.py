from __future__ import annotations

from abc import abstractmethod
from configparser import ConfigParser

from .Classes.Listener import ListenData

from typing import Dict, List, Optional

import subprocess, os


# Empty classes def.
class AbstractCommand:
    pass


class AbstractModule:
    pass


# Types def.
CommandList = List[AbstractCommand]
CommandDictList = Dict[str, CommandList]
ModuleDict = Dict[str, AbstractModule]


class AbstractCommand(object):
    CONFIG_POSTFIX_REGEXP = 'regexp'
    CONFIG_POSTFIX_COMMAND = 'command'

    def __init__(self, resolver: AbstractResolver) -> None:
        super().__init__()
        self._resolver = resolver

        config = ConfigParser()
        config.optionxform = str
        config.read(self._get_commands_file())
        self._commands_map = self._parse_config(config)

    @abstractmethod
    # Process command by speach.
    def process_command(self, command: str, language: str, reg_exp_args: list, listen_data: ListenData) -> None:
        pass

    @staticmethod
    @abstractmethod
    # Get file with commands configuration.
    def _get_commands_file() -> str:
        pass

    @staticmethod
    # Get modules (modes) where can be used this command.
    def get_modules() -> list:
        return []

    @staticmethod
    def get_identifier() -> str:
        return str(__class__)

    @staticmethod
    # Can use this command in all modes?
    def use_for_all_modules() -> bool:
        return False

    # Get map commandName => regexp
    def get_commands_req_exps_map(self, language: str) -> dict[str, str]:
        commands_reg_exps = {}

        for command in self._commands_map[language]:
            commands_reg_exps[command] = self._commands_map[language][command][self.CONFIG_POSTFIX_REGEXP]

        return commands_reg_exps

    @staticmethod
    def _parse_config(config: ConfigParser) -> dict:
        commands_map = {}

        for language in config.sections():
            commands_map[language] = {}

            for command_data in config.options(language):
                command_parts = command_data.split('.')
                command_name = command_parts[0]
                command_postfix = command_parts[1]

                if command_name not in commands_map[language]:
                    commands_map[language][command_name] = {}

                commands_map[language][command_name][command_postfix] = config.get(language, command_data)

        return commands_map

    # Call command in shell.
    def _run_shell_command(self, command: str, env=None):
        enviroment = {
            "DISPLAY": os.getenv('DISPLAY'),
            "LANG": os.getenv('LANG')
        }

        if env is not None:
            for env_key in env:
                enviroment[env_key] = env[env_key]

        subprocess.call(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            env=enviroment
        )



class AbstractResolver(object):

    # Get all exist modules.
    @abstractmethod
    def get_modules(self) -> ModuleDict:
        pass

    # Add module to resolver.
    @abstractmethod
    def add_module(self, module: AbstractModule) -> AbstractResolver:
        pass

    # Add command to resolver.
    @abstractmethod
    def add_command(self, command: AbstractCommand) -> AbstractResolver:
        pass

    # Set active module.
    @abstractmethod
    def set_active_module(self, module: AbstractModule) -> AbstractResolver:
        pass

    # Get all command, can be filtered by active module.
    @abstractmethod
    def get_all_commands(self, filter_by_module: bool = False) -> CommandList:
        pass

    # Get last messages.
    @abstractmethod
    def get_last_messages(self, module_filter: Optional[str] = None) -> list[ListenData]:
        pass


class AbstractModule(object):
    MODULE_NAME = "name"

    def __init__(self, resolver: AbstractResolver) -> None:
        self._resolver: AbstractResolver = resolver

        config = ConfigParser()
        config.optionxform = str
        config.read(self._get_config_file())
        self._config: dict[str, dict[str, str]] = self._parse_config(config)

    @staticmethod
    @abstractmethod
    def get_identifier() -> str:
        pass

    @staticmethod
    @abstractmethod
    # Get file with commands configuration.
    def _get_config_file() -> str:
        pass

    @abstractmethod
    def get_name(self, language: str) -> str:
        return self._config[language][self.MODULE_NAME]

    @staticmethod
    def _parse_config(config: ConfigParser) -> dict:
        config_map = {}

        for language in config.sections():
            config_map[language] = {}

            for option in config.options(language):
                config_map[language][option] = config.get(language, option)

        return config_map

    # Run command in module.
    def process_command(self, command: AbstractCommand, command_name: str, language: str, reg_exp_args: list, listen_data: ListenData) -> None:
        command.process_command(command_name, language, reg_exp_args, listen_data)

    # Run unrecognized command.
    def process_unrecognized_command(self, language: str, text: str, listen_data: ListenData) -> None:
        pass

