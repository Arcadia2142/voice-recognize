#!/bin/bash
CURRENT_DIRNAME="$(dirname `readlink -f $0`)"

EPOCHS="20"
LANGUAGE="cs-test"
EXPORT=false

COMMANDS=()

while test $# -gt 0; do
	case "$1" in
		-e|--export)
			EXPORT=true
			shift
			;;
			
        -l|--language)
            LANGUAGE="$2"
            shift 2
            ;;
            
        --epochs)
            EPOCHS="$2"
            shift 2
            ;;
        

		*)
		    COMMANDS+=($1)
			shift
			;;
	esac
done

MODEL_DIR="${CURRENT_DIRNAME}/models/${LANGUAGE}"
source "${CURRENT_DIRNAME}/train/bin/activate"

#Learn
if [ $# -eq 0 ]; then
    DeepSpeech \
        --n_hidden 2048 \
        --alphabet_config_path "${MODEL_DIR}/alphabet.txt" \
        --checkpoint_dir "${MODEL_DIR}/checkpoint" \
        --epochs "${EPOCHS}" \
        --train_files "$1" \
        --test_files "$1" \
        --learning_rate 0.0001
fi

#export
if [[ "${EXPORT}" != "false" ]]; then
DeepSpeech \
    --alphabet_config_path "${MODEL_DIR}/alphabet.txt" \
    --checkpoint_dir "${MODEL_DIR}/checkpoint" \
    --export_dir "${MODEL_DIR}/export" 
    
    convert_graphdef_memmapped_format \
    --in_graph="${MODEL_DIR}/export/output_graph.pb" \
    --out_graph="${MODEL_DIR}/export/output_graph.pbmm"
fi
