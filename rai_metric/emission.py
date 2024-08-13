from codecarbon import EmissionsTracker
import numpy as np

#from core.utility import get_nn_model_name
class Emission:
    """
    Class for carbon emission calculations
    """
    def __init__(self):
        self.__emissions = 0.0
        self.__emissions_index = 0.0
        self.__tracker = EmissionsTracker(save_to_file=False, on_csv_write='update', tracking_mode='process')
        self.energy_consumptions = []
        self.__total_inference_energy = -1
        self.__mean_inference_energy = -1
        self.__total_train_energy = -1

    def start_emissions_tracker(self):
        self.__tracker.start()
    
    def stop_emissions_tracker(self):
        self.__emissions : float = self.__tracker.stop()
        if self.__emissions != None:
            self.energy_consumptions.append(self.__emissions)
    
    def get_emissions_index(self)->float:
        if self.__emissions_index == 0 :
            self.__calculate_emissions_index()
            
        return self.__emissions_index
    
    def get_total_inference_emissions(self)->float:
        self.__total_inference_energy = np.sum(self.energy_consumptions)
        return self.__total_inference_energy
    
    def get_mean_inference_emissions(self)->float:
        if len(self.energy_consumptions) == 0:
            return 0.0
        self.__mean_inference_energy = np.mean(self.energy_consumptions)
        return self.__mean_inference_energy
    
    def reset_emissions(self):
        self.energy_consumptions = []
    
    def get_training_emissions(self, model)->float:
        if self.__total_train_energy == -1:
            self.estimate_training_emission(model)

        return self.__total_train_energy
    
    def __calculate_emissions_index(self):
        self.__mean_inference_energy = np.mean(self.energy_consumptions)
        if self.__mean_inference_energy <= 500:
            self.__emissions_index = 3
        elif self.__mean_inference_energy > 500 and self.emissions <= 10000:
            self.__emissions_index = 2
        else:
            self.__emissions_index = 1