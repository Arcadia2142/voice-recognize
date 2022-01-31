#!/bin/bash
CURRENT_DIRNAME="$(dirname `readlink -f $0`)"

IS_HELP=false
ONLY_CSV=false
MP3_DIR="clips"

COMMANDS=()

while test $# -gt 0; do
	case "$1" in
      --only-csv)
          ONLY_CSV=true
          shift
          ;;

      --mp3-dir)
        ONLY_CSV="$2"
        shift 2
        ;;

      -h|--help)
        IS_HELP=true
        shift
        ;;

      *)
          COMMANDS+=($1)
			shift
			;;
	esac
done

if [[ "${IS_HELP}" == "true" ]]; then
  echo "Prepare lear data from:"
  echo "https://commonvoice.mozilla.org/en/datasets"
  ehoo "${CURRENT_DIRNAME} [options] <language>"
  echo -e "\t --only-csv \t Disable audio convert"
  echo -e "\t --mp3-dir \t Dirname with mp3 files."
  echo -e "\t -h|--help \t Print help"
  exit 0
fi

if [[ ! -d "${CURRENT_DIRNAME}/${COMMANDS[0]}" ]]; then
  echo "Training dir for language ${COMMANDS[0]} not found"
  exit 1
fi

ALPHABET="${CURRENT_DIRNAME}/${COMMANDS[0]}/alphabet.txt"
if [[ ! -f "${ALPHABET}" ]]; then
  echo "Missing ${ALPHABET} :-("
  exit 1
fi

if [[ "${ONLY_CSV}" == "false" ]]; then
  echo "Starting audio convert - this take many time"
  sleep 5
  
  find"${CURRENT_DIRNAME}/${COMMANDS[0]}/${MP3_DIR}" -name '*.csv' -exec bash -c 'rm ${0}' {} \;
  find "${CURRENT_DIRNAME}/${COMMANDS[0]}/${MP3_DIR}" -name '*.mp3' -exec bash -c 'ffmpeg -i "${0}" -ar 44100 "${0/.mp3/.wav}"' {} \;
fi

(
  source "${CURRENT_DIRNAME}/../venv/bin/activate"

  cd "${CURRENT_DIRNAME}"
  
  find"${CURRENT_DIRNAME}/${COMMANDS[0]}" -name '*.csv' -exec bash -c 'rm ${0}' {} \;
  find "${CURRENT_DIRNAME}/${COMMANDS[0]}" -name "*.tsv" -exec bash -c "python tsv_convert.py -f \"\${0}\" -a \"${ALPHABET}\" -p \"${MP3_DIR}\"" {} \;
)
