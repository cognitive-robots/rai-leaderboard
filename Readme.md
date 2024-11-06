## RAI-Leaderboard

### Cloning Repositories

1. If you are working with an existing agent, move the `team_code` directory outside the `leaderboard` directory.

2. If you wish to host your agent code online, fork your own version of the [rai-leaderboard](https://github.com/cognitive-robots/rai-leaderboard) so you can modify it easily for your agent.

    *If you prefer to clone the repositories directly, proceed with steps 3-5 below, or skip to step 6 to add them as git submodules.*

3. Clone the `leaderboard-1.0` branch from the official Carla repository:
    ```bash
    git clone -b leaderboard-1.0 --single-branch https://github.com/carla-simulator/leaderboard.git
    ```

4. Similarly, clone the `leaderboard-1.0` branch of the Carla ScenarioRunner:
    ```bash
    git clone -b leaderboard-1.0 --single-branch https://github.com/carla-simulator/scenario_runner.git
    ```

5. Next, clone the `rai-leaderboard` repository (or your fork of it) and name it `rai` using the following command:
    ```bash
    git clone -b main https://github.com/cognitive-robots/rai-leaderboard.git rai # or use the URL of your fork
    ```

6. If you are adding these repositories to an existing git repository and wish to include them as submodules, use the following commands:
    ```bash
    git submodule add -b leaderboard-1.0 https://github.com/carla-simulator/leaderboard.git
    git submodule add -b leaderboard-1.0 https://github.com/carla-simulator/scenario_runner.git
    git submodule add -b main https://github.com/cognitive-robots/rai-leaderboard.git rai # or use the URL of your fork
    ```

    **Note:** In the command for the `rai-leaderboard` repository, we are naming the submodule `rai`. Ensure you use the full command as shown.



### Setting Up the Environment

- Update environment variables in `rai/scripts/env_var.sh`.

- Import the RAI base agent and update your team agent’s base class from `autonomous_agent.AutonomousAgent` to `base_agent.BaseAgent` as shown below:
    ```python
    from rai.autoagents import base_agent

    class MyAgent(base_agent.BaseAgent):
    ```



### Running Tests

#### Carla Server

Start the Carla server before running the agent.

##### Without Docker
   ```bash
   cd <your carla installation path>
   ./CarlaUE4.sh
   ```

##### With Docker

   For detailed instructions on running the Carla server inside Docker, refer to the [Carla documentation](https://carla.readthedocs.io/en/latest/build_docker/).

   A quick command to get started is shown below:

   ```bash
   docker run --privileged --gpus all --net=host -e DISPLAY=${DISPLAY} -it -e SDL_VIDEODRIVER=x11 -v /tmp/.X11-unix:/tmp/.X11-unix carlasim/carla:0.9.10.1 /bin/bash
   # launch carla inside the container
   ./CarlaUE4.sh
   ```

#### Agent

##### Without Docker

To run the evaluation locally without using Docker:
```bash
bash rai/scripts/run_evaluation.sh
```

##### With Docker

To run with Docker:

1. First, create a Docker image for your agent. Ensure the `team_code` directory is outside the leaderboard.

2. Update `rai/scripts/make_docker.sh` to include agent-specific files you want to copy to the Docker container, such as `requirements.txt`, model weights, etc.

3. Lastly, update the USER COMMANDS section in `rai/scripts/Dockerfile.master` to include agent-specific environment variables and install any necessary Python/Conda packages.

4. Build the Docker image by running:
    ```bash
    bash rai/scripts/make_docker.sh -t <image:tag> # for example, -t interfuser:0.1
    ```

5. Once the image is built, run the Docker image with:
    ```bash
    docker run --ipc=host --gpus all --net=host -e DISPLAY=$DISPLAY -it -e SDL_VIDEODRIVER=x11 -v /tmp/.X11-unix:/tmp/.X11-unix <image:tag> /bin/bash
    ```

6. Finally, run the evaluation script within the Docker container:
    ```bash
    bash rai/scripts/run_evaluation.sh
    ```



### Submission

To submit an agent to the RAI Carla Challenge:

1. First, create a Conda environment and install EvalAI, which is EvalAI's command-line interface package:
    ```bash
    conda create -n evalai-cli python=3.7
    conda activate evalai-cli
    pip install evalai~=1.3.18
    ```

2. If the Conda environment already exists, update the Conda environment path in `rai/scripts/submit_evalai.sh` and execute the script. This will activate your Conda environment and submit the agent:
    ```bash
    bash rai/scripts/submit_evalai.sh -t <image:tag>
    ```
