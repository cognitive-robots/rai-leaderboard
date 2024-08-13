
from rai.core.variations import RAIVariation
from rai.utils.sensors import RAISensors
from rai_metric.emission import Emission
from rai_metric.robustness import Robustness


class RAIModels:
    """
    Class for starting and stopping the emission tracker and perturbing
    sensor data
    """
    def __init__(self, sensors):
        self.__robuster = Robustness(sensors)
        self.__emitter = Emission()
        self.no_predictions = 0
        self.emission_calc_rate = 20

    def start_emission_tracker(self):
        self.__emitter.start_emissions_tracker()

    def stop_emission_tracker(self):
        self.__emitter.stop_emissions_tracker()

    def get_emissions_per_sec(self):
        return self.__emitter.get_mean_inference_emissions()
    
    def get_total_emissions(self):
        return self.__emitter.get_total_inference_emissions()
    
    def reset_emissions(self):
        return self.__emitter.reset_emissions()

    def perturb_data(self, input_data, sensor_info, noise_type):
        """
        Manipulate frames and scenarios and then return the updated data
        """
        input_to_noise = input_data[sensor_info['id']]
        if noise_type == RAIVariation.DISTORTION1 + RAISensors.CAMERA:
            noised_input = self.__robuster.add_salt_and_pepper_noise(input_to_noise, sensor_info)
            input_data[sensor_info['id']][1][:, :, :3] = noised_input

        elif noise_type == RAIVariation.DISTORTION1+ RAISensors.LIDAR:
            noised_input = self.__robuster.add_salt_and_pepper_noise(input_to_noise, sensor_info)
            input_data[sensor_info['id']] = noised_input

        elif noise_type == RAIVariation.DISTORTION2 + RAISensors.CAMERA:
            noised_input = self.__robuster.add_occlussion_noise(input_to_noise, sensor_info)
            input_data[sensor_info['id']][1][:, :, :3] = noised_input

        elif noise_type == RAIVariation.DISTORTION2 + RAISensors.LIDAR:
            noised_input = self.__robuster.add_occlussion_noise(input_to_noise, sensor_info)
            input_data[sensor_info['id']] = noised_input
        
        elif noise_type == RAIVariation.DISTORTION3 + RAISensors.GNSS:
            noised_input = self.__robuster.add_random_noise(input_to_noise, sensor_info)
            input_data[sensor_info['id']][1][:] = noised_input
        
        elif noise_type == RAIVariation.DISTORTION3 + RAISensors.IMU:
            noised_input = self.__robuster.add_random_noise(input_to_noise, sensor_info)   
            input_data[sensor_info['id']][1][:] = noised_input
        
        elif noise_type == RAIVariation.DISTORTION3 + RAISensors.SPEEDOMETER:
            noised_input = self.__robuster.add_random_noise(input_to_noise, sensor_info)
            input_data[sensor_info['id']] = (input_data[sensor_info['id']][0], {'speed':noised_input})

        return input_data