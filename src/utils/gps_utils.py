from collections import deque
import requests
from geopy.geocoders import Nominatim
import random
import numpy as np
from utils.filters import kalman_filter, sliding_window_filter

class LocationService:
    def __init__(self):
        self.mul = 1
        self.latitude = 55.7482
        self.longitude = 37.6171
        self.small_noise_level=0.0005
        self.large_noise_level=0.003
        self.big_noise_level=0.02
        self.positions = deque(maxlen=10)
    def __get_real_location_data(self):
        try:
            response = requests.get("http://ip-api.com/json/")
            response.raise_for_status()
            location_data = response.json()
            
            latitude = location_data.get("lat")
            longitude = location_data.get("lon")

            return {"latitude": latitude,
                    "longitude": longitude}
        except requests.exceptions.RequestException as e:
            print(f"Ошибка получения местоположения: {e}")
        return None

    def __get_fake_location_data(self):
        step = 0.001 * self.mul
        r = np.random.rand()
        if r < 0.1:
            noise_lat = np.random.uniform(-self.large_noise_level, self.large_noise_level)
            noise_lon = np.random.uniform(-self.large_noise_level, self.large_noise_level)
        elif r < 0.9:
            noise_lat = np.random.uniform(-self.small_noise_level, self.small_noise_level)
            noise_lon = np.random.uniform(-self.small_noise_level, self.small_noise_level)
        else:
            noise_lat = np.random.uniform(-self.big_noise_level, self.big_noise_level)
            noise_lon = np.random.uniform(-self.big_noise_level, self.big_noise_level)  
            
        dx = step + np.random.uniform(-noise_lat, noise_lat)
        dy = step + np.random.uniform(-noise_lon, noise_lon)
        self.mul += 1
        return {"latitude": self.latitude + dx,
                "longitude": self.longitude + dy}

    def get_location_data(self, geofilter=sliding_window_filter):
        location = self.__get_fake_location_data()
        self.positions.append(location)
        filtered_position = geofilter(self.positions)
        return filtered_position