import deepspeech
import os
import numpy as np
from datetime import datetime

from multiprocessing.connection import Connection
from .Audio import VADAudio


class ListenData(object):
    def __init__(self, language: str, text: str, csv_file_path: str) -> None:
        super().__init__()
        self.csv_file_path = csv_file_path
        self.text = text
        self.language = language


class Listener(object):

    def __init__(self, pipe: Connection, args) -> None:
        self._pipe = pipe
        self._args = args

    def run(self) -> None:
        temp_dir = os.path.realpath(
            os.path.dirname(os.path.realpath(__file__)) + "/../../../tmp/" + self._args.language)
        model_dir = os.path.realpath(
            os.path.dirname(os.path.realpath(__file__)) + "/../../../models/" + self._args.language)

        if not os.path.isdir(temp_dir):
            os.mkdir(temp_dir)

        if os.path.isdir(model_dir):
            model = deepspeech.Model(model_dir + "/" + self._args.language + ".pbmm")
            model.enableExternalScorer(model_dir + "/" + self._args.language + ".scorer")
        else:
            raise RuntimeError(f"Model dir ${model_dir} missing")

        # Start audio with VAD
        vad_audio = VADAudio(aggressiveness=self._args.vad_aggressiveness, input_rate=self._args.rate)

        frames = vad_audio.vad_collector()

        # Stream from microphone to DeepSpeech using VAD
        stream_context = model.createStream()
        wav_data = bytearray()

        for frame in frames:
            if frame is not None:
                stream_context.feedAudioContent(np.frombuffer(frame, np.int16))
                wav_data.extend(frame)
            else:
                text = stream_context.finishStream()

                if text.strip() != "":
                    timestamp = datetime.now().strftime("savewav_%Y-%m-%d_%H-%M-%S_%f")

                    # save audio for possible correct. {
                    dirname = os.path.join(temp_dir, timestamp)
                    os.mkdir(dirname)

                    vad_audio.write_wav(dirname + "/voice.wav", wav_data)
                    vaw_size = os.stat(dirname + "/voice.wav").st_size

                    f = open(dirname + "/data.csv", "w")
                    f.write("wav_filename,wav_filesize,transcript\n")
                    f.write(dirname + "/voice.wav" + ",")
                    f.write(str(vaw_size) + ",")
                    f.write(text)
                    f.close()
                    # }

                    # send data by pipe.
                    self._pipe.send(ListenData(self._args.language, text, dirname + "/data.csv"))

                wav_data = bytearray()
                stream_context = model.createStream()
