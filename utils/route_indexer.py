import copy

from leaderboard.utils.route_indexer import RouteIndexer
from leaderboard.utils.checkpoint_tools import fetch_dict, create_default_json_msg, save_dict

from rai.utils.route_parser import RAIRouteParser


class RAIRouteIndexer(RouteIndexer):
    def __init__(self, routes_file, scenarios_file, repetitions, routes_subset):
        super(RAIRouteIndexer, self).__init__(routes_file, scenarios_file, repetitions, routes_subset)

        # retrieve routes
        route_configurations = RAIRouteParser.parse_routes_file(self._routes_file, self._scenarios_file, self._routes_subset)

        self.n_routes = len(route_configurations)
        self.total = self.n_routes*self._repetitions

        for i, config in enumerate(route_configurations):
            for repetition in range(repetitions):
                config.index = i * self._repetitions + repetition
                config.repetition_index = repetition
                self._configs_dict['{}.{}'.format(config.name, repetition)] = copy.copy(config)

        self._configs_list = list(self._configs_dict.items())
    
    def save_state(self, endpoint):
        data = fetch_dict(endpoint)
        if not data:
            data = create_default_json_msg()
        data['_checkpoint']['progress'] = [self._index, self.total]
        self._index += 1
        save_dict(endpoint, data)