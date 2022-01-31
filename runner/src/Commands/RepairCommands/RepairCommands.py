from abc import ABC

import os
import shutil
import csv
import re

from typing import Optional, Dict
from multiprocessing import Process

from ...Abstracts import AbstractCommand, AbstractResolver
from ...Classes.Listener import ListenData
from ...Modules.RepairModule.RepairModule import RepairModule
from ...Classes.Utils import Utils

class RepairCommandsOptions(object):

    def __init__(self, model_dir: str) -> None:
        super().__init__()
        self.model_dir : str = model_dir
        self.ram_fs_tmp : Optional[str] = None
        self.use_docker : bool = False


class RepairCommands(AbstractCommand, ABC):
    ACTION_REPAIR = "repair"
    ACTION_LEARN = "learn"

    def __init__(self, resolver: AbstractResolver, options: RepairCommandsOptions) -> None:
        super().__init__(resolver)
        self._options = options

    @staticmethod
    def get_modules() -> list:
        return [RepairModule.get_identifier()]

    @staticmethod
    def _get_commands_file() -> str:
        return os.path.dirname(os.path.realpath(__file__)) + "/commands.txt"

    def process_command(self, action: str, language: str, reg_exp_args: list, listen_data: ListenData) -> None:
        if action == self.ACTION_REPAIR:
            self.action_repair()
        elif action == self.ACTION_LEARN:
            self.action_learn(language)

    # Open message for repair.
    def action_repair(self, repair_message: Optional[ListenData] = None) -> None:
        # Search invalid message in last messages.
        if repair_message is None:
            last_messages = self._resolver.get_last_messages()
            last_messages.reverse()

            # Find last message not associated with command.
            for message in last_messages:
                if not message.fixed and message.command_identifier is None:
                    repair_message = message
                    break

        if repair_message is None:
            print('No message for repair')
            return

        repair_message.fixed = True
        model_dir = self._options.model_dir + "/" + repair_message.language

        # create train dir + files..
        if not os.path.isdir(model_dir + "/train"):
            os.mkdir(model_dir + "/train")

        if not os.path.isdir(model_dir + "/train/learn"):
            os.mkdir(model_dir + "/train/learn")

        if not os.path.isfile(model_dir + "/train/learn/data.csv"):
            f = open(model_dir + "/train/learn/data.csv", "w")
            f.write("wav_filename,wav_filesize,transcript\n")
            f.close()

        # Start text editor for manual repair.
        print("Opening " + repair_message.text_file_path + " for repair text")

        def repair_task(editor_command: str, message_data: ListenData, train_dir: str) -> None:
            Utils.run_shell_command(
                editor_command,
                {"FILE": message_data.text_file_path}
            )

            text_file = open(message_data.text_file_path, 'r')
            fixed_text = text_file.read().replace("\n", '')

            wav_file_path = train_dir + "/" + message_data.timestamp + '.wav'
            shutil.copy(message_data.wav_file_path, wav_file_path)

            vaw_size = os.stat(wav_file_path).st_size
            train_scv = open(train_dir + "/data.csv", 'a')
            train_scv.write(message_data.timestamp + '.wav' + "," + str(vaw_size) + "," + fixed_text + "\n")
            train_scv.close()


        # Start sub-process with text editor.
        repair_process = Process(
            target=repair_task,
            args=(
                self._get_shell_command(self.ACTION_REPAIR, 'kwrite "$FILE"'),
                repair_message,
                model_dir + "/train/learn"
            )
        )
        repair_process.start()

    # Learn
    def action_learn(self, language: str) -> None:
        print("Starting learn process")

        model_dir = self._options.model_dir + "/" + language
        if not os.path.isfile(model_dir + "/train/learn/data.csv"):
            print("No data for learn")
            return

        if not os.path.isdir(model_dir + "/train/learned"):
            os.mkdir(model_dir + "/train/learned")

        if not os.path.isfile(model_dir + "/train/learned/data.csv"):
            f = open(model_dir + "/train/learned/data.csv", "w")
            f.write("wav_filename,wav_filesize,transcript\n")
            f.close()

        def learn_task(language_inner: str, options: RepairCommandsOptions):

            model_dir_inner = options.model_dir + "/" + language_inner
            ram_fs_inner = options.ram_fs_tmp

            # Copy to learning folder.
            os.rename(model_dir_inner + '/train/learn', model_dir_inner + '/train/learning')

            # Copy checkpoints to ram fs.
            use_ram_fs = False
            checkpoint_dir = checkpoint_original_dir = model_dir_inner + '/checkpoint'
            if ram_fs_inner is not None:
                if os.path.isdir(ram_fs_inner):
                    use_ram_fs = True
                    checkpoint_dir = ram_fs_inner + '/model-' + language_inner

                    if not os.path.isdir(checkpoint_dir):
                        os.mkdir(checkpoint_dir)

                    for file_name in os.listdir(checkpoint_original_dir):
                        shutil.copy(checkpoint_original_dir + "/" + file_name, checkpoint_dir + "/" + file_name)
                else:
                    print("Ram FS dir doesnt exist.")

            # Run learning process in docker.
            model_dir_learn = model_dir
            checkpoint_dir_learn = checkpoint_dir
            wrapper_runner_pre = []
            wrapper_runner_pos = []

            if options.use_docker:
                wrapper_runner_pre = ['docker', 'exec', '-it', 'deepspeach_train-gpu_1']
                wrapper_runner_pos = ['--train_cudnn']

                model_dir_learn = "/models/" + language_inner
                checkpoint_dir = model_dir_learn + '/checkpoint'

                if ram_fs_inner:
                    checkpoint_dir_learn = '/ramfs/model-' + language_inner

            # Learn data.
            return_code = Utils.run_shell_command(
                wrapper_runner_pre + [
                    'deepspeech-train',
                    '--n_hidden', '2048',
                    '--alphabet_config_path', model_dir_learn + '/alphabet.txt',
                    '--checkpoint_dir', checkpoint_dir_learn,
                    '--epochs', '30',
                    '--train_files', model_dir_learn + '/train/learning/data.csv',
                    '--test_files', model_dir_learn + '/train/learning/data.csv',
                    '--learning_rate', '0.001',
                    '--export_dir', model_dir_learn + '/export',
                    '--show_progressbar'
                ] + wrapper_runner_pos,
                shell=False
            )

            #Learn failed.
            if return_code != 0:
                print("Learning process failed.")
                return None

            checkpoint_file_map: Dict[str, bool] = {}
            with open(checkpoint_dir + "/checkpoint", 'r') as checkpoint_file:
                checkpoint_files_paths_reg = re.compile(r'^all_model_checkpoint_paths:\s+"(.+)"$')

                for checkpoint_line in checkpoint_file.readlines():
                    checkpoint_file_path = checkpoint_files_paths_reg.findall(checkpoint_line.strip())
                    if checkpoint_file_path:
                        checkpoint_file_map[checkpoint_file_path[0]] = True


            # Copy from ram FS.
            if use_ram_fs:
                os.rename(checkpoint_original_dir, checkpoint_original_dir + ".bak")
                os.mkdir(checkpoint_original_dir)

                for file_name in os.listdir(checkpoint_dir):
                    file_path = os.path.splitext( os.path.realpath(checkpoint_dir + "/" + file_name))[0]

                    if file_path in checkpoint_file_map or file_name == 'checkpoint':
                        shutil.copy(checkpoint_dir + "/" + file_name, checkpoint_original_dir + "/" + file_name)

                shutil.rmtree(checkpoint_dir)
                shutil.rmtree(checkpoint_original_dir + ".bak")
            else:
                # Remove old checkpoints.
                for file_name in os.listdir(checkpoint_original_dir):
                    file_path = os.path.splitext( os.path.realpath(checkpoint_original_dir + "/" + file_name))[0]
                    if file_path not in checkpoint_file_map and file_name != 'checkpoint':
                        os.remove(file_path)


            # Convert to pbmm
            pbmm_file_address = model_dir_inner + '/' + language_inner + '.pbmm'
            try:
                os.rename(pbmm_file_address, pbmm_file_address + ".bak")

                return_code = Utils.run_shell_command(
                    [
                        'convert_graphdef_memmapped_format',
                        '--in_graph=' + model_dir_inner + '/export/output_graph.pb',
                        '--out_graph=' + model_dir_inner + '/' + language_inner + '.pbmm'
                    ],
                    shell=False
                )

                if return_code == 0:
                    os.remove(pbmm_file_address + ".bak")
                else:
                    os.rename(pbmm_file_address + ".bak", pbmm_file_address)
            except Exception as e:
                os.rename(pbmm_file_address + ".bak", pbmm_file_address)
                raise

                # Copy data to learned folder.
            with open(model_dir_inner + "/train/learned/data.csv", "a") as learned_csv:
                with open(model_dir_inner + '/train/learning/data.csv') as csv_file:
                    csv_reader = csv.reader(csv_file, delimiter=',')

                    is_header = True
                    for row in csv_reader:
                        if is_header:
                            is_header = False
                            continue

                        os.rename(model_dir_inner + '/train/learning/' + row[0],
                                  model_dir_inner + '/train/learned/' + row[0])
                        learned_csv.write(','.join(row) + "\n")

            shutil.rmtree(model_dir_inner + '/train/learning/')
            print("Learn process complete")

        # Start sub-process for learning.
        learn_process = Process(
            target=learn_task,
            args=(
                language,
                self._options
            )
        )

        learn_process.start()
        return
