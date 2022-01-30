import deepspeech
import os
import numpy as np
from datetime import datetime
from typing import Optional

from multiprocessing.connection import Connection
from .Audio import VADAudio


class ListenData(object):
    def __init__(self, language: str, text: str, timestamp: str, text_file_path: str, wav_file_path: str) -> None:
        super().__init__()
        self.text: str = text
        self.language: str = language

        self.text_file_path: str = text_file_path
        self.wav_file_path: str = wav_file_path
        self.timestamp = timestamp

        self.module: Optional[str] = None
        self.command_identifier: Optional[str] = None
        self.command_action: Optional[str] = None


class Listener(object):

    def __init__(self, pipe: Connection, args, root_dir: str) -> None:
        self._pipe = pipe
        self._args = args
        self._root_dir = root_dir

    def run(self) -> None:
        temp_dir = self._root_dir + "/tmp/" + self._args.language
        model_dir = self._root_dir + "/models/" + self._args.language

        if not os.path.isdir(temp_dir):
            os.mkdir(temp_dir)

        if os.path.isdir(model_dir):
            model = deepspeech.Model(model_dir + "/" + self._args.language + ".pbmm")
            model.enableExternalScorer(model_dir + "/" + self._args.language + ".scorer")
        else:
            raise RuntimeError(f"Model dir ${model_dir} missing")

        # Start audio with VAD
        vad_audio = VADAudio(
            aggressiveness=self._args.vad_aggressiveness,
            input_rate=self._args.rate,
            device=self._args.device,
        )

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
                    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")

                    # save audio for possible correct. {
                    dirname = os.path.join(temp_dir, timestamp)
                    os.mkdir(dirname)

                    vad_audio.write_wav(dirname + "/voice.wav", wav_data)

                    f = open(dirname + "/text.txt", "w")
                    f.write(text)
                    f.close()
                    # }

                    # send data by pipe.
                    self._pipe.send(
                        ListenData(
                            self._args.language,
                            text,
                            timestamp,
                            dirname + "/text.txt",
                            dirname + "/voice.wav"
                        )
                    )

                wav_data = bytearray()
                stream_context = model.createStream()
