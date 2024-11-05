FROM nvidia/cuda:11.7.1-cudnn8-devel-ubuntu20.04

ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG http_proxy

# Update package repositories and install locales
RUN apt-get update && apt-get install -y --reinstall locales && \
    locale-gen en_US.UTF-8 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set locale environment variables
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US
ENV LC_ALL en_US.UTF-8
# Set environment variables to avoid interactive prompts during the build
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=GMT

RUN apt-get update && apt-get install -y --no-install-recommends \
     build-essential \
     cmake \
     git \
     curl \
     vim \
     ca-certificates \
     libjpeg-dev \
     libpng16-16 \
     libtiff5 \
     libpng-dev && \
     rm -rf /var/lib/apt/lists/*

# installing conda
RUN curl -o ~/miniconda.sh -LO https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh  && \
     chmod +x ~/miniconda.sh && \
     ~/miniconda.sh -b -p /opt/conda && \
     rm ~/miniconda.sh && \
     /opt/conda/bin/conda create -n python37 python=3.7 numpy networkx scipy six requests && \
     /opt/conda/bin/conda clean -ya

# Set default Conda environment
RUN /opt/conda/bin/conda init bash && \
     echo "conda activate python37" >> ~/.bashrc

RUN packages='py_trees==0.8.3 psutil shapely six dictor requests ephem tabulate' && \
     /opt/conda/envs/python37/bin/pip install --no-cache-dir ${packages}

WORKDIR /workspace

ENV CARLA_ROOT "/workspace/CARLA"
ENV SCENARIO_RUNNER_ROOT "/workspace/scenario_runner"
ENV LEADERBOARD_ROOT "/workspace/leaderboard"
ENV RAI_LEADERBOARD_ROOT "/workspace/rai"
ENV TEAM_CODE_ROOT "/workspace/team_code"

COPY .tmp/PythonAPI ${CARLA_ROOT}/PythonAPI
COPY .tmp/scenario_runner ${SCENARIO_RUNNER_ROOT}
COPY .tmp/leaderboard ${LEADERBOARD_ROOT}
COPY .tmp/rai ${RAI_LEADERBOARD_ROOT}
COPY .tmp/team_code ${TEAM_CODE_ROOT}

ENV PATH "/workspace/CARLA/PythonAPI/carla/dist/carla-0.9.10-py3.7-linux-x86_64.egg:/opt/conda/envs/python37/bin:/opt/conda/envs/bin:$PATH"
ENV PYTHONPATH "/workspace/CARLA/PythonAPI/carla/dist/carla-0.9.10-py3.7-linux-x86_64.egg:${SCENARIO_RUNNER_ROOT}:${CARLA_ROOT}/PythonAPI/carla:${LEADERBOARD_ROOT}:${RAI_LEADERBOARD_ROOT}:${TEAM_CODE_ROOT}:${PYTHONPATH}"

RUN mkdir -p /workspace/results && \
    chmod +x /workspace/leaderboard/scripts/run_evaluation.sh

# Install additional packages and leaderboard dependencies
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libgtk2.0-dev && \
    /opt/conda/envs/python37/bin/pip install --no-cache-dir -r /workspace/rai/requirements.txt && \
    rm -rf /var/lib/apt/lists/*

########################################################################################################################
########################################################################################################################
############                                BEGINNING OF USER COMMANDS                                      ############
########################################################################################################################
########################################################################################################################

### Example (InterFuser): Agent specific commands

# COPY .tmp/interfuser /workspace/interfuser
# COPY .tmp/requirements.txt /workspace/requirements.txt

# ENV PYTHONPATH ${PYTHONPATH}:"/workspace/interfuser"
# ENV TEAM_AGENT ${TEAM_CODE_ROOT}/interfuser_agent.py
# ENV TEAM_CONFIG ${TEAM_CODE_ROOT}/interfuser_config.py
# ENV CHALLENGE_TRACK_CODENAME SENSORS
# ENV RESUME True
# ENV MODEL_PATH ${TEAM_CODE_ROOT}/interfuser.pth.tar

# /opt/conda/envs/python37/bin/pip install my_package
# RUN /opt/conda/envs/python37/bin/pip install -r /workspace/requirements.txt

###

ENV TEAM_AGENT ${TEAM_CODE_ROOT}/npc_agent.py
ENV TEAM_CONFIG ${TEAM_CODE_ROOT}/YOUR_CONFIG_FILE
ENV CHALLENGE_TRACK_CODENAME SENSORS

########################################################################################################################
########################################################################################################################
############                                   END OF USER COMMANDS                                         ############
########################################################################################################################
########################################################################################################################

ENV SCENARIOS ${LEADERBOARD_ROOT}/data/all_towns_traffic_scenarios_public.json
ENV ROUTES ${LEADERBOARD_ROOT}/data/routes_training.xml
ENV REPETITIONS 1
ENV CHECKPOINT_ENDPOINT /workspace/results/results.json
ENV DEBUG_CHALLENGE 0
ENV HAS_DISPLAY 0

ENV HTTP_PROXY ""
ENV HTTPS_PROXY ""
ENV http_proxy ""
ENV https_proxy ""


CMD ["/bin/bash"]
