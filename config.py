
CONFIG = {
  # Ruta de la red de calles
  "road_network_path": "../proyecto/data/calles_portage/PortageRoads.shp",  # Ruta al archivo Shapefile de la red de calles

  # Información del archivo de puntos GPS
  "gps_points_info": { 
    "path": '../proyecto/data/series_portage/1190268102/data_1.shp',  # Ruta al archivo Shapefile de los puntos GPS
    "frecuency": 10, # Frecuencia de muestreo de los puntos (en segundos)
    "name_attributes": {
      "speed": "Speed", # velocidad en mph
      "time": "Time", # tiempo en formato HH:MM:SS AM/PM, o tambien HH:MM:SS
      "real_route": "NEAR_FID" # id de la calle o ruta real por la que pasó el vehículo
    },
  },

  # Parámetros de configuración
  "buffer_distance_ft": 60.0, # Radio del buffer en pies
  "speed_tolerance_mph": 35, # Tolerancia para la validación de velocidad, en millas por hora
  "max_consecutive_points": 2, # Número máximo de puntos consecutivos a analizar en la búsqueda de rutas válidas
  "angulo_giro_umbral": 30, # Umbral para el ángulo de giro (solo para el algoritmo modificado)

  # Parámetros de visualización y resultados
  "visualize_data": True, # Pinta los datos en el lienzo de QGIS
  "save_results": True, # Guarda los resultados en un archivo .txt
}