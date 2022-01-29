#!/bin/bash
CURRENT_DIRNAME="$(dirname `readlink -f $0`)"

#recognize
(
    rm -Rf "${CURRENT_DIRNAME}/recognize"
    mkdir "${CURRENT_DIRNAME}/recognize"
    
    virtualenv -p python3 "${CURRENT_DIRNAME}/recognize/"
    source "${CURRENT_DIRNAME}/recognize/bin/activate"


    pip3 install deepspeech

    cd "${CURRENT_DIRNAME}/runner/"
    pip install -r requirements.txt
    cd "${CURRENT_DIRNAME}"
)

#training
(
    rm -Rf "${CURRENT_DIRNAME}/train"
    mkdir "${CURRENT_DIRNAME}/train"
    
    python3 -m venv "${CURRENT_DIRNAME}/train/"
    source "${CURRENT_DIRNAME}/train//bin/activate"
    
    git clone --branch v0.9.3 https://github.com/mozilla/DeepSpeech "${CURRENT_DIRNAME}/train/DeepSpeech"
    cd "${CURRENT_DIRNAME}/train/DeepSpeech"
    
    python -m pip install --upgrade pip
    pip3 install --upgrade wheel==0.34.2 setuptools==49.6.0
    pip3 install --upgrade -e .
    
    ln -s "${CURRENT_DIRNAME}/train/DeepSpeech/DeepSpeech.py" "${CURRENT_DIRNAME}/train/bin/DeepSpeech"
    
    cd "${CURRENT_DIRNAME}/train/DeepSpeech"
    python3 util/taskcluster.py --source tensorflow --artifact convert_graphdef_memmapped_format --branch r1.15 --target .
    
    ln -s "${CURRENT_DIRNAME}/train/DeepSpeech/convert_graphdef_memmapped_format" "${CURRENT_DIRNAME}/train/bin/convert_graphdef_memmapped_format"
    cd "${CURRENT_DIRNAME}"
)

#Download CS-model
(
  mkdir "${CURRENT_DIRNAME}/modesl/cs"
  cd "${CURRENT_DIRNAME}/models/cs"

  wget -o "${CURRENT_DIRNAME}/models/cs/alphabet.txt" "https://github.com/comodoro/deepspeech-cs/releases/download/2021-07-21/alphabet.txt"
  wget -o "${CURRENT_DIRNAME}/models/cs/cs.scorer" "https://github.com/comodoro/deepspeech-cs/releases/download/2021-07-21/o4-500k-wnc-2011.scorer"
  wget -o "${CURRENT_DIRNAME}/models/cs/cs.pbmm" "https://github.com/comodoro/deepspeech-cs/releases/download/2021-07-21/output_graph.pbmm"

  wget -o "${CURRENT_DIRNAME}/models/cs/checkpoint.zip" "https://github.com/comodoro/deepspeech-cs/releases/download/2021-07-21/checkpoint.zip"
  unzip "${CURRENT_DIRNAME}/models/cs/checkpoint.zip"
)

