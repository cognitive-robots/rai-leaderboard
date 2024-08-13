
from leaderboard.autoagents.agent_wrapper import AgentWrapper

class RAIAgentWrapper(AgentWrapper):
    """
    RAIAgentWrapper derived from the AgentWrapper class, which is
    required for tracking and checking of used sensors
    """
    def __call__(self, config):
        """
        Pass the call directly to the agent
        """
        return self._agent(config)