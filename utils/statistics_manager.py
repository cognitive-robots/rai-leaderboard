import copy
from dictor import dictor

from srunner.scenariomanager.traffic_events import TrafficEventType

from leaderboard.utils.statistics_manager import RouteRecord, StatisticsManager
from leaderboard.utils.statistics_manager import compute_route_length
from leaderboard.utils.statistics_manager import PENALTY_COLLISION_PEDESTRIAN, PENALTY_COLLISION_VEHICLE, PENALTY_COLLISION_STATIC, \
    PENALTY_TRAFFIC_LIGHT, PENALTY_STOP
from leaderboard.utils.checkpoint_tools import fetch_dict, save_dict, create_default_json_msg

from rai.core.variations import RAIVariation, RAI_CASES
from rai.utils.sensors import RAISensors


class RAIRouteRecord(RouteRecord):
    def __init__(self):
        super().__init__()
        self.rai_scores = {}

def to_route_record(record_dict):
    record = RAIRouteRecord()
    for key, value in record_dict.items():
        setattr(record, key, value)

    return record

class RAIStatisticsManager(StatisticsManager):
    """
    Statistics manager for the RAI Carla leaderboard
    """
    def __init__(self, is_rai=True):
        self.unique_id = 0
        super().__init__()
        self.is_rai = is_rai
        
    def resume(self, endpoint):
        data = fetch_dict(endpoint)

        if data and dictor(data, '_checkpoint.records'):
            records = data['_checkpoint']['records']

            for record in records:
                self._registry_route_records.append(to_route_record(record))

    def set_route(self, route_id, index):
        self._master_scenario = None
        route_record = RAIRouteRecord()
        route_record.route_id = route_id
        route_record.index = index
        if self.is_rai:
            self._registry_route_records.append(route_record)
        else:
            if index < len(self._registry_route_records):
                # the element already exists and therefore we update it
                self._registry_route_records[index] = route_record
            else:
                self._registry_route_records.append(route_record)

    def compute_route_statistics(self, config, duration_time_system=-1, duration_time_game=-1, failure=""):
        """
        Compute the current statistics by evaluating all relevant scenario criteria
        """
        index = config.index
        if self.is_rai:
            index = len(self._registry_route_records) - 1

        if not self._registry_route_records or index >= len(self._registry_route_records):
            raise Exception('Critical error with the route registry.')

        # fetch latest record to fill in
        route_record = self._registry_route_records[index]

        target_reached = False
        score_penalty = 1.0
        score_route = 0.0

        route_record.meta['duration_system'] = duration_time_system
        route_record.meta['duration_game'] = duration_time_game
        route_record.meta['route_length'] = compute_route_length(config)

        if self._master_scenario:
            if self._master_scenario.timeout_node.timeout:
                route_record.infractions['route_timeout'].append('Route timeout.')
                failure = "Agent timed out"

            for node in self._master_scenario.get_criteria():
                if node.list_traffic_events:
                    # analyze all traffic events
                    for event in node.list_traffic_events:
                        if event.get_type() == TrafficEventType.COLLISION_STATIC:
                            score_penalty *= PENALTY_COLLISION_STATIC
                            route_record.infractions['collisions_layout'].append(event.get_message())

                        elif event.get_type() == TrafficEventType.COLLISION_PEDESTRIAN:
                            score_penalty *= PENALTY_COLLISION_PEDESTRIAN
                            route_record.infractions['collisions_pedestrian'].append(event.get_message())

                        elif event.get_type() == TrafficEventType.COLLISION_VEHICLE:
                            score_penalty *= PENALTY_COLLISION_VEHICLE
                            route_record.infractions['collisions_vehicle'].append(event.get_message())

                        elif event.get_type() == TrafficEventType.OUTSIDE_ROUTE_LANES_INFRACTION:
                            score_penalty *= (1 - event.get_dict()['percentage'] / 100)
                            route_record.infractions['outside_route_lanes'].append(event.get_message())

                        elif event.get_type() == TrafficEventType.TRAFFIC_LIGHT_INFRACTION:
                            score_penalty *= PENALTY_TRAFFIC_LIGHT
                            route_record.infractions['red_light'].append(event.get_message())

                        elif event.get_type() == TrafficEventType.ROUTE_DEVIATION:
                            route_record.infractions['route_dev'].append(event.get_message())
                            failure = "Agent deviated from the route"

                        elif event.get_type() == TrafficEventType.STOP_INFRACTION:
                            score_penalty *= PENALTY_STOP
                            route_record.infractions['stop_infraction'].append(event.get_message())

                        elif event.get_type() == TrafficEventType.VEHICLE_BLOCKED:
                            route_record.infractions['vehicle_blocked'].append(event.get_message())
                            failure = "Agent got blocked"

                        elif event.get_type() == TrafficEventType.ROUTE_COMPLETED:
                            score_route = 100.0
                            target_reached = True
                        elif event.get_type() == TrafficEventType.ROUTE_COMPLETION:
                            if not target_reached:
                                if event.get_dict():
                                    score_route = event.get_dict()['route_completed']
                                else:
                                    score_route = 0

        # update route scores
        route_record.scores['score_route'] = score_route
        route_record.scores['score_penalty'] = score_penalty
        route_record.scores['score_composed'] = max(score_route*score_penalty, 0.0)

        if self.is_rai:

            route_record.rai_scores[config.route_type] = max(route_record.scores['score_composed'], 0.0)

            #if config.route_type == RAIVariation.REGULAR:
            route_record.rai_scores['emission_per_sec'] = config.rai_interface.get_emissions_per_sec()
            route_record.rai_scores['emission_per_route'] = config.rai_interface.get_total_emissions()
            config.rai_interface.stop_emission_tracker()
            config.rai_interface.reset_emissions()

        # update status
        if target_reached:
            route_record.status = 'Completed'
        else:
            route_record.status = 'Failed'
            if failure:
                route_record.status += ' - ' + failure

        return route_record

    def compute_global_statistics(self, total_routes):
        global_record = RAIRouteRecord()
        global_record.route_id = -1
        global_record.index = -1
        global_record.status = 'Completed'

        global_record.meta['total_length'] = 0
        global_record.meta['duration_system'] = 0
        global_record.meta['duration_game'] = 0

        global_record.rai_scores['rai_avg_score_route'] = 0
        global_record.rai_scores['rai_avg_score_composed'] = 0
        global_record.rai_scores['rai_avg_duration_game'] = 0
        global_record.rai_scores['rai_avg_emission_per_sec'] = 0
        global_record.rai_scores['rai_avg_emission_per_route'] = 0

        if self._registry_route_records:

            records = copy.deepcopy(global_record)
            for route_record in self._registry_route_records:

                rai_keys = route_record.rai_scores.keys()

                for key in rai_keys:
                    if not 'emission' in key:
                        record_dict = {"score_composed": route_record.scores["score_composed"],
                                        "score_route": route_record.scores["score_route"],
                                        "score_penalty": route_record.scores["score_penalty"],
                                        "emission_per_route": route_record.rai_scores["emission_per_route"],
                                        "emission_per_sec": route_record.rai_scores["emission_per_sec"],
                                        "duration_game": route_record.meta["duration_game"],
                                        "duration_system": route_record.meta["duration_system"],
                                        "route_length": route_record.meta["route_length"]}
                        if key in records.rai_scores:
                            records.rai_scores[key].append(record_dict)
                        else:
                            records.rai_scores[key] = [record_dict]

                for key in global_record.infractions.keys():

                    # Change the infraction from list to a number
                    if isinstance(global_record.infractions[key], list):
                        global_record.infractions[key] = 0

                    # Avoid adding infractions if the vehicle hasn't moved,
                    # as they will most likely be caused by the Leaderboard
                    if route_record.scores['score_route'] == 0:
                        continue

                    route_length_kms = route_record.scores['score_route'] / 100 * route_record.meta['route_length'] / 1000.0
                    global_record.infractions[key] += len(route_record.infractions[key]) / route_length_kms

                if route_record.status != 'Completed':
                    global_record.status = 'Failed'
                    if 'exceptions' not in global_record.meta:
                        global_record.meta['exceptions'] = []
                    global_record.meta['exceptions'].append((route_record.route_id,
                                                             route_record.index,
                                                             route_record.status))

        '''RAI is assessed in four dimensions, energy consumed per sec, power consumed per run, robustness against noise, robustness against distributional shifts'''
        if self.is_rai:
            eps = 1e-9
            records_rai_keys = records.rai_scores.keys()

            print(f'records_rai_keys: {records_rai_keys}')
            assert(RAIVariation.REGULAR in records_rai_keys)

            # Get the regular driving score
            regular_score = records.rai_scores['REGULAR'][0]['score_composed']

            # Calculate number of REGULAR_* keys in the records.rai_scores.keys()
            rai_keys_num = sum("REGULAR_" in key for key in records.rai_scores.keys())

            for key in records.rai_scores.keys():
                # We only check lists since we want to exclude score_composed, score_route, duration_game, etc
                if isinstance(records.rai_scores[key], list):
                    if len(records.rai_scores[key]) > 1:
                        # Get minimun_score_dict where we have multiple runs for e.g. weather or D1_CAM
                        records.rai_scores[key] = [min(records.rai_scores[key], key=lambda d: d['score_composed'])]

                    if 'REGULAR_' in key:
                        # Adjust the score based on regular_score
                        global_record.rai_scores[key] = min(regular_score, records.rai_scores[key][0]['score_composed'])

                        # Calculate all global_record.rai_scores from records.rai_scores 
                        global_record.rai_scores['rai_avg_score_composed'] += global_record.rai_scores[key]/ rai_keys_num
                        global_record.rai_scores['rai_avg_score_route'] += records.rai_scores[key][0]['score_route'] / rai_keys_num
                        global_record.rai_scores['rai_avg_duration_game'] += records.rai_scores[key][0]['duration_game'] / rai_keys_num
                        global_record.rai_scores['rai_avg_emission_per_sec'] += records.rai_scores[key][0]['emission_per_sec'] / rai_keys_num
                        global_record.rai_scores['rai_avg_emission_per_route'] += records.rai_scores[key][0]['emission_per_route'] / rai_keys_num
                    elif 'REGULAR' in key:
                        global_record.rai_scores[key] = records.rai_scores[key][0]['score_composed']
                        global_record.scores['score_composed'] = records.rai_scores[key][0]['score_composed']
                        global_record.scores['score_route'] = records.rai_scores[key][0]['score_route']
                        global_record.scores['score_penalty'] = records.rai_scores[key][0]['score_penalty']
                        global_record.meta['total_length'] = records.rai_scores[key][0]['route_length']
                        global_record.meta['duration_system'] = records.rai_scores[key][0]['duration_system']
                        global_record.meta['duration_game'] = records.rai_scores[key][0]['duration_game']
                    
                    # take ratios of REGULAR*/ regular_score
                    global_record.rai_scores[key] /= (regular_score + eps)

        return global_record

    @staticmethod
    def save_record(route_record, index, endpoint):
        data = fetch_dict(endpoint)
        if not data:
            data = create_default_json_msg()

        stats_dict = route_record.__dict__
        record_list = data['_checkpoint']['records']
        
        record_list.append(stats_dict)

        save_dict(endpoint, data)
        
    @staticmethod
    def save_global_record(route_record, sensors, total_routes, endpoint, is_rai):
        data = fetch_dict(endpoint)
        if not data:
            data = create_default_json_msg()

        stats_dict = route_record.__dict__
        data['_checkpoint']['global_record'] = stats_dict
        data['values'] = ['{:.3f}'.format(stats_dict['scores']['score_composed']),
                          '{:.3f}'.format(stats_dict['scores']['score_route']),
                          '{:.3f}'.format(stats_dict['scores']['score_penalty']),
                          # infractions
                          '{:.3f}'.format(stats_dict['infractions']['collisions_pedestrian']),
                          '{:.3f}'.format(stats_dict['infractions']['collisions_vehicle']),
                          '{:.3f}'.format(stats_dict['infractions']['collisions_layout']),
                          '{:.3f}'.format(stats_dict['infractions']['red_light']),
                          '{:.3f}'.format(stats_dict['infractions']['stop_infraction']),
                          '{:.3f}'.format(stats_dict['infractions']['outside_route_lanes']),
                          '{:.3f}'.format(stats_dict['infractions']['route_dev']),
                          '{:.3f}'.format(stats_dict['infractions']['route_timeout']),
                          '{:.3f}'.format(stats_dict['infractions']['vehicle_blocked'])
                          ]

        data['labels'] = ['Avg. driving score',
                          'Avg. route completion',
                          'Avg. infraction penalty',
                          'Collisions with pedestrians',
                          'Collisions with vehicles',
                          'Collisions with layout',
                          'Red lights infractions',
                          'Stop sign infractions',
                          'Off-road infractions',
                          'Route deviations',
                          'Route timeouts',
                          'Agent blocked'
                          ]

        if is_rai:
            data['values'] = data['values'] + [
                            '{:.6f}'.format(stats_dict['rai_scores']['rai_avg_emission_per_sec']),
                            '{:.6f}'.format(stats_dict['rai_scores']['rai_avg_emission_per_route'])
                            ]

            data['labels'] = data['labels'] + [
                            'Avg. Emissions Per Sec',
                            'Avg. Emissions Per Route'
                            ]

            #for RAI_CASE in RAI_CASES:
            for RAI_CASE in RAI_CASES:
                if RAI_CASE in [RAIVariation.DISTORTION1, RAIVariation.DISTORTION2]:
                    if 'camera' in sensors:
                        data['values'] = data['values'] + ['{:.3f}'.format(stats_dict['rai_scores'][RAI_CASE + RAISensors.CAMERA])]
                        if RAI_CASE == RAIVariation.DISTORTION1:
                            data['labels'] = data['labels'] + ['Camera Robustness_Sp']
                        else:
                            data['labels'] = data['labels'] + ['Camera Robustness_Occ']

                    if 'lidar' in sensors:
                        data['values'] = data['values'] + ['{:.3f}'.format(stats_dict['rai_scores'][RAI_CASE + RAISensors.LIDAR])]
                        if RAI_CASE == RAIVariation.DISTORTION1:
                            data['labels'] = data['labels'] + ['Lidar Robustness_Sp']
                        else:
                            data['labels'] = data['labels'] + ['Lidar Robustness_Occ']

                if RAI_CASE in [RAIVariation.DISTORTION3]:
                    if 'gnss' in sensors: 
                        data['values'] = data['values'] + ['{:.3f}'.format(stats_dict['rai_scores'][RAI_CASE + RAISensors.GNSS])]
                        data['labels'] = data['labels'] + ['GNSS Robustness']
                
                    if 'imu' in sensors: 
                        data['values'] = data['values'] + ['{:.3f}'.format(stats_dict['rai_scores'][RAI_CASE + RAISensors.IMU])]
                        data['labels'] = data['labels'] + ['IMU Robustness']

                    if 'speedometer' in sensors: 
                        data['values'] = data['values'] + ['{:.3f}'.format(stats_dict['rai_scores'][RAI_CASE + RAISensors.SPEEDOMETER])]
                        data['labels'] = data['labels'] + ['Speedometer Robustness']
                
                if RAI_CASE in [RAIVariation.WEATHER]:
                    data['values'] = data['values'] + ['{:.3f}'.format(stats_dict['rai_scores'][RAI_CASE])]
                    data['labels'] = data['labels'] + ['Weather Robustness']
                
                if RAI_CASE in [RAIVariation.SHIFT]:
                    data['values'] = data['values'] + ['{:.3f}'.format(stats_dict['rai_scores'][RAI_CASE])]
                    data['labels'] = data['labels'] + ['Data Drift']

            # Add additional RAI metrics
            data['values'] = data['values'] + \
                            ['{:.3f}'.format(stats_dict['rai_scores']['rai_avg_score_composed']),
                            '{:.3f}'.format(stats_dict['rai_scores']['rai_avg_score_route']),
                            '{:.3f}'.format(stats_dict['rai_scores']['rai_avg_duration_game']),
                            ]

            data['labels'] = data['labels'] + \
                            ['RAI Avg. Driving Score',
                            'RAI Avg. route completion',
                            'RAI Avg. Game Duration',
                            ]

        entry_status = "Finished"
        eligible = True

        route_records = data["_checkpoint"]["records"]
        progress = data["_checkpoint"]["progress"]
        
        if progress[1] != total_routes:
            raise Exception('Critical error with the route registry.')

        if len(route_records) != total_routes or progress[0] != progress[1]:
            entry_status = "Finished with missing data"
            eligible = False
        else:
            for route in route_records:
                route_status = route["status"]
                if "Agent" in route_status:
                    entry_status = "Finished with agent errors"
                    break

        data['sensors'] = sensors
        data['entry_status'] = entry_status
        data['eligible'] = eligible

        save_dict(endpoint, data)