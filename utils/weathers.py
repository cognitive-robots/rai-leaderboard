import carla


class Weathers:
    """
    A class containing different weather simulations for Carla
    """
    def __init__(self):
        pass

    def get_weathers(self):
        # Define a list of weather conditions
        weather_conditions = []

        weather_conditions.append(self.foggy_weather())
        weather_conditions.append(self.rainy_weather())
        weather_conditions.append(self.night_weather())
        weather_conditions.append(self.night_rainy_weather())
        weather_conditions.append(self.icy_weather())

        return weather_conditions

    def clear_weather(self):
        return carla.WeatherParameters(
            cloudiness=5.0,
            precipitation=0.0,
            precipitation_deposits=0.0,
            wind_intensity=0.0,
            sun_altitude_angle=60.0
        )

    def foggy_weather(self):
        return carla.WeatherParameters(
            cloudiness=70.0,
            fog_density=100.0,
            fog_distance=0.0,
            sun_altitude_angle=90.0,
            precipitation=0.0,
            precipitation_deposits=0.0,
            wind_intensity=10.0,
        )

    def rainy_weather(self):
        return carla.WeatherParameters(
            cloudiness=90.0,
            precipitation=100.0,
            precipitation_deposits=100.0,
            wind_intensity=50.0,
            sun_altitude_angle=90.0
        )

    def night_weather(self):
        return carla.WeatherParameters(
            sun_altitude_angle=-10.0,  # Set a low sun angle to simulate nighttime
            cloudiness=10.0,          # Adjust cloudiness as needed
            precipitation=0.0,        # No precipitation
            precipitation_deposits=0.0,
            wind_intensity=10.0,      # Adjust wind intensity as needed
            fog_density=0.0,          # No fog
            fog_distance=0.0
        )

    def night_rainy_weather(self):
        return carla.WeatherParameters(
            sun_altitude_angle=-10.0,  # Set a low sun angle to simulate nighttime
            cloudiness=10.0,          # Adjust cloudiness as needed
            precipitation=100.0,        # No precipitation
            precipitation_deposits=100.0,
            wind_intensity=30.0,      # Adjust wind intensity as needed
            fog_density=0.0,          # No fog
            fog_distance=0.0
        )

    def icy_weather(self):
        return carla.WeatherParameters(
            sun_altitude_angle=60.0,   # Adjust sun angle as needed
            cloudiness=30.0,           # Adjust cloudiness as needed
            precipitation=30.0,        # Some light precipitation (snow or sleet)
            precipitation_deposits=100.0,  # More deposits for icy roads
            wind_intensity=10.0,       # Adjust wind intensity as needed
            fog_density=0.0,           # No fog
            fog_distance=0.0
        )