import numpy as np
from collections import deque
from filterpy.kalman import KalmanFilter
import time
mul = 1
def initialize_kalman_filter():
    kf = KalmanFilter(dim_x=4, dim_z=2)
    kf.x = np.array([[0], [0], [0], [0]])
    dt = 1
    kf.F = np.array([[1, 0, dt, 0],
                     [0, 1, 0, dt],
                     [0, 0, 1, 0],
                     [0, 0, 0, 1]])
    
    kf.H = np.array([[1, 0, 0, 0],
                     [0, 1, 0, 0]])

    kf.P *= 1000  
    
    kf.Q = np.array([[1e-5, 0, 0, 0],
                     [0, 1e-5, 0, 0],
                     [0, 0, 1e-5, 0],
                     [0, 0, 0, 1e-5]])
    
    kf.R = np.array([[1e-1, 0],
                     [0, 1e-1]])
    
    return kf

def kalman_filter(positions):
    kf = initialize_kalman_filter()
    
    for measurement in positions:
        kf.predict()
        z = np.array([[measurement['latitude']],
                      [measurement['longitude']]])
        
        if measurement.get('is_outlier', False):
            kf.R = np.array([[1e+1, 0],
                             [0, 1e+1]])
        else:
            kf.R = np.array([[1e-1, 0],
                             [0, 1e-1]])

        kf.update(z)

    return {'latitude': kf.x[0][0], 'longitude': kf.x[1][0]}

def sliding_window_filter(positions):
    avg_latitude = sum(pos["latitude"] for pos in positions) / len(positions)
    avg_longitude = sum(pos["longitude"] for pos in positions) / len(positions)
    return {'latitude': avg_latitude, 'longitude': avg_longitude}
