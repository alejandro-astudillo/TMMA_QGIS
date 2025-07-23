import importlib

# --- Importa la configuración y las utilidades ---
import config
from algorithms import interface, original, modified # Importar los módulos para poder recargarlos
from shared import paint, helpers

# --- Importa las estrategias que has creado ---
from algorithms.original import OriginalTMMA
from algorithms.modified import ModifiedTMMA

# --- Forzar la recarga de los módulos para desarrollo ---
importlib.reload(config)
importlib.reload(paint)
importlib.reload(interface)
importlib.reload(original)
importlib.reload(modified)
importlib.reload(helpers)

def main():
    """
    Punto de entrada principal para ejecutar los algoritmos de Map Matching.
    """
    # --- 1. Elige qué algoritmo y configuración usar ---
    # Cambiando esta línea, puedes ejecutar una u otra estrategia.
    algorithm_to_use = OriginalTMMA # <--- Cambia esto para usar el algoritmo que desees

    # --- 2. Carga la red de calles ---
    road_layer = QgsVectorLayer(config.CONFIG["road_network_path"], "Red Vial", "ogr")
    if not road_layer.isValid():
        print("Error: No se pudo cargar la capa de la red vial.")
        return
    
    # --- 3. Carga la capa de puntos GPS ---
    gps_layer = QgsVectorLayer(config.CONFIG["gps_points_info"]["path"], "Puntos GPS", "ogr")

    if gps_layer.isValid(): # Añadimos las capas al proyecto para verlas en QGIS
      QgsProject.instance().addMapLayer(road_layer)
      QgsProject.instance().addMapLayer(gps_layer)

      # --- 4. Ejecuta el algoritmo ---
      map_matcher = algorithm_to_use(gps_layer, road_layer, config.CONFIG)
      map_matcher.run()
    else:
        print(f"Advertencia: No se pudo cargar la capa GPS: {config.CONFIG['gps_points_info']['path']}")

# --- Ejecuta la función principal ---
main()