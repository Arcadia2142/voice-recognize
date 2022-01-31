import os
import csv
import re

def main(ARGS):
    root_dir = os.path.dirname(os.path.realpath(ARGS.tsv_file))
    tsv_file_name = os.path.splitext( os.path.realpath(ARGS.tsv_file))[0]

    alphabet = []
    with open(ARGS.alphabet, 'r') as alphabet_file:
        for line in alphabet_file.readlines():
            line_char = line.replace("\n", '')
            if line_char != '':
                alphabet.append(line)

    chars_filter = re.compile('[^' + ''.join(alphabet) + ']+')
    correct_filter = re.compile(r'[^\w\s]+')

    with open(tsv_file_name + ".csv", 'w') as csv_file:
        csv_file.write("wav_filename,wav_filesize,transcript\n")

        with open(ARGS.tsv_file, 'r') as tsv_file:
            is_first = True
            for row in csv.reader(tsv_file, delimiter="\t"):
                if is_first:
                    is_first = False
                    continue

                audio_file_path = os.path.splitext( ARGS.audio_path_prefix + "/" + row[1])[0] + ".wav"

                learn_text = row[2].lower()
                learn_text_correct = chars_filter.sub('', learn_text)

                if learn_text_correct == correct_filter.sub('', learn_text):
                    csv_file.write(audio_file_path + "," + str(os.stat(root_dir + "/" + audio_file_path).st_size) + "," + learn_text_correct + "\n")
                else:
                    print('Invalid text: ' + learn_text)




if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Stream from microphone to DeepSpeech using VAD")

    parser.add_argument('-f', '--tsv_file',
                        help=f"Path to tsv file.",
                        required=True
                        )

    parser.add_argument('-p', '--audio_path_prefix',
                        default="clips",
                        help=f"Prefix to audio files."
                        )

    parser.add_argument('-a', '--alphabet',
                        help=f"Supported alphabet",
                        required=True
                        )

    ARGS = parser.parse_args()
    main(ARGS)