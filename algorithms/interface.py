# algorithms/base.py
from abc import ABC, abstractmethod
from qgis.core import QgsVectorLayer

class MapMatchingStrategy(ABC):
    """
    Clase base abstracta para una estrategia de Map Matching.
    Define la interfaz común que todas las implementaciones de algoritmos deben seguir.
    """
    def __init__(self, gps_points_layer: QgsVectorLayer, road_layer: QgsVectorLayer, config: dict):
        """
        Inicializa la estrategia.
        """
        self.config = config
        self.gps_points_layer = gps_points_layer
        self.road_layer = road_layer
        self.gps_points_path = config.get('gps_points_info').get('path')
        self.gps_points_frecuency = config.get('gps_points_info').get('frecuency')
        self.gps_points_name_attributes = config.get('gps_points_info').get('name_attributes')
        self.buffer_distance_ft = config.get('buffer_distance_ft')
        self.speed_tolerance_mph = config.get('speed_tolerance_mph')
        self.max_consecutive_points = config.get('max_consecutive_points')
        self.visualize_data = config.get('visualize_data')
        self.display_results = config.get('display_results')
        self.save_results = config.get('save_results')
        self.geometrias = []
        self.start_time = None
        self.end_time = None
        self.angulo_giro_umbral = config.get('angulo_giro_umbral', 30)
        self.last_heading_deg = None
        self.speed_attribute = config.get('gps_points_info').get('name_attributes').get('speed')
        self.time_attribute = config.get('gps_points_info').get('name_attributes').get('time')
        self.real_route_attribute = config.get('gps_points_info').get('name_attributes').get('real_route')

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def _visualize_data(self):
        pass
    
    @abstractmethod
    def _save_results(self):
        pass
    
    @abstractmethod
    def _is_valid_route(self):
        pass