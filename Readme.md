## RAI-Leaderboard

### Cloning Repositories

1. Clone the `leaderboard-1.0` branch from the official Carla repository:
    ```bash
    git clone -b leaderboard-1.0 --single-branch https://github.com/carla-simulator/leaderboard.git
    ```

2. Similarly, clone the `leaderboard-1.0` branch of the Carla ScenarioRunner:
    ```bash
    git clone -b leaderboard-1.0 --single-branch https://github.com/carla-simulator/scenario_runner.git
    ```

3. Next, clone the RAI Carla repository and name it `rai` using the following command:
    ```bash
    git clone -b main https://github.com/cognitive-robots/rai-leaderboard.git rai
    ```

4. If you are adding these repositories to an existing Git repository and wish to include them as submodules, use the following commands:
    ```bash
    git submodule add -b leaderboard-1.0 https://github.com/carla-simulator/leaderboard.git
    git submodule add -b leaderboard-1.0 https://github.com/carla-simulator/scenario_runner.git
    git submodule add -b main https://github.com/cognitive-robots/rai-leaderboard.git rai
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

#### Without Docker

To run the evaluation locally without creating a Docker image:
```bash
bash rai/scripts/run_evaluation.sh
```

#### With Docker

To run with Docker:

1. First, create a Docker image for your agent. Ensure the `team_code` directory is outside the leaderboard.

2. Update `rai/scripts/make_docker.sh` to include agent-specific files you want to copy to the Docker container, such as `requirements.txt`, model weights, etc.

3. Lastly, update the USER COMMANDS section in `rai/scripts/Dockerfile.master` to include agent-specific environment variables and install any necessary Python/Conda packages.

4. Build the Docker image by running:
    ```bash
    bash rai/scripts/make_docker.sh
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
