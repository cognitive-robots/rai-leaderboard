#!/bin/bash

# Function to handle arguments
handle_arguments() {
    while [[ "$#" -gt 0 ]]; do
        case $1 in
            --docker) DOCKER="$2"; shift ;;
            *) echo "Unknown parameter passed: $1"; exit 1 ;;
        esac
        shift
    done
}

# Call the function to handle arguments
handle_arguments "$@"

# Default value if DOCKER is not set
: "${DOCKER:=True}"


export CARLA_ROOT="<Path to your CARLA PythonAPI>"
export LEADERBOARD_ROOT="<Path to your Carla leaderboard root>"
export RAI_LEADERBOARD_ROOT="<Path to your rai leaderboard root>"
export SCENARIO_RUNNER_ROOT="<Path to your scenario runner root>"
export TEAM_CODE_ROOT="<Path to your team_code root>"
export USER_CODE_ROOT="<Path to your user code root (e.g., ../interfuser/)>"

if [ "$DOCKER" = False ]
then
    export PYTHONPATH="${CARLA_ROOT}/PythonAPI/carla/dist/carla-0.9.10-py3.7-linux-x86_64.egg:${SCENARIO_RUNNER_ROOT}:${CARLA_ROOT}/PythonAPI/carla:${LEADERBOARD_ROOT}:${RAI_LEADERBOARD_ROOT}:${TEAM_CODE_ROOT}:${USER_CODE_ROOT}:${PYTHONPATH}"

    # export LEADERBOARD_ROOT=leaderboard
    export CHALLENGE_TRACK_CODENAME=SENSORS
    export PORT=2000 # same as the carla server port
    export TM_PORT=2500 # port for traffic manager, required when spawning multiple servers/clients
    export DEBUG_CHALLENGE=0 # debug information from the simulator
    export REPETITIONS=1 # multiple evaluation runs
    export ROUTES=leaderboard/data/routes_devtest.xml # routes
    export SCENARIOS=leaderboard/data/all_towns_traffic_scenarios_public.json # scenarios
    export TEAM_AGENT=leaderboard/team_code/interfuser_agent.py # agent
    export TEAM_CONFIG=leaderboard/team_code/interfuser_config.py # model checkpoint, not required for expert
    export CHECKPOINT_ENDPOINT=results/interfuser_result.json # results file
    export SAVE_PATH=data/eval # path for saving episodes while evaluating
    export RESUME=True
    export CUSTOM_ROUTE_TIMEOUT=370
    export HAS_DISPLAY=0 # set to 1 to enable visualisation. Wrap vis code in `if os.getenv("HAS_DISPLAY") == "1"` check
fi