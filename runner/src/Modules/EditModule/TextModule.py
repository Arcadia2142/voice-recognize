import os
from ...Abstracts import AbstractModule


class EditModule(AbstractModule):

    @staticmethod
    def get_identifier() -> str:
        return "edit"

    @staticmethod
    def _get_config_file() -> str:
        return os.path.dirname(os.path.realpath(__file__)) + "/module.txt"
