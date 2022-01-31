#!/bin/bash
CURRENT_DIRNAME="$(dirname `readlink -f $0`)"

IS_HELP=false
EPOCHS="75"

COMMANDS=()

while test $# -gt 0; do
	case "$1" in
      --epochs)
          EPOCHS="$2"
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
  echo "Learn model from scratch:"
  echo "${CURRENT_DIRNAME} [options] <language>"
  echo -e "\t --epochs \t Number of learn iterations"
  echo -e "\t -h|--help \t Print help"
  exit 0
fi

if [[ ! -d "${CURRENT_DIRNAME}/train/${COMMANDS[0]}" ]]; then
  echo "Training dir for language ${COMMANDS[0]} not found"
  exit 1
fi

ALPHABET="${CURRENT_DIRNAME}/train/${COMMANDS[0]}/alphabet.txt"
if [[ ! -f "${ALPHABET}" ]]; then
  echo "Missing ${ALPHABET} :-("
  exit 1
fi

(
    cd "$CURRENT_DIRNAME"
    ./stop_gpu_docker.sh
    ./start_gpu_docker.sh
    docker exec -it deepspeach_train-gpu_1 /bin/bash -c \
        "TF_FORCE_GPU_ALLOW_GROWTH=true deepspeech-train --summary_dir='/train/${COMMANDS[0]}/summarize' --n_hidden 2048 --alphabet_config_path '/train/${COMMANDS[0]}/alphabet.txt' --checkpoint_dir '/models/${COMMANDS[0]}/checkpoint' --epochs 75 --train_files '/train/${COMMANDS[0]}/validated.csv' --test_files '/train/${COMMANDS[0]}/test.csv' --dev_files '/train/${COMMANDS[0]}/dev.csv' --learning_rate 0.0001 --export_dir '/train/${COMMANDS[0]}/export' --show_progressbar --train_cudnn --automatic_mixed_precision"
)
