import os
from multiprocessing import Process, Pipe
from colorama import deinit

from src.Classes.Listener import Listener
from src.Classes.MessageQueue import MessageQueue
from src.Classes.Resolver import Resolver

# Modules import
from src.Modules.TextModule.TextModule import TextModule
from src.Modules.EditModule.TextModule import EditModule
from src.Modules.RepairModule.RepairModule import RepairModule
from src.Modules.CommandModule.CommandModule import CommandModule


# Commands import
from src.Commands.ModulesChanges.ModulesChanges import ModulesChanges
from src.Commands.FocusCommands.FocusCommands import FocusCommands
from src.Commands.RepairCommands.RepairCommands import RepairCommands
from src.Commands.TypeCommands.TypeCommands import TypeCommands


def start_listener(pipe, args):
    listener = Listener(pipe, args)
    listener.run()


def start_message_queue(listener_pipe, resolver_pipe):
    queue = MessageQueue(listener_pipe, resolver_pipe)
    queue.run()


def start_resolver(master_pipe, resolver_pipe, root_dir: str):
    resolver = Resolver(master_pipe, resolver_pipe)

    # fill with commands
    resolver.add_command(ModulesChanges(resolver))
    resolver.add_command(FocusCommands(resolver))
    resolver.add_command(RepairCommands(resolver, root_dir + "/models"))

    type_command = TypeCommands(resolver)
    resolver.add_command(type_command)


    # fill modules
    resolver.add_module(TextModule(resolver, type_command))
    resolver.add_module(EditModule(resolver))
    resolver.add_module(RepairModule(resolver))
    resolver.add_module(CommandModule(resolver))

    # Set active module
    resolver.set_active_module(resolver.get_modules()[CommandModule.get_identifier()])

    resolver.run()

def main(ARGS):
    deinit()

    root_dir = os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + "/..")

    # Start listen for text.
    listener_pipe_extern, listener_pipe_inner = Pipe()
    listener_process = Process(target=start_listener, args=(listener_pipe_inner, ARGS))
    listener_process.start()

    # Start message queen.
    message_queue_resolver, message_queue_inner = Pipe()
    message_queue_process = Process(target=start_message_queue, args=(listener_pipe_extern, message_queue_inner))
    message_queue_process.start()

    # command resolver.
    resolver_master_pipe, resolver_inner_pipe = Pipe()
    resolver_process = Process(target=start_resolver, args=(message_queue_resolver, resolver_inner_pipe, root_dir))
    resolver_process.start()

    while True:
        command = resolver_master_pipe.recv()


if __name__ == '__main__':
    DEFAULT_SAMPLE_RATE = 44100
    DEFAULT_LANGUAGE = "cs"

    import sys, os

    sys.path.insert(0, os.path.abspath('.'))

    import argparse

    parser = argparse.ArgumentParser(description="Stream from microphone to DeepSpeech using VAD")

    parser.add_argument('-v', '--vad_aggressiveness', type=int, default=3,
                        help="Set aggressiveness of VAD: an integer between 0 and 3, 0 being the least aggressive about filtering out non-speech, 3 the most aggressive. Default: 2")

    parser.add_argument('-l', '--language',
                        help=f"Default language Default: {DEFAULT_LANGUAGE}", default=DEFAULT_LANGUAGE)

    parser.add_argument('-r', '--rate', type=int, default=DEFAULT_SAMPLE_RATE,
                        help=f"Input device sample rate. Default: {DEFAULT_SAMPLE_RATE}. Your device may require 44100.")

    parser.add_argument('-d', '--device', type=int, default=None,
                        help="Device input index (Int) as listed by pyaudio.PyAudio.get_device_info_by_index(). If not provided, falls back to PyAudio.get_default_device().")

    ARGS = parser.parse_args()
    main(ARGS)
