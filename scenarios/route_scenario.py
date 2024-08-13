from leaderboard.scenarios.route_scenario import RouteScenario

class RAIRouteScenario(RouteScenario):
    def __init__(self, world, config, debug_mode, custom_timeout, criteria_enable=True):
        """
        Setup all relevant parameters and create scenarios along route
        """
        self.config = config
        self.route = None
        self.sampled_scenarios_definitions = None

        self._update_route(world, config, debug_mode>0)

        ego_vehicle = self._update_ego_vehicle()

        if custom_timeout > -1:
            self.timeout = custom_timeout

        self.list_scenarios = self._build_scenario_instances(world,
                                                             ego_vehicle,
                                                             self.sampled_scenarios_definitions,
                                                             scenarios_per_tick=10,
                                                             timeout=self.timeout,
                                                             debug_mode=debug_mode>1)

        super(RouteScenario, self).__init__(name=config.name,
                                            ego_vehicles=[ego_vehicle],
                                            config=config,
                                            world=world,
                                            debug_mode=debug_mode>1,
                                            terminate_on_failure=False,
                                            criteria_enable=criteria_enable)