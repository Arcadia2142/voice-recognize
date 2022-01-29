from __future__ import annotations

import re
from typing import Optional

from multiprocessing.connection import Connection
from collections import deque

from .Listener import ListenData
from ..Abstracts import AbstractResolver, AbstractCommand, AbstractModule, CommandList, CommandDictList, ModuleDict
from .MessageQueue import MessageQueue


class Resolver(AbstractResolver):
    def __init__(self, queue_pipe: Connection, master_pipe: Connection) -> None:
        self._queue_pipe = queue_pipe
        self._master_pipe = master_pipe

        self._active_module: Optional[AbstractModule] = None

        self._modules: ModuleDict = {}
        self._modules_command_map: CommandDictList = {}
        self._commands: CommandList = []
        self._global_commands: CommandList = []

        self._last_commands = deque(maxlen=50)
        self._modules_last_commands: dict[str, deque] = {}

    # Add module to resolver.
    def add_module(self, module: AbstractModule) -> Resolver:
        identifier = module.get_identifier()
        self._modules[identifier] = module
        self._modules_last_commands[identifier] = deque(maxlen=15)

        return self

    # Add command to resolver.
    def add_command(self, command: AbstractCommand) -> Resolver:
        self._commands.append(command)

        for module_identifier in command.get_modules():
            if module_identifier not in self._modules_command_map:
                self._modules_command_map[module_identifier] = []

            self._modules_command_map[module_identifier].append(command)

        if command.use_for_all_modules():
            self._global_commands.append(command)

        return self

    # Set active module.
    def set_active_module(self, module: AbstractModule) -> Resolver:
        self._active_module = module
        return self

    # Get all exist modules.
    def get_modules(self) -> ModuleDict:
        return self._modules

    # Get all command, can be filtered by active module.
    def get_all_commands(self, filter_by_module: bool = False) -> CommandList:
        if not filter_by_module:
            return self._commands

        all_available_commands = self._global_commands

        if self._active_module is not None:
            module_identifier = self._active_module.get_identifier()
            if module_identifier in self._modules_command_map:
                all_available_commands = all_available_commands + self._modules_command_map[module_identifier]

        return all_available_commands

    # Get last messages.
    def get_last_messages(self, module_filter: Optional[str] = None) -> list[ListenData]:
        if module_filter is not None:
            return list(self._modules_last_commands[module_filter])

        return list(self._last_commands)

    # Thread run loop
    def run(self) -> None:
        while True:
            # Ask for new message.
            self._queue_pipe.send(MessageQueue.MESSAGE_GET)

            # Process new message.
            message = self._queue_pipe.recv()
            self._process_message(message)

    # Process speach data.
    def _process_message(self, message: ListenData) -> None:
        # Save message info.
        self._last_commands.append(message)

        if self._active_module is not None:
            self._modules_last_commands[self._active_module.get_identifier()].append(message)

        # find command for run.
        for command in self.get_all_commands(filter_by_module=True):
            command_regexps = command.get_commands_req_exps_map(message.language)
            for command_name in command_regexps:
                regexp = command_regexps[command_name]
                match = re.findall('^' + regexp + '$', message.text, re.IGNORECASE | re.UNICODE)

                if match:
                    if self._active_module is not None:
                        # Run command through module.
                        self._active_module.process_command(command, command_name, message.language, match, message)
                    else:
                        # Run command direct.
                        command.process_command(command_name, message.language, match, message)
                    return

        # Process unrecognized message by module.
        if self._active_module is not None:
            self._active_module.process_unrecognized_command(message.language, message.text, message)
