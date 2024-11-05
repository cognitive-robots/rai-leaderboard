#!/bin/bash

DOC_STRING="Build Carla agent docker image."

USAGE_STRING=$(cat <<- END
Usage: $0 [-h|--help] [-t|--target-name TARGET]

The default target name is "leaderboard-user"

END
)

usage() { echo "${DOC_STRING}"; echo "${USAGE_STRING}"; exit 0; }

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

# Get the relative path to the bash directory
SCRIPT_DIR="$( dirname "${BASH_SOURCE[0]}" )"

# load environment variables
source $SCRIPT_DIR/env_var.sh

if [ -z "$CARLA_ROOT" ]
then
    echo "Error $CARLA_ROOT is empty. Set \$CARLA_ROOT as an environment variable first."
    exit 1
fi

if [ -z "$SCENARIO_RUNNER_ROOT" ]
then echo "Error $SCENARIO_RUNNER_ROOT is empty. Set \$SCENARIO_RUNNER_ROOT as an environment variable first."
    exit 1
fi

if [ -z "$LEADERBOARD_ROOT" ]
then echo "Error $LEADERBOARD_ROOT is empty. Set \$LEADERBOARD_ROOT as an environment variable first."
    exit 1
fi

if [ -z "$RAI_LEADERBOARD_ROOT" ]
then echo "Error $RAI_LEADERBOARD_ROOT is empty. Set \$RAI_LEADERBOARD_ROOT as an environment variable first."
    exit 1
fi

if [ -z "$TEAM_CODE_ROOT" ]
then echo "Error $TEAM_CODE_ROOT is empty. Set \$TEAM_CODE_ROOT as an environment variable first."
    exit 1
fi

mkdir .tmp

cp -fr ${CARLA_ROOT}/PythonAPI  .tmp
cp -fr ${SCENARIO_RUNNER_ROOT}/ .tmp
cp -fr ${LEADERBOARD_ROOT}/ .tmp
cp -fr ${RAI_LEADERBOARD_ROOT}/ .tmp
cp -fr ${TEAM_CODE_ROOT}/ .tmp/team_code

if [ -n "$USER_CODE_ROOT" ]
then cp -fr $USER_CODE_ROOT .tmp
fi

# Agent specific things that you want to copy
# For example, requirements.txt or environment.yml
# cp -f ${RAI_LEADERBOARD_ROOT}/../requirements.txt .tmp

# build docker image
docker build --force-rm -t ${TARGET_NAME} -f ${RAI_LEADERBOARD_ROOT}/scripts/Dockerfile .

rm -fr .tmp
