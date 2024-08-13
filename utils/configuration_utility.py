
import copy
from rai.core.variations import RAIVariation
from rai.utils.weathers import Weathers
from rai.utils.sensors import RAISensors

class RAIConfigurationUtility:
    """
    A class to collect configurations that are passed to
    load_and_run_scenario to run the simulation
    """
    def __init__(self) -> None:
        self.weathers = Weathers()

    def collect_configs(self, config, sensor_types):
        """
        Collect configs based on the RAI_CASE/ route_type which 
        will be passed to _load_and_run_scenario() in leaderboard_evaluator
        """
        if config.route_type == RAIVariation.WEATHER:
            return self.collect_weather_configs(config)
        elif config.route_type in [RAIVariation.DISTORTION1, RAIVariation.DISTORTION2, RAIVariation.DISTORTION3]:
            return self.collect_sensor_configs(config, sensor_types)
        else:
            return [config]

    def collect_weather_configs(self, config):
        """
        Collect weather configs
        """
        configs = []
        all_weathers = self.weathers.get_weathers()
        for weather in all_weathers:
            new_config = copy.copy(config)
            new_config.weather = weather
            configs.append(new_config)

        return configs

    def collect_sensor_configs(self, config, sensor_types):
        """
        Collect all sensor configs for the particular RAI_CASE/ 
        route_type
        """
        tmp_route_type = config.route_type
        configs = []
        if tmp_route_type == RAIVariation.DISTORTION3:
            if 'imu' in sensor_types:
                config_imu = copy.copy(config)
                config_imu.route_type = tmp_route_type + RAISensors.IMU
                #Run the route and noise the sensors one after the other in each run
                config_imu.sensor_to_noise = sensor_types['imu'][0]
                print(f"route_type: {config_imu.route_type}, sensor: {sensor_types['imu'][0]}")
                configs.append(config_imu)

            if 'gnss' in sensor_types:
                config_gnss = copy.copy(config)
                config_gnss.route_type = tmp_route_type + RAISensors.GNSS
                #Run the route and noise the sensors one after the other in each run
                config_gnss.sensor_to_noise = sensor_types['gnss'][0]
                print(f"route_type: {config_gnss.route_type}, sensor: {sensor_types['gnss'][0]}")
                configs.append(config_gnss)

            if 'speedometer' in sensor_types:
                config_speedometer = copy.copy(config)
                config_speedometer.route_type = tmp_route_type + RAISensors.SPEEDOMETER
                #Run the route and noise the sensors one after the other in each run
                config_speedometer.sensor_to_noise = sensor_types['speedometer'][0]
                print(f"route_type: {config_speedometer.route_type}, sensor: {sensor_types['speedometer'][0]}")
                configs.append(config_speedometer)
        else:

            if 'camera' in sensor_types:
                sensor_len = len(sensor_types['camera'])
                sensor_itr = 0
                config_camera = copy.copy(config)
                config_camera.route_type = tmp_route_type + RAISensors.CAMERA
                print(tmp_route_type + RAISensors.CAMERA)
                #Run the route and noise the sensors one after the other in each run
                while sensor_itr < sensor_len:
                    config_camera_tmp = copy.copy(config_camera)
                    config_camera_tmp.sensor_to_noise = sensor_types['camera'][sensor_itr]
                    print(f"route_type: {config_camera_tmp.route_type}, sensor: {sensor_types['camera'][sensor_itr]}")
                    configs.append(config_camera_tmp)
                    sensor_itr += 1

            if 'lidar' in sensor_types:
                sensor_len = len(sensor_types['lidar'])
                sensor_itr = 0
                config_lidar = copy.copy(config)
                config_lidar.route_type = tmp_route_type + RAISensors.LIDAR
                #Run the route and noise the sensors one after the other in each run
                while sensor_itr < sensor_len:
                    config_lidar_tmp = copy.copy(config_lidar)
                    config_lidar_tmp.sensor_to_noise = sensor_types['lidar'][sensor_itr]
                    print(f"route_type: {config_lidar_tmp.route_type}, sensor: {sensor_types['lidar'][sensor_itr]}")
                    configs.append(config_lidar_tmp)
                    sensor_itr += 1

        return configs