
from srunner.scenarioconfigs.route_scenario_configuration import RouteScenarioConfiguration

class ExtRouteScenarioConfiguration(RouteScenarioConfiguration):
     #add RAI info
    route_type = None
    sensor_to_noise = None
    is_rai = False
    rai_interface = None
    frame_rate = 20
    run_id = None
