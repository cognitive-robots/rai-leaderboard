import os
import random
import cv2
import yaml
import numpy as np
from scipy.spatial import Delaunay

def check_default_values(config, **kwargs):
    """
    If any values are None, update them with values from the yaml config. If not None,
    keep the current value. The keys in kwargs should match keys in the config.
    """
    updated_values = {}
    for key, value in kwargs.items():
        if value is None:
            config_value = get_config_value(config, key)
            updated_values[key] = config_value
        else:
            updated_values[key] = value
    return updated_values.values()

def get_config_value(config, key):
    """
    Navigate the config dict and return the value for the key
    """
    for k, v in config.items():
        # For nested dict
        if isinstance(v, dict):
            if key in v:
                return v[key]
        # If the value is not dict
        else:
            if key in config:
                return config[key]
    raise KeyError(f"Key '{key}' not found in the config.")

def sort_vertices(vertices):
    """
    Sort vertices in clockwise order
    """
    centre_x = sum([v[0] for v in vertices]) / len(vertices)
    centre_y = sum([v[1] for v in vertices]) / len(vertices)
    return sorted(vertices, key=lambda v: np.arctan2(v[1] - centre_y, v[0] - centre_x))


class Robustness:
    """
    Class for noising sensors for robustness test
    """
    def __init__(self, sensors):
        self.sensors = sensors

        # load parameters from the config file
        rai_path = os.environ.get('RAI_LEADERBOARD_ROOT')
        with open(f'{rai_path}/config/robustness.yaml','r') as f:
            self.config = yaml.safe_load(f)

        # default parameters for lidar from agent_wrapper.py.
        # TODO: These parameters are not directly accessible in sensors
        # but can we obtain them from the world once the scenario is loaded for
        # the first time?
        self._LIDAR_RANGE = 85
        self._UPPER_FOV = 10
        self._LOWER_FOV = -30
        self._NUM_OF_CHANNELS = 64

        # 5 points, including the origin, defines the occlusion shape.
        # spherical (r, theta, phi)
        theta_0, theta_1 = self.config['lidar']['theta']
        phi_0, phi_1 = self.config['lidar']['phi']
        self.points_in_spherical = np.array([[self._LIDAR_RANGE,theta_0,phi_0],
                                            [self._LIDAR_RANGE,theta_0,phi_1],
                                            [self._LIDAR_RANGE,theta_1,phi_0],
                                            [self._LIDAR_RANGE,theta_1,phi_1],
                                            [0,0,0]])
        self.occlusion_hull = None
        self.lidar_occlusion_init = False
        # channel range to remove for internal noise
        channel_range_to_remove = np.array(self.config['lidar']['channel_range_to_remove'])
        self.angle_range_to_remove = self.channels_to_angle(channel_range_to_remove)

    def channels_to_angle(self, channel_range_to_remove, in_radians=True):
        """
        Convert channels to angles for internal noise/ channel removal
        """
        # channel_resolution = vertical_fov/ num_of_channels. Here, (10) - (-30) = 40/64
        channel_resolution = float((self._UPPER_FOV - self._LOWER_FOV)/self._NUM_OF_CHANNELS)
        # we convert channels to degrees and add (90 - upper_fov) (= 80) 
        # as the angle we measure, which is with the +ve z axis compared to specs, 
        # where the vertical range of (10 to -30) is with +ve X axis.
        angle_range_to_remove = (90 - self._UPPER_FOV) + (channel_range_to_remove * channel_resolution)
        if in_radians:
            return np.radians(angle_range_to_remove)
        return angle_range_to_remove

    def add_salt_and_pepper_noise(self, sensor_data, sensor_info, probability=None):
        """
        Add salt and pepper noise with some given probability.
        """
        if  sensor_info:
            if sensor_info['type'] == 'camera':
                probability, = check_default_values(self.config, probability=probability)

                # Generate random noise with the same shape as the input image
                sensor_data = sensor_data[1][:, :, :3]

                # Generate random noise mask
                black = np.array([0, 0, 0], dtype='uint8')
                white = np.array([255, 255, 255], dtype='uint8')
                probs = np.random.random(sensor_data.shape[:2])
                sensor_data[probs < (probability / 2)] = black
                sensor_data[probs > 1 - (probability / 2)] = white

            elif sensor_info['type'] == 'lidar':
                # Remove selected lidar channels
                sensor_data = tuple([sensor_data[0], self.lidar_channel_removal(sensor_data[1])])

        return sensor_data

    def lidar_channel_removal(self, sensor_data):
        """
        Compute angles between the origin->sensor_data points and 
        +ve Z axis. Remove points whose angle is within the range that
        we want to remove.
        """
        ORIGIN = np.zeros(3)
        op = sensor_data[:,0:3] - ORIGIN # by taking [:,0:3] we only take XYZ
        normalized_op = self.normalize_vector(op)
        DIRECTION_VECTOR = np.array([0,0,1]).reshape(-1,1) # Z axis
        dot_product = np.dot(normalized_op, DIRECTION_VECTOR)
        # compute the angle between the origin->point and the +ve z axis
        # the precision has to be upto 4 decimal digits otherwise it will 
        # not remove points that have phi e.g. 79.9999 degrees.
        phi_angle = np.round(np.arccos(dot_product),4)
        # check if calculated angle phi belong in *any* of the range that we 
        # want to remove
        in_range = (
                    (phi_angle >= self.angle_range_to_remove[:,0]) & 
                    (phi_angle <= self.angle_range_to_remove[:,1])
                    ).any(-1)
        points_removal = ~in_range
        cropped_data = sensor_data[points_removal,:]
        return cropped_data

    def normalize_vector(self, vector):
        """
        Normalize a given vector to unit length
        """
        norm = np.linalg.norm(vector, axis=1, keepdims=True)
        # replace norm 0 with 1 i.e. no change on division
        norm[norm == 0] = 1.0
        return vector / norm

    def add_occlussion_noise(self, sensor_data, sensor_info, num_vertices=None, random_seed=None):
        """
        Create polygon shape occlusion over camera
        """
        # Create an empty mask array
        if  sensor_info:
            if sensor_info['type'] == 'camera':
                # Get default values from yaml if params are None
                num_vertices, random_seed = check_default_values(self.config, num_vertices=num_vertices,
                                                                 random_seed=random_seed)
                # Generate random noise with the same shape as the input image
                sensor_data = sensor_data[1][:, :, :3]
                height, width, _ = sensor_data.shape
                mask = np.zeros(sensor_data.shape[:2], dtype=np.uint8)

                # Generate random polygon vertices
                random.seed(random_seed)

                # Generate unique vertices
                vertices = set()
                while len(vertices) < num_vertices:
                    x = random.randint(0, width - 1)
                    y = random.randint(0, height - 1)
                    vertices.add((x, y))

                # Sort vertices in clockwise order
                vertices_sorted = sort_vertices(list(vertices))

                # Create a polygon mask using fillPoly
                cv2.fillPoly(mask, [np.array(vertices_sorted)], 255)
                # self.display_image(mask)
                # Invert the mask
                inverted_mask = cv2.bitwise_not(mask)
                # Apply the mask to the image
                sensor_data = cv2.bitwise_and(sensor_data, sensor_data, mask=inverted_mask)

            elif sensor_info['type'] == 'lidar':
                if not self.lidar_occlusion_init:
                    self.occlusion_hull = self.setup_lidar_occlusion(self.points_in_spherical)
                # Create occlusion and return occluded lidar data
                sensor_data = tuple([sensor_data[0], self.lidar_occlusion(sensor_data[1])])

        return sensor_data

    def setup_lidar_occlusion(self, points_in_spherical):
        """
        Take points_in_spherical(radius,theta,phi), convert them to the Cartesian
        space(x,y,z) and return convex hull of those points.
        """
        self.lidar_occlusion_init = True
        points_in_spherical = self.transform_theta(points_in_spherical)
        points_in_cartesian = self.spherical_to_cartesian(points_in_spherical)
        return Delaunay(points_in_cartesian)

    def transform_theta(self, points_in_spherical):
        """
        Get lidar yaw and transform the theta of points_in_spherical
        """
        # TODO: if the change of angle is not only in the yaw/theta then we can use
        # something like this to transform the points instead of transform_theta().

        # rotation = carla.Rotation(roll=0, pitch=0, yaw=90)
        # lidart_tf = carla.Transform(rotation=rotation)
        # print(lidart_tf.transform_vector(carla.Vector3D(points_in_cartesian[0,0],
        #                                                 points_in_cartesian[0,1],
        #                                                 points_in_cartesian[0,2])))

        yaw = [sensor['yaw'] for sensor in self.sensors if sensor['type']=='sensor.lidar.ray_cast'][0]
        points_in_spherical[:,1] = points_in_spherical[:,1] - yaw
        return points_in_spherical

    def spherical_to_cartesian(self, points_in_spherical):
        """
        Conversion from spherical(radius,theta,phi) -> cartesian(x,y,z)
        """
        points_in_cartesian = np.empty(shape=points_in_spherical.shape)
        for idx, point in enumerate(points_in_spherical):
            radius=point[0]
            theta=np.radians(point[1])
            phi=np.radians(point[2])
            x = radius * np.sin(phi) * np.cos(theta)
            y = radius * np.sin(phi) * np.sin(theta)
            z = radius * np.cos(phi)
            points_in_cartesian[idx] = [x,y,z]
        return points_in_cartesian

    def lidar_occlusion(self, sensor_data):
        """
        Return occuled sensor_data where occlusion is created with convex hull
        """
        def in_occlusion_hull(cloud, hull):
            """
            Test if points in `cloud` are in `hull`

            `cloud` should be a `NxK` coordinates of `N` points in `K` dimensions
            `hull` is either a scipy.spatial.Delaunay object or the `MxK` array of the 
            coordinates of `M` points in `K`dimensions for which Delaunay triangulation
            will be computed
            """
            if not isinstance(hull, Delaunay):
                hull = Delaunay(hull)

            return hull.find_simplex(cloud)>=0

        # points inside the occlusion_hull would return true. To remove those points
        # we invert the array. In [:, 0:3], we take xyz but not lidar intentsity.
        points_removal = ~in_occlusion_hull(sensor_data[:,0:3], self.occlusion_hull)
        #print(f'number of points that will be removed: {np.sum(~points_removal)}')
        cropped_data = sensor_data[points_removal,:]
        return cropped_data
    
    def add_random_noise(self, sensor_data, sensor_info):
        """
        Add random noise to GPS readings or IMU readings depending
        on the type of sensor parameter passed in
        """
        # Generate random noise values within the specified noise_level
        if sensor_info['type'] == 'gnss':
            return self.noise_gnss(sensor_data[1])
        elif sensor_info['type'] == 'imu':
            return self.noise_imu(sensor_data[1])
        elif sensor_info['type'] == 'speedometer':
            return self.noise_speedometer(sensor_data[1])
    
    def noise_gnss(self, sensor_data, noise_level=None):
        """
        Use the same level of random noise for latitude, longitude, and altitude
        """
        noise_level, = check_default_values(self.config, noise_level=noise_level)
        lat_noise = random.uniform(-noise_level, noise_level)
        lon_noise = random.uniform(-noise_level, noise_level)
        alt_noise = random.uniform(-noise_level, noise_level)

        # Add noise to GPS coordinates
        sensor_data +=  np.array([lat_noise, lon_noise, alt_noise])
        return sensor_data
    
    def noise_imu(self, sensor_data, acc_noise_lvl=None, compass_noise_lvl=None, gyroscope_noise_lvl=None):
        """
        Set levels for random noise for acceleration, compass, and gyroscope
        """
        noise_levels = check_default_values(self.config, acc_noise_lvl=acc_noise_lvl,
                                                 compass_noise_lvl=compass_noise_lvl,
                                                 gyroscope_noise_lvl=gyroscope_noise_lvl)
        acc_noise_lvl, compass_noise_lvl, gyroscope_noise_lvl = noise_levels
        acc_noise = random.uniform(-acc_noise_lvl, acc_noise_lvl)
        compass_noise = random.uniform(-compass_noise_lvl, compass_noise_lvl)
        gyroscope_noise = random.uniform(-gyroscope_noise_lvl, gyroscope_noise_lvl)

        # Add noise to GPS coordinates
        sensor_data[0:3] += acc_noise
        sensor_data[3] += compass_noise
        sensor_data[4:] += gyroscope_noise
        return sensor_data

    def noise_speedometer(self, sensor_data, speed_noise_lvl=None):
        """
        Set level for random noise for speedometer
        """
        speed_noise_lvl, = check_default_values(self.config, speed_noise_lvl=speed_noise_lvl)
        speed_noise = random.uniform(-speed_noise_lvl, speed_noise_lvl)

        # Add noise to speedometer reading
        sensor_data['speed'] += speed_noise
        return sensor_data['speed']
    
    def display_image(self, image):
        """
        Helper function to display image using OpenCV for debugging
        """
        cv2.imshow('test', image)  
        # waits for user to press any key
        # (this is necessary to avoid Python kernel form crashing)
        cv2.waitKey(0)
        cv2.destroyAllWindows()