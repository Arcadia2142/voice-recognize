CURRENT_DIRNAME="$(dirname `readlink -f $0`)"
source "${CURRENT_DIRNAME}/recognize/bin/activate" 
deepspeech $@
