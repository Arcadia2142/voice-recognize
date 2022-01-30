#!/bin/bash
CURRENT_DIRNAME="$(dirname `readlink -f $0`)"

IS_HELP=false
USE_GPU=false

COMMANDS=()

while test $# -gt 0; do
	case "$1" in
		--use-gpu)
			USE_GPU=true
			shift
			;;

	  --help|-h)
	    IS_HELP=true
	    shift
      ;;

		*)
		  COMMANDS+=($1)
			shift
			;;
	esac
done

if [[ "${IS_HELP}" != "false" ]]; then
  echo "Options:"
  echo -e "\t --use-gpu \t install gpu version of deepspeach"
  echo -e "\t -h|-help \t print this help"

  exit 0
fi


#Create enviroment and install deppspeach recognize + learn
(
    rm -Rf "${CURRENT_DIRNAME}/venv"
    mkdir "${CURRENT_DIRNAME}/venv"

    # Setup venv
    virtualenv -p python3 "${CURRENT_DIRNAME}/venv/"
    source "${CURRENT_DIRNAME}/venv/bin/activate"

    # Recognize install
    if [[ "${EXPORT}" != "false" ]]; then
      pip3 install deepspeech-gpu
    else
      pip3 install deepspeech
    fi

    # Learn install
    git clone --branch v0.9.3 https://github.com/mozilla/DeepSpeech "${CURRENT_DIRNAME}/venv/DeepSpeech"
    cd "${CURRENT_DIRNAME}/venv/DeepSpeech"

    python -m pip install --upgrade pip
    pip3 install --upgrade wheel==0.34.2 setuptools==49.6.0
    # pip3 install --upgrade -e .
    pip3 install .

    if [[ "${EXPORT}" != "false" ]]; then
      pip3 uninstall -y tensorflow
      pip3 install 'tensorflow-gpu==1.15.4'
    fi

    ln -s "${CURRENT_DIRNAME}/venv/DeepSpeech/DeepSpeech.py" "${CURRENT_DIRNAME}/venv/bin/deepspeech-train"

    python3 util/taskcluster.py --source tensorflow --artifact convert_graphdef_memmapped_format --branch r1.15 --target .
    ln -s "${CURRENT_DIRNAME}/venv/DeepSpeech/convert_graphdef_memmapped_format" "${CURRENT_DIRNAME}/venv/bin/convert_graphdef_memmapped_format"


    # App install
    cd "${CURRENT_DIRNAME}/runner/"
    pip install -r requirements.txt
    cd "${CURRENT_DIRNAME}"
)

#Download CS-model
(
  if [[ ! -d "${CURRENT_DIRNAME}/models/cs" ]]; then
    mkdir "${CURRENT_DIRNAME}/models/cs"
    cd "${CURRENT_DIRNAME}/models/cs"

    wget -O "${CURRENT_DIRNAME}/models/cs/alphabet.txt" "https://github.com/comodoro/deepspeech-cs/releases/download/2021-07-21/alphabet.txt"
    wget -O "${CURRENT_DIRNAME}/models/cs/cs.scorer" "https://github.com/comodoro/deepspeech-cs/releases/download/2021-07-21/o4-500k-wnc-2011.scorer"
    wget -O "${CURRENT_DIRNAME}/models/cs/cs.pbmm" "https://github.com/comodoro/deepspeech-cs/releases/download/2021-07-21/output_graph.pbmm"

    wget -O "${CURRENT_DIRNAME}/models/cs/checkpoint.zip" "https://github.com/comodoro/deepspeech-cs/releases/download/2021-07-21/checkpoint.zip"

    mkdir "${CURRENT_DIRNAME}/models/cs/checkpoint"
    unzip "${CURRENT_DIRNAME}/models/cs/checkpoint.zip" -d "${CURRENT_DIRNAME}/models/cs/checkpoint/"

    echo "model_checkpoint_path: \"${CURRENT_DIRNAME}/models/cs/checkpoint/best_dev-1777698\"" > "${CURRENT_DIRNAME}/models/cs/checkpoint/checkpoint"
    echo "all_model_checkpoint_paths: \"${CURRENT_DIRNAME}/models/cs/checkpoint/best_dev-1777698\"" >> "${CURRENT_DIRNAME}/models/cs/checkpoint/checkpoint"
    rm "${CURRENT_DIRNAME}/models/cs/checkpoint.zip"
  fi
)

