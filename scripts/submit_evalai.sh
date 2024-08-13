#!/bin/bash

DOC_STRING="Push docker image for evalai submission."

USAGE_STRING=$(cat <<- END
Usage: $0 [-h|--help] [-t|--target-name TARGET]

The default target name is "leaderboard-user"

END
)

# Defaults
TARGET_NAME="leaderboard-user"

while [[ $# -gt 0 ]]; do
  case "$1" in
    -t | --target-name )
      TARGET_NAME=$2
      shift 2 ;;
    -h | --help )
      usage
      ;;
    * )
      shift ;;
  esac
done

export EVALAI_API_URL=https://eval.ai
export AWS_REGION_NAME=eu-west-2

source $HOME/miniconda3/bin/activate
conda activate evalai-cli

evalai push ${TARGET_NAME} --phase carla-rai-leaderboard-sensors-2352