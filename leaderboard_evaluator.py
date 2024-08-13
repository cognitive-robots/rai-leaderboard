import copy
import sys
import traceback
import warnings
from tabulate import tabulate

import carla

from leaderboard.autoagents.agent_wrapper import  AgentError
from leaderboard.leaderboard_evaluator import LeaderboardEvaluator
from srunner.scenariomanager.carla_data_provider import CarlaDataProvider
from leaderboard.leaderboard_evaluator import sensors_to_icons
from leaderboard.envs.sensor_interface import SensorInterface, SensorConfigurationInvalid

from rai.core.responsibleAI import RAIModels
from rai.core.variations import RAIVariation, RAI_CASES
from rai.autoagents.agent_wrapper import RAIAgentWrapper
from rai.scenarios.scenario_manager import RAIScenarioManager
from rai.scenarios.route_scenario import RAIRouteScenario
from rai.utils.configuration_utility import RAIConfigurationUtility
from rai.utils.route_indexer import RAIRouteIndexer
from rai.utils.utility import shift_environment
from rai.utils.weathers import Weathers

class RAILeaderboardEvaluator(LeaderboardEvaluator):
    """
    RAI leaderboard evaluator class dervied from leaderboard evaluator class
    """
    def __init__(self, args, statistics_manager):
        super().__init__(args, statistics_manager)
        #Create agent object
        self.agent_instance = None
        self.is_rai = args.is_rai
        self.weathers = Weathers()
        self.config_utils = RAIConfigurationUtility()
        #dictionary to organise sensors
        self.sensor_types = {}
        # Create the ScenarioManager
        self.manager = RAIScenarioManager(args.timeout, args.debug > 1)
        self.n_weather_conditions = 5

    def _organise_sensors(self, sensors):
        """
        Collect meta sensors info to inform perturbation process
        """
        #Ensure that at least one sensor exist
        assert(len(sensors) > 0)
        for sensor in sensors:
            if sensor['type'] == 'sensor.camera.rgb':
                if 'camera' in self.sensor_types:
                    self.sensor_types['camera'].append({'type': 'camera', 'id': sensor['id']})  
                else: 
                    self.sensor_types['camera'] = [{'type': 'camera', 'id': sensor['id']}]
            elif sensor['type'] ==  'sensor.lidar.ray_cast':
                if 'lidar' in self.sensor_types:
                    self.sensor_types['lidar'].append({'type': 'lidar', 'id': sensor['id']})  
                else: 
                    self.sensor_types['lidar'] = [{'type': 'lidar', 'id': sensor['id']}]
            elif sensor['type'] ==  'sensor.other.gnss':
                if 'gnss' in self.sensor_types:
                    self.sensor_types['gnss'].append({'type': 'gnss', 'id': sensor['id']})  
                else: 
                    self.sensor_types['gnss'] = [{'type': 'gnss', 'id': sensor['id']}]
            elif sensor['type'] ==  'sensor.other.imu':
                if 'imu' in self.sensor_types:
                    self.sensor_types['imu'].append({'type': 'imu', 'id': sensor['id']})  
                else: 
                    self.sensor_types['imu'] = [{'type': 'imu', 'id': sensor['id']}]
            elif sensor['type'] ==  'sensor.speedometer':
                if 'speedometer' in self.sensor_types:
                    self.sensor_types['speedometer'].append({'type': 'speedometer', 'id': sensor['id']})  
                else: 
                    self.sensor_types['speedometer'] = [{'type': 'speedometer', 'id': sensor['id']}]

    def create_agent_with_sensors(self, args, config):
        """
        Create a dummy agent to retrive basic sensor info when sensor is not setup yet
        """
        try:
            agent_class_name = getattr(self.module_agent, 'get_entry_point')()
            agent_instance = getattr(self.module_agent, agent_class_name)(args.agent_config)
            # Check and store the sensors
            self.sensors = agent_instance.sensors()
            self._organise_sensors(self.sensors)
            agent_instance.destroy()
            agent_instance = None

        except SensorConfigurationInvalid as e:
            # The sensors are invalid -> set the ejecution to rejected and stop
            print("\n\033[91mThe sensor's configuration used is invalid:")
            print("> {}\033[0m\n".format(e))
            traceback.print_exc()

            crash_message = "Agent's sensors were invalid"
            entry_status = "Rejected"

            self._register_statistics(config, args.checkpoint, entry_status, crash_message)
            self._cleanup()
            sys.exit(-1)

        except Exception as e:
            # The agent setup has failed -> start the next route
            print("\n\033[91mCould not set up the required agent:")
            print("> {}\033[0m\n".format(e))
            traceback.print_exc()

            crash_message = "Agent couldn't be set up"

            self._register_statistics(config, args.checkpoint, entry_status, crash_message)
            self._cleanup()
            return        

    def _load_and_run_scenario(self, args, config):
        """
        Load and run the scenario given by config.

        Depending on what code fails, the simulation will either stop the route and
        continue from the next one, or report a crash and stop.
        """
        crash_message = ""
        entry_status = "Started"
        print("\n\033[1m========= Preparing {} (repetition {}) =========".format(config.name, config.repetition_index))
        print("> Setting up the agent\033[0m")

        # Prepare the statistics of the route
        route_name = config.name +'_'+ config.route_type + '_' + config.run_id
        self.statistics_manager.set_route(route_name, int(config.run_id.split('_')[0]))
        print("Route setting completed...")
        # Set up the user's agent, and the timer to avoid freezing the simulation
        try:
            self._agent_watchdog.start()
            agent_class_name = getattr(self.module_agent, 'get_entry_point')()
            self.agent_instance = getattr(self.module_agent, agent_class_name)(args.agent_config)
            config.agent = self.agent_instance

            # Check and store the sensors
            if not self.sensors:
                self.sensors = self.agent_instance.sensors()
                track = self.agent_instance.track
                
                #check that sensors have been organised
                if not self.sensor_types:
                    self._organise_sensors(self.sensors)

                RAIAgentWrapper.validate_sensor_configuration(self.sensors, track, args.track)

                self.sensor_icons = [sensors_to_icons[sensor['type']] for sensor in self.sensors]
                self.statistics_manager.save_sensors(self.sensor_icons, args.checkpoint)

            self._agent_watchdog.stop()
            print("Sensor data inspected and stored...")

        except SensorConfigurationInvalid as e:
            # The sensors are invalid -> set the ejecution to rejected and stop
            print("\n\033[91mThe sensor's configuration used is invalid:")
            print("> {}\033[0m\n".format(e))
            traceback.print_exc()

            crash_message = "Agent's sensors were invalid"
            entry_status = "Rejected"

            self._register_statistics(config, args.checkpoint, entry_status, crash_message)
            self._cleanup()
            sys.exit(-1)

        except Exception as e:
            # The agent setup has failed -> start the next route
            print("\n\033[91mCould not set up the required agent:")
            print("> {}\033[0m\n".format(e))
            traceback.print_exc()

            crash_message = "Agent couldn't be set up"

            self._register_statistics(config, args.checkpoint, entry_status, crash_message)
            self._cleanup()
            return

        print("\033[1m> Loading the world\033[0m")

        # Load the world and the scenario
        try:
            self._load_and_wait_for_world(args, config.town, config.ego_vehicles)
            self._prepare_ego_vehicles(config.ego_vehicles, False)

            # If RAI_CASE is SHIFT, shift the environment
            if config.route_type == RAIVariation.SHIFT:
                shift_environment(world = self.world, _map = CarlaDataProvider._map, client = self.client, traffic_manager = self.traffic_manager, args=args)

            scenario = RAIRouteScenario(world=self.world, config=config, debug_mode=args.debug, \
                                     custom_timeout = args.customRouteTimeout)
            print("Scenario instance created...")
            self.statistics_manager.set_scenario(scenario.scenario)

            # self.agent_instance._init()
            # self.agent_instance.sensor_interface = SensorInterface()

            # Night mode
            if config.weather.sun_altitude_angle < 0.0:
                for vehicle in scenario.ego_vehicles:
                    vehicle.set_light_state(carla.VehicleLightState(self._vehicle_lights))

            # Load scenario and run it
            if args.record:
                self.client.start_recorder("{}/{}_rep{}.log".format(args.record, config.name, config.repetition_index))
            print("Loading scenario...")
            self.manager.load_scenario(scenario, self.agent_instance, config.repetition_index)
            print("Scenario loading complete...")

        except Exception as e:
            # The scenario is wrong -> set the ejecution to crashed and stop
            print("\n\033[91mThe scenario could not be loaded:")
            print("> {}\033[0m\n".format(e))
            traceback.print_exc()

            crash_message = "Simulation crashed"
            entry_status = "Crashed"

            self._register_statistics(config, args.checkpoint, entry_status, crash_message)

            if args.record:
                self.client.stop_recorder()

            self._cleanup()
            sys.exit(-1)

        print("\033[1m> Running the route\033[0m")

        # Run the scenario
        try:
            self.manager.run_scenario(config)

        except AgentError as e:
            # The agent has failed -> stop the route
            print("\n\033[91mStopping the route, the agent has crashed:")
            print("> {}\033[0m\n".format(e))
            traceback.print_exc()

            crash_message = "Agent crashed"

        except Exception as e:
            print("\n\033[91mError during the simulation:")
            print("> {}\033[0m\n".format(e))
            traceback.print_exc()

            crash_message = "Simulation crashed"
            entry_status = "Crashed"

        # Stop the scenario
        try:
            print("\033[1m> Stopping the route\033[0m")
            self.manager.stop_scenario()
            self._register_statistics(config, args.checkpoint, entry_status, crash_message)

            if args.record:
                self.client.stop_recorder()

            # Remove all actors
            scenario.remove_all_actors()

            self._cleanup()

        except Exception as e:
            print("\n\033[91mFailed to stop the scenario, the statistics might be empty:")
            print("> {}\033[0m\n".format(e))
            traceback.print_exc()

            crash_message = "Simulation crashed"

        if crash_message == "Simulation crashed":
            sys.exit(-1)

    def _calculate_total_runs(self):
        """
        Calculate total runs based on each case in RAI_CASES.
        """
        total_runs = 0
        if RAIVariation.REGULAR in RAI_CASES:
            total_runs += 1
        if RAIVariation.SHIFT in RAI_CASES:
            total_runs += 1
        if RAIVariation.DISTORTION1 in RAI_CASES:
            # If Camera is present, update the total_runs
            if 'camera' in self.sensor_types:
                total_runs += len(self.sensor_types['camera'])
            # If LIDAR is present, update the total_runs
            if 'lidar' in self.sensor_types:
                total_runs += len(self.sensor_types['lidar'])
        if RAIVariation.DISTORTION2 in RAI_CASES:
            # If Camera is present, update the total_runs
            if 'camera' in self.sensor_types:
                total_runs += len(self.sensor_types['camera'])
            # If LIDAR is present, update the total_runs
            if 'lidar' in self.sensor_types:
                total_runs += len(self.sensor_types['lidar'])
        if RAIVariation.DISTORTION3 in RAI_CASES:
            # If IMU is present, update the total_runs
            if 'imu' in self.sensor_types:
                total_runs += 1
            # If GNSS is present, update the total_runs
            if 'gnss' in self.sensor_types:
                total_runs += 1
            # If Speedometer is present, update the total_runs
            if 'speedometer' in self.sensor_types:
                total_runs += 1
        if RAIVariation.WEATHER in RAI_CASES:
                total_runs += self.n_weather_conditions
        return total_runs

    def run(self, args):
        """
        Run the challenge mode
        """
        route_indexer = RAIRouteIndexer(args.routes, args.scenarios, args.repetitions, args.routes_subset)

        warnings.warn(f"The argument args.repetitions (= {args.repetitions}) will be ignored when args.is_rai is True!")

        trial_idx = 0
        if route_indexer.peek():
            # setup config with additional variables related to RAI
            config = route_indexer.next()
            config.is_rai = True #TODO: use self.is_rai?
            config.frame_rate = self.frame_rate
            #create a dummy agent to retrive basic sensor info when sensor is not setup yet
            self.create_agent_with_sensors(args, config)

            # get total runs from all RAI_CASES
            total_runs = self._calculate_total_runs()
            route_indexer.total = total_runs

            args.resume = False # TODO: this doesn't seem like a good idea!!
            if args.resume:
                route_indexer.resume(args.checkpoint)
                self.statistics_manager.resume(args.checkpoint)
            else:
                self.statistics_manager.clear_record(args.checkpoint)
                route_indexer.save_state(args.checkpoint)

            args.resume = True
            #Loop through all of the cases that we need to assess to obtain RAI
            run_id = 0
            while trial_idx < len(RAI_CASES):
                # Get an instance of the RAI class interface
                self.rai_interface = RAIModels(self.sensors)
                new_config = copy.copy(config)
                new_config.rai_interface = self.rai_interface
                new_config.route_type = RAI_CASES[trial_idx]
                new_config.weather = self.weathers.clear_weather() # default weather

                # Collect configurations based on the RAI_CASE/ route_type
                configs = self.config_utils.collect_configs(new_config, self.sensor_types)

                if new_config.route_type == RAIVariation.WEATHER:
                    assert (self.n_weather_conditions == len(configs)), "The number of weather conditions must match"

                for config_i in configs:
                    print(f"Executing: {config_i.route_type} ")
                    #print('weather.. ', config_i.weather)
                    if config_i.sensor_to_noise is not None:
                        print(f"... with sensor ID: {config_i.sensor_to_noise['id']}")

                    config_i.run_id = str(run_id) + '_of_' + str(total_runs)
                    self._load_and_run_scenario(args, config_i)
                    route_indexer.save_state(args.checkpoint)
                    run_id += 1

                trial_idx += 1

            print("\033[1m> Registering the global statistics\033[0m")
            global_stats_record = self.statistics_manager.compute_global_statistics(route_indexer.total)
            self.statistics_manager.save_global_record(global_stats_record, self.sensor_types, route_indexer.total,\
                                                         args.checkpoint, args.is_rai)

        
            header = ['Criterion', 'Result']
            list_statistics = [header]

            for rai_case in global_stats_record.rai_scores.keys():
                if rai_case in ['Emission_Per_Sec', 'Emission_Per_Route']:
                    list_statistics.extend([[rai_case, '{:.6f}'.format(global_stats_record.rai_scores[rai_case])+ 'Kg']])
                else:
                    list_statistics.extend([[rai_case, '{:.6f}'.format(global_stats_record.rai_scores[rai_case])]])

            #RAI result organisation
            output = ''
            output += tabulate(list_statistics, tablefmt='fancy_grid')
            output += "\n"
            print(output)

        return
