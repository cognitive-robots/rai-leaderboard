#!/bin/bash

# Get the relative path to the bash directory
SCRIPT_DIR="$( dirname "${BASH_SOURCE[0]}" )"

# load environment variables
source $SCRIPT_DIR/env_var.sh --docker False

#Uncomment this to give permission to read how much electric power your hardware consume.
#Note that this require super user priviledge to run.
chmod +r /sys/class/powercap/intel-rapl/intel-rapl:0/energy_uj

python3 ${RAI_LEADERBOARD_ROOT}/main.py \
--scenarios=${SCENARIOS}  \
--routes=${ROUTES} \
--repetitions=${REPETITIONS} \
--track=${CHALLENGE_TRACK_CODENAME} \
--checkpoint=${CHECKPOINT_ENDPOINT} \
--agent=${TEAM_AGENT} \
--agent-config=${TEAM_CONFIG} \
--debug=${DEBUG_CHALLENGE} \
--record=${RECORD_PATH} \
--resume=${RESUME} \
--port=${PORT} \
--trafficManagerPort=${TM_PORT} \
--customRouteTimeout=${CUSTOM_ROUTE_TIMEOUT}
