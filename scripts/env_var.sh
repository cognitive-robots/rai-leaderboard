#!/bin/bash

[[ -z "${CARLA_ROOT}" ]]               && export CARLA_ROOT="<Path to your CARLA PythonAPI>"
[[ -z "${LEADERBOARD_ROOT}" ]]         && export LEADERBOARD_ROOT="<Path to your Carla leaderboard root>"
[[ -z "${RAI_LEADERBOARD_ROOT}" ]]     && export RAI_LEADERBOARD_ROOT="<Path to your rai leaderboard root>"
[[ -z "${SCENARIO_RUNNER_ROOT}" ]]     && export SCENARIO_RUNNER_ROOT="<Path to your scenario runner root>"
[[ -z "${TEAM_CODE_ROOT}" ]]           && export TEAM_CODE_ROOT="<Path to your team_code root>"
[[ -z "${USER_CODE_ROOT}" ]]           && export USER_CODE_ROOT="<Path to your user code root (e.g., ../interfuser/)>"


[[ -z "${CHALLENGE_TRACK_CODENAME}" ]] && export CHALLENGE_TRACK_CODENAME=SENSORS
[[ -z "${PORT}" ]]                     && export PORT=2000 # same as the carla server port
[[ -z "${TM_PORT}" ]]                  && export TM_PORT=2500 # port for traffic manager, required when spawning multiple servers/clients
[[ -z "${DEBUG_CHALLENGE}" ]]          && export DEBUG_CHALLENGE=0 # debug information from the simulator
[[ -z "${REPETITIONS}" ]]              && export REPETITIONS=1 # multiple evaluation runs
[[ -z "${ROUTES}" ]]                   && export ROUTES=leaderboard/data/routes_devtest.xml # routes
[[ -z "${SCENARIOS}" ]]                && export SCENARIOS=leaderboard/data/all_towns_traffic_scenarios_public.json # scenarios
[[ -z "${CHECKPOINT_ENDPOINT}" ]]      && export CHECKPOINT_ENDPOINT=results/result.json # results file
[[ -z "${SAVE_PATH}" ]]                && export SAVE_PATH=data/eval # path for saving episodes while evaluating
[[ -z "${RESUME}" ]]                   && export RESUME=True
[[ -z "${CUSTOM_ROUTE_TIMEOUT}" ]]     && export CUSTOM_ROUTE_TIMEOUT=370
[[ -z "${HAS_DISPLAY}" ]]              && export HAS_DISPLAY=0 # set to 1 to enable visualisation. Wrap vis code in `if os.getenv("HAS_DISPLAY") == "1"` check

# Agent params
# Note: Don't need this when running inside Docker since we specify this in the user commands in Dockerfile
[[ -z "${TEAM_AGENT}" ]]               && export TEAM_AGENT=team_code/interfuser_agent.py # agent
[[ -z "${TEAM_CONFIG}" ]]              && export TEAM_CONFIG=team_code/interfuser_config.py # model checkpoint, not required for expert

# Don't need this if building a docker image but shouldn't harm
export PYTHONPATH="${CARLA_ROOT}/PythonAPI/carla/dist/carla-0.9.10-py3.7-linux-x86_64.egg:${SCENARIO_RUNNER_ROOT}:${CARLA_ROOT}/PythonAPI/carla:${LEADERBOARD_ROOT}:${RAI_LEADERBOARD_ROOT}:${TEAM_CODE_ROOT}:${USER_CODE_ROOT}:${PYTHONPATH}"

# To set a variable explicitly, for example, to enable visualisation:
# export HAS_DISPLAY=1
