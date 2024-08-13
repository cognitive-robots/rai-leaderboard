#!/usr/bin/env python

# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""
Module used to parse all the route and scenario configuration parameters.
"""
import xml.etree.ElementTree as ET

import carla
from leaderboard.utils.route_parser import RouteParser

from rai.scenarioconfigs.route_scenario_configuration import ExtRouteScenarioConfiguration


class RAIRouteParser(RouteParser):

    """
    Pure static class used to parse all the route and scenario configuration parameters.
    """

    @staticmethod
    def parse_routes_file(route_filename, scenario_file, routes_subset=''):
        """
        Returns a list of route elements.
        :param route_filename: the path to a set of routes.
        :param routes_subset: If provided, these routes shall be returned
        :return: List of dicts containing the waypoints, id and town of the routes
        """
        def get_routes_subset():
            """
            The route subset can be indicated by single routes separated by commas,
            or group of routes separated by dashes (or a combination of the two)"""
            subset_ids = []
            subset_groups = routes_subset.replace(" ","").split(',')
            for group in subset_groups:
                if "-" in group:
                    # Group of route, iterate from start to end, making sure both ids exist
                    start, end = group.split('-')
                    found_start, found_end = (False, False)

                    for route in tree.iter("route"):
                        route_id = route.attrib['id']
                        if not found_start and route_id == end:
                            raise ValueError(f"Malformed route subset '{group}', found the end id before the starting one")
                        elif not found_start and route_id == start:
                            found_start = True
                        if not found_end and found_start:
                            if route_id in subset_ids:
                                raise ValueError(f"Found a repeated route with id '{route_id}'")
                            else:
                                subset_ids.append(route_id)
                            if route_id == end:
                                found_end = True

                    if not found_start:
                        raise ValueError(f"Couldn\'t find the route with id '{start}' inside the given routes file")
                    if not found_end:
                        raise ValueError(f"Couldn\'t find the route with id '{end}' inside the given routes file")

                else:
                    # Just one route, get its id while making sure it exists

                    found = False
                    for route in tree.iter("route"):
                        route_id = route.attrib['id']
                        if route_id == group:
                            if route_id in subset_ids:
                                raise ValueError(f"Found a repeated route with id '{route_id}'")
                            else:
                                subset_ids.append(route_id)
                            found = True

                    if not found:
                        raise ValueError(f"Couldn't find the route with id '{group}' inside the given routes file")

            subset_ids.sort()
            return subset_ids

        list_route_descriptions = []
        tree = ET.parse(route_filename)
        if routes_subset:
            subset_list = get_routes_subset()
        for route in tree.iter("route"):

            route_id = route.attrib['id']
            if routes_subset and route_id not in subset_list:
                continue

            new_config = ExtRouteScenarioConfiguration()
            new_config.town = route.attrib['town']
            new_config.name = "RouteScenario_{}".format(route_id)
            new_config.weather = RouteParser.parse_weather(route)
            new_config.scenario_file = scenario_file

            waypoint_list = []  # the list of waypoints that can be found on this route
            for waypoint in route.iter('waypoint'):
                waypoint_list.append(carla.Location(x=float(waypoint.attrib['x']),
                                                    y=float(waypoint.attrib['y']),
                                                    z=float(waypoint.attrib['z'])))

            new_config.trajectory = waypoint_list

            list_route_descriptions.append(new_config)

        return list_route_descriptions
