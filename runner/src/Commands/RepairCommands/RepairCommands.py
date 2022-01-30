from abc import ABC

import os
import shutil
import csv

from typing import Optional
from multiprocessing import Process

from ...Abstracts import AbstractCommand, AbstractResolver
from ...Classes.Listener import ListenData
from ...Modules.RepairModule.RepairModule import RepairModule
from ...Classes.Utils import Utils


class RepairCommands(AbstractCommand, ABC):
    ACTION_REPAIR = "repair"
    ACTION_LEARN = "learn"

    def __init__(self, resolver: AbstractResolver, models_dir: str) -> None:
        super().__init__(resolver)
        self._models_dir = models_dir

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

            for message in last_messages:
                if message.command_identifier is None:
                    repair_message = message

        model_dir = self._models_dir + "/" + repair_message.language

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
        if repair_message is not None:
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
            return

        print('No message for repair')

    # Learn
    def action_learn(self, language: str) -> None:
        print("Starting learn process")

        model_dir = self._models_dir + "/" + language
        if not os.path.isfile(model_dir + "/train/learn/data.csv"):
            print("No data for learn")
            return

        if not os.path.isdir(model_dir + "/train/learned"):
            os.mkdir(model_dir + "/train/learned")

        if not os.path.isfile(model_dir + "/train/learned/data.csv"):
            f = open(model_dir + "/train/learned/data.csv", "w")
            f.write("wav_filename,wav_filesize,transcript\n")
            f.close()

        def learn_task(language_inner: str, model_dir_inner: str):
            # Copy to learning folder.
            os.rename(model_dir_inner + '/train/learn', model_dir_inner + '/train/learning')

            # Learn data.
            Utils.run_shell_command(
                [
                    'deepspeech-train',
                    '--n_hidden', '2048',
                    '--alphabet_config_path', model_dir_inner + '/alphabet.txt',
                    '--checkpoint_dir', model_dir_inner + '/checkpoint',
                    '--epochs', '30',
                    '--train_files', model_dir_inner + '/train/learning/data.csv',
                    '--test_files', model_dir_inner + '/train/learning/data.csv',
                    '--learning_rate', '0.001',
                    '--export_dir', model_dir_inner + '/export',
                    '--show_progressbar'
                ],
                shell=False
            )

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
                model_dir
            )
        )

        learn_process.start()
        return
