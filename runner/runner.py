import os

from configparser import ConfigParser
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
from src.Commands.RepairCommands.RepairCommands import RepairCommands, RepairCommandsOptions
from src.Commands.TypeCommands.TypeCommands import TypeCommands


def start_listener(pipe, args, root_dir: str):
    listener = Listener(pipe, args, root_dir)
    listener.run()


def start_message_queue(listener_pipe, resolver_pipe):
    queue = MessageQueue(listener_pipe, resolver_pipe)
    queue.run()


def start_resolver(args, master_pipe, resolver_pipe, root_dir: str):
    resolver = Resolver(master_pipe, resolver_pipe)

    repair_options = RepairCommandsOptions(root_dir + "/models")
    repair_options.ram_fs_tmp = args.ram_fs_tmp
    repair_options.use_docker = args.enable_gpu_docker

    # fill with commands
    resolver.add_command(ModulesChanges(resolver))
    resolver.add_command(FocusCommands(resolver))
    resolver.add_command(RepairCommands(resolver, repair_options))

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


def main(ARGS, root_dir: str):
    deinit()

    # Create missing temp dir
    temp_dir = root_dir + "/tmp"
    if not os.path.isdir(temp_dir):
        os.mkdir(temp_dir)

    # Start listen for text.
    listener_pipe_extern, listener_pipe_inner = Pipe()
    listener_process = Process(target=start_listener, args=(listener_pipe_inner, ARGS, root_dir))
    listener_process.start()

    # Start message queen.
    message_queue_resolver, message_queue_inner = Pipe()
    message_queue_process = Process(target=start_message_queue, args=(listener_pipe_extern, message_queue_inner))
    message_queue_process.start()

    # command resolver.
    resolver_master_pipe, resolver_inner_pipe = Pipe()
    resolver_process = Process(target=start_resolver, args=(ARGS, message_queue_resolver, resolver_inner_pipe, root_dir))
    resolver_process.start()

    while True:
        command = resolver_master_pipe.recv()


if __name__ == '__main__':
    CONFIG_MAIN_SECTION = "default"

    CONFIG_OPTION_LANGUAGE = 'language'
    CONFIG_OPTION_VAD_AGGR = 'vad_aggressiveness'
    CONFIG_OPTION_S_RATE = 'sample_rate'
    CONFIG_OPTION_DEVICE = 'device'
    CONFIG_OPTION_RAM_FS = 'train_ram_fs_tmp'
    CONFIG_OPTION_EN_GPU = 'enable_gpu_docker'

    import argparse

    root_dir = os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + "/..")

    config = ConfigParser()
    if os.path.isfile(root_dir + "/defaults.txt"):
        config.read(root_dir + "/defaults.txt")

    language = config.get(CONFIG_MAIN_SECTION, CONFIG_OPTION_LANGUAGE, fallback="cs")
    vad_aggressiveness = config.getint(CONFIG_MAIN_SECTION, CONFIG_OPTION_VAD_AGGR, fallback=3)
    sample_rate = config.getint(CONFIG_MAIN_SECTION, CONFIG_OPTION_S_RATE, fallback=44100)
    device = config.getint(CONFIG_MAIN_SECTION, CONFIG_OPTION_DEVICE, fallback=None)
    ram_fs_tmp = config.get(CONFIG_MAIN_SECTION, CONFIG_OPTION_RAM_FS, fallback=None)
    enable_gpu = config.getboolean(CONFIG_MAIN_SECTION, CONFIG_OPTION_EN_GPU, fallback=False)

    parser = argparse.ArgumentParser(description="Stream from microphone to DeepSpeech using VAD")

    parser.add_argument('-v', '--vad_aggressiveness',
                        type=int,
                        default=vad_aggressiveness,
                        help=f"Set aggressiveness of VAD: an integer between 0 and 3, 0 being the least aggressive about filtering out non-speech, 3 the most aggressive. Default: {vad_aggressiveness}"
                        )

    parser.add_argument('-l', '--language',
                        help=f"Default language Default: {language}",
                        default=language
                        )

    parser.add_argument('-r', '--rate', type=int, default=sample_rate,
                        help=f"Input device sample rate. Default: {sample_rate}. Your device may require 44100.")

    parser.add_argument('-d', '--device', type=int, default=device,
                        help="Device input index (Int) as listed by pyaudio.PyAudio.get_device_info_by_index(). If not provided, falls back to PyAudio.get_default_device().")

    parser.add_argument('--ram_fs_tmp', default=ram_fs_tmp,
                        help="Path to RAM FS tmp dir for speedup train process")

    parser.add_argument('--enable_gpu_docker', default=enable_gpu, action='store_true',
                        help="Enable process learning on GPU.")

    ARGS = parser.parse_args()

    #Expand relative path to absolute.
    if ARGS.ram_fs_tmp is not None and not os.path.isabs(ARGS.ram_fs_tmp):
        ARGS.ram_fs_tmp = os.path.realpath(root_dir + "/" + ARGS.ram_fs_tmp)

    main(ARGS, root_dir)
