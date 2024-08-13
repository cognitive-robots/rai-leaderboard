
#!/usr/bin/env python

import logging
import random
import warnings
import carla

class Actors:
    walkers ='walkers'
    vehicle = 'vehicle'

def get_actor_blueprints(world, filter, generation):
    bps = world.get_blueprint_library().filter(filter)

    if generation.lower() == "all":
        return bps

    # If the filter returns only one bp, we assume that this one needed
    # and therefore, we ignore the generation
    if len(bps) == 1:
        return bps

    try:
        int_generation = int(generation)
        # Check if generation is in available generations
        if int_generation in [1, 2]:
            bps = [x for x in bps if int(x.get_attribute('generation')) == int_generation]
            return bps
        else:
            print("   Warning! Actor Generation is not valid. No actor will be spawned.")
            return []
    except:
        print("   Warning! Actor Generation is not valid. No actor will be spawned.")
        return []


def shift_environment(world, _map, client, traffic_manager, args, actors_dict={Actors.walkers : ['walker', 'all', 200]}):
    """
    Introduce a distribution shift in the environment
    """

    vehicles_list = []
    walkers_list = []
    all_id = []

    if _map == None:
        _map = world.get_map()

    synchronous_master = False

    random.seed(args.carlaProviderSeed)

    try:
        
        #traffic_manager.set_global_distance_to_leading_vehicle(2.5)


        # @todo cannot import these directly.
        SpawnActor = carla.command.SpawnActor
        SetAutopilot = carla.command.SetAutopilot
        FutureActor = carla.command.FutureActor
        
        if Actors.vehicle in actors_dict:

            v_filter = actors_dict[Actors.vehicle][0]
            v_generation = actors_dict[Actors.vehicle][1]
            n_vehicles = actors_dict[Actors.vehicle][2]
        
            blueprints = get_actor_blueprints(world, v_filter, v_generation)

            blueprints = [x for x in blueprints if x.get_attribute('base_type') == 'car']

            blueprints = sorted(blueprints, key=lambda bp: bp.id)

            spawn_points = _map.get_spawn_points()
            number_of_spawn_points = len(spawn_points)

            n_vehicles = actors_dict[Actors.vehicle][2]
            if n_vehicles < number_of_spawn_points:
                random.shuffle(spawn_points)
            elif n_vehicles > number_of_spawn_points:
                print(f'requested {n_vehicles} {Actors.vehicle}, but could \
                    only find {number_of_spawn_points} spawn points')
                #warnings.warn(msg, n_vehicles, number_of_spawn_points)
                msg = 'requested %d vehicles, but could only find %d spawn points'
                logging.warning(msg, n_vehicles, number_of_spawn_points)
                n_vehicles = number_of_spawn_points

            # --------------
            # Spawn vehicles
            # --------------
            batch = []

            for n, transform in enumerate(spawn_points):
                if n >= n_vehicles:
                    break
                blueprint = random.choice(blueprints)
                if blueprint.has_attribute('color'):
                    color = random.choice(blueprint.get_attribute('color').recommended_values)
                    blueprint.set_attribute('color', color)
                if blueprint.has_attribute('driver_id'):
                    driver_id = random.choice(blueprint.get_attribute('driver_id').recommended_values)
                    blueprint.set_attribute('driver_id', driver_id)
            
                blueprint.set_attribute('role_name', 'autopilot')

                # spawn the cars and set their autopilot and light state all together
                batch.append(SpawnActor(blueprint, transform)
                    .then(SetAutopilot(FutureActor, True, traffic_manager.get_port())))

            for response in client.apply_batch_sync(batch, synchronous_master):
                if response.error:
                    logging.error(response.error)
                else:
                    vehicles_list.append(response.actor_id)

            # Set automatic vehicle lights update if specified
            all_vehicle_actors = world.get_actors(vehicles_list)
            for actor in all_vehicle_actors:
                traffic_manager.update_vehicle_lights(actor, True)
            print('spawned %d vehicles, press Ctrl+C to exit.' % (len(vehicles_list)))

        # -------------
        # Spawn Walkers
        # -------------
        # some settings

        if Actors.walkers in actors_dict:

            w_filter = actors_dict[Actors.walkers][0]
            w_generation = actors_dict[Actors.walkers][1]
            n_walkers = actors_dict[Actors.walkers][2]

            blueprintsWalkers = get_actor_blueprints(world, w_filter, w_generation)
            percentagePedestriansRunning = n_walkers      # how many pedestrians will run
            percentagePedestriansCrossing = int(n_walkers/2.0)     # how many pedestrians will walk through the road
            
            #world.set_pedestrians_seed(args.carlaProviderSeed)
            #random.seed(args.traffic_manager_seed)

            # 1. take all the random locations to spawn
            spawn_points = []
            for i in range(n_walkers):
                spawn_point = carla.Transform()
                loc = world.get_random_location_from_navigation()
                if (loc != None):
                    spawn_point.location = loc
                    spawn_points.append(spawn_point)
            # 2. we spawn the walker object
            batch = []
            walker_speed = []

            for spawn_point in spawn_points:
                walker_bp = random.choice(blueprintsWalkers)
                # set as not invincible
                if walker_bp.has_attribute('is_invincible'):
                    walker_bp.set_attribute('is_invincible', 'false')
                # set the max speed
                if walker_bp.has_attribute('speed'):
                    if (percentagePedestriansRunning > 0):
                        # running
                        walker_speed.append(walker_bp.get_attribute('speed').recommended_values[2])
                        percentagePedestriansRunning -= 1
                    else:
                        # walking
                        walker_speed.append(walker_bp.get_attribute('speed').recommended_values[1])
                else:
                    print("Walker has no speed")
                    walker_speed.append(0.0)
                batch.append(SpawnActor(walker_bp, spawn_point))
            results = client.apply_batch_sync(batch, True)
            walker_speed2 = []

            for i in range(len(results)):
                if results[i].error:
                    logging.error(results[i].error)
                else:
                    walkers_list.append({"id": results[i].actor_id})
                    walker_speed2.append(walker_speed[i])

            walker_speed = walker_speed2
            # 3. we spawn the walker controller
            batch = []
            
            walker_controller_bp = world.get_blueprint_library().find('controller.ai.walker')

            for i in range(len(walkers_list)):
                batch.append(SpawnActor(walker_controller_bp, carla.Transform(), walkers_list[i]["id"]))

            results = client.apply_batch_sync(batch, True)

            for i in range(len(results)):
                if results[i].error:
                    logging.error(results[i].error)
                else:
                    walkers_list[i]["con"] = results[i].actor_id

            # 4. we put together the walkers and controllers id to get the objects from their id
            for i in range(len(walkers_list)):
                all_id.append(walkers_list[i]["con"])
                all_id.append(walkers_list[i]["id"])
            all_actors = world.get_actors(all_id)

            # wait for a tick to ensure client receives the last transform of the walkers we have just created
            # MAYBE NOT NEEDED
            if not world.get_settings().synchronous_mode or not synchronous_master:
                world.tick()
            else:
                world.wait_for_tick()
                
            # 5. initialize each controller and set target to walk to (list is [controler, actor, controller, actor ...])
            # set how many pedestrians can cross the road
            world.set_pedestrians_cross_factor(percentagePedestriansCrossing)
            for i in range(0, len(all_id), 2):
                # start walker
                all_actors[i].start()
                # set walk to random point
                all_actors[i].go_to_location(world.get_random_location_from_navigation())
                # max speed
                all_actors[i].set_max_speed(float(walker_speed[int(i/2)]))

            print('spawned %d walkers, press Ctrl+C to exit.' % (len(walkers_list)))

        # Example of how to use Traffic Manager parameters
        traffic_manager.global_percentage_speed_difference(30.0)

    except Exception:
        print('Error while setting up actors')
