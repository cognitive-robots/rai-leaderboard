from leaderboard.autoagents.autonomous_agent import AutonomousAgent
from srunner.scenariomanager.timer import GameTime
from rai.core.variations import RAIVariation

class BaseAgent(AutonomousAgent):

    """
    RAI Autonomous agent base class. All user agents have to be derived from this class
    """

    def __call__(self, config):
        """
        Execute the agent call, e.g. agent()
        Returns the next vehicle controls
        """
        sensor_info = config.sensor_to_noise
        input_data = self.sensor_interface.get_data()

        if not config.is_rai:
            timestamp = GameTime.get_time()

            if not self.wallclock_t0:
                self.wallclock_t0 = GameTime.get_wallclocktime()
            wallclock = GameTime.get_wallclocktime()
            wallclock_diff = (wallclock - self.wallclock_t0).total_seconds()

            #print('======[Agent] Wallclock_time = {} / Sim_time = {}'.format(wallclock, timestamp))

            control = self.run_step(input_data, timestamp)
            control.manual_gear_shift = False

        else:
            control = None
            #Create an instance of RAI engine
            rai_interface = config.rai_interface

            #Count the '_' occurrences in the config.route_type string and
            #right-split if there are more than two entries. For example,
            #REGULAR_D1_LID --> REGULAR_D1 and REGULAR_W --> REGULAR_W.
            char_count = config.route_type.count('_')
            rai_case = config.route_type.rsplit('_', char_count-1)[0]

            #Perturb the sensor data if the rai_case is from D1, D2 or D3
            if rai_case in [RAIVariation.DISTORTION1, RAIVariation.DISTORTION2, RAIVariation.DISTORTION3]:
                input_data = rai_interface.perturb_data(input_data, sensor_info, config.route_type)

            timestamp = GameTime.get_time()

            if not self.wallclock_t0:
                self.wallclock_t0 = GameTime.get_wallclocktime()
            wallclock = GameTime.get_wallclocktime()
            #wallclock_diff = (wallclock - self.wallclock_t0).total_seconds()
            # only estimate emission for a select amount of time due to processng speed issues
            #print('======[Agent] Wallclock_time = {} / Sim_time = {}'.format(wallclock, timestamp))
           
            if rai_interface.no_predictions == 0:
                rai_interface.start_emission_tracker()
            control = self.run_step(input_data, timestamp)
            rai_interface.no_predictions += 1

            #Track power usage per second
            if rai_interface.no_predictions >= config.frame_rate: #rai_interface.emission_calc_rate:
                rai_interface.stop_emission_tracker()
                rai_interface.no_predictions = 0

            control.manual_gear_shift = False

        return control