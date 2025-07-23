from .interface import MapMatchingStrategy
from qgis.core import (QgsVectorLayer)
import time
import os 
from shared.helpers import (
    get_buffer_geom, found_closest_segments, most_closest_segment, 
    get_feature_by_id, get_or_create_layer, project_point, calcular_distancia_mas_corta, verificar_velocidad_en_rango
)
from shared.paint import paint_snapped_point, paint_buffer, dibujar_etiquetado, dibujar_ruta_con_flechas, dibujar_flechas_gps_snapped



class OriginalTMMA(MapMatchingStrategy):
    """Implementación del algoritmo de Map Matching Topológico original."""

    def run(self):
        # --- Inicialización ---
        puntos_gps_list = list(self.gps_points_layer.getFeatures())
        if not puntos_gps_list:
            print("La capa de puntos GPS está vacía.")
            return
        
        # --- Geometrias ---
        self.geometrias = [{"geom_buffer": None, "geom_punto_snapped": None, "assigned_route": None, "closest_segments": None} for _ in range(len(puntos_gps_list))]

        # --- Inicio Tiempo ---
        self.start_time = time.time()

        i = 0
        j = i + 1

        # --- Bucle Principal del Algoritmo ---
        while i < len(puntos_gps_list) and j < len(puntos_gps_list):
          punto_i = puntos_gps_list[i]
          punto_j = puntos_gps_list[j]

          punto_i_id = punto_i.id()
          punto_j_id = punto_j.id()

          # -*- Crear Buffer -*-
          if self.geometrias[punto_i_id]['geom_buffer'] is None:
            self.geometrias[punto_i_id]['geom_buffer'] = get_buffer_geom(
                punto_i,
                self.buffer_distance_ft,
            )
          if self.geometrias[punto_j_id]['geom_buffer'] is None:
            self.geometrias[punto_j_id]['geom_buffer'] = get_buffer_geom(
                punto_j,
                self.buffer_distance_ft,
            )

          geom_buffer_punto_i = self.geometrias[punto_i_id]['geom_buffer']
          geom_buffer_punto_j = self.geometrias[punto_j_id]['geom_buffer']

          # -*- Calles Intersectantes Cercanas -*-
          if self.geometrias[punto_i_id]['closest_segments'] is None:
            self.geometrias[punto_i_id]['closest_segments'] = found_closest_segments(geom_buffer_punto_i, self.road_layer)
          if self.geometrias[punto_j_id]['closest_segments'] is None:
            self.geometrias[punto_j_id]['closest_segments'] = found_closest_segments(geom_buffer_punto_j, self.road_layer)

          calles_intersectantes_punto_i = self.geometrias[punto_i_id]['closest_segments']
          calles_intersectantes_punto_j = self.geometrias[punto_j_id]['closest_segments']

          # -*- Verificar Calles Intersectantes -*-
          if len(self.geometrias[punto_i_id]['closest_segments']) == 0 and len(self.geometrias[punto_j_id]['closest_segments']) == 0:
            i += 2
            j = i + 1
            continue

          if len(calles_intersectantes_punto_i) == 0:
            i += 1
            j = i + 1
            calle_mas_cercana_punto_j = most_closest_segment(
              punto_j, calles_intersectantes_punto_j)
            continue

          if len(calles_intersectantes_punto_j) == 0:
            j += 1
            calle_mas_cercana_punto_i = most_closest_segment(
              punto_i, calles_intersectantes_punto_i)
            continue
          
          fw = False
          consecutive_points = 1
          while consecutive_points <= self.max_consecutive_points:
            if consecutive_points > 1:
              if fw:
                fw = False
                punto_candidato_i_encontrado = False
                i -= 1
                while not punto_candidato_i_encontrado:
                  if i > 0:
                    punto_i = puntos_gps_list[i]
                    punto_i_id = punto_i.id()
                    if self.geometrias[punto_i_id]['geom_buffer'] is None:
                      self.geometrias[punto_i_id]['geom_buffer'] = get_buffer_geom(
                          punto_i,
                          self.buffer_distance_ft,
                      )
                    if self.geometrias[punto_i_id]['closest_segments'] is None:
                      self.geometrias[punto_i_id]['closest_segments'] = found_closest_segments(self.geometrias[punto_i_id]['geom_buffer'], self.road_layer)
                    
                    calles_intersectantes_punto_i = self.geometrias[punto_i_id]['closest_segments']
                    if len(calles_intersectantes_punto_i) > 0:
                      punto_candidato_i_encontrado = True
                    else:
                      i -= 1
                  else:
                    break
                if not punto_candidato_i_encontrado:
                  break
              else:
                fw = True
                punto_candidato_j_encontrado = False
                j += 1
                while not punto_candidato_j_encontrado:
                  if j < len(puntos_gps_list):
                    punto_j = puntos_gps_list[j]
                    punto_j_id = punto_j.id()
                    if self.geometrias[punto_j_id]['geom_buffer'] is None:
                      self.geometrias[punto_j_id]['geom_buffer'] = get_buffer_geom(
                          punto_j,
                          self.buffer_distance_ft,
                      )
                    if self.geometrias[punto_j_id]['closest_segments'] is None:
                      self.geometrias[punto_j_id]['closest_segments'] = found_closest_segments(self.geometrias[punto_j_id]['geom_buffer'], self.road_layer)
                    
                    if len(self.geometrias[punto_j_id]['closest_segments']) > 0:
                      punto_candidato_j_encontrado = True
                      calles_intersectantes_punto_j = self.geometrias[punto_j_id]['closest_segments']
                    else:
                      j += 1
                  else:
                    break
                if not punto_candidato_j_encontrado:
                  break
            
            route_validation = False
            calle_mas_cercana_punto_i = most_closest_segment(
                  punto_i, calles_intersectantes_punto_i)

            calles_intersectantes_punto_j_copy = calles_intersectantes_punto_j.copy()
              
            while len(calles_intersectantes_punto_j_copy) > 0:
              calle_mas_cercana_punto_j = most_closest_segment(
                  punto_j, calles_intersectantes_punto_j_copy)
              calles_intersectantes_punto_j_copy.remove(calle_mas_cercana_punto_j)
              route_validation = self._is_valid_route(punto_i, punto_j, calle_mas_cercana_punto_i, calle_mas_cercana_punto_j)

              if route_validation:
                self.geometrias[punto_i_id]['assigned_route'] = calle_mas_cercana_punto_i
                self.geometrias[punto_j_id]['assigned_route'] = calle_mas_cercana_punto_j
                break
            
            if route_validation:
              break
            
            calle_mas_cercana_punto_j = most_closest_segment(
              punto_j, calles_intersectantes_punto_j)
            
            route_validation_previous_point = False
            calles_intersectantes_punto_i_copy = calles_intersectantes_punto_i.copy()

            while len(calles_intersectantes_punto_i_copy) > 0 and len(calles_intersectantes_punto_j) > 0:
              punto_anterior_a_i = None
              if punto_i_id > 0:
                punto_anterior_a_i = get_feature_by_id(self.gps_points_layer, punto_i_id-1)
              else:
                break

              calle_mas_cercana_punto_i = most_closest_segment(
                punto_i, calles_intersectantes_punto_i_copy)
              calles_intersectantes_punto_i_copy.remove(calle_mas_cercana_punto_i)
              route_validation = self._is_valid_route(punto_i, punto_j, calle_mas_cercana_punto_i, calle_mas_cercana_punto_j)

              if not route_validation:
                continue

              if punto_anterior_a_i is not None:
                if self.geometrias[punto_anterior_a_i.id()]['assigned_route'] is not None:
                  calle_mapeada_punto_anterior_a_i = self.geometrias[punto_anterior_a_i.id()]['assigned_route']
                  route_validation_previous_point = self._is_valid_route(punto_anterior_a_i, punto_i, calle_mapeada_punto_anterior_a_i, calle_mas_cercana_punto_i)

                  if route_validation_previous_point:
                    self.geometrias[punto_i_id]['assigned_route'] = calle_mas_cercana_punto_i
                    self.geometrias[punto_j_id]['assigned_route'] = calle_mas_cercana_punto_j
                    self.geometrias[punto_anterior_a_i.id()]['assigned_route'] = calle_mapeada_punto_anterior_a_i
                    break
                else:
                  break

              else:
                calles_intersectantes_punto_i_copy.remove(calle_mas_cercana_punto_i)
            
            if route_validation_previous_point:
              break
            consecutive_points += 1

          i = j
          j = i + 1
        
        self.end_time = time.time()

        if self.visualize_data:
          self._visualize_data(self.gps_points_layer, puntos_gps_list, self.gps_points_path)
        if self.save_results:
          self._save_results(puntos_gps_list)
      
    def _is_valid_route(self, punto_i, punto_j, calle_mas_cercana_punto_i, calle_mas_cercana_punto_j):
      punto_i_id = punto_i.id()
      punto_j_id = punto_j.id()

      # -*- Proyectar Punto Snapped -*-
      geom_punto_snapped_i = project_point(punto_i, calle_mas_cercana_punto_i)
      self.geometrias[punto_i_id]['geom_punto_snapped'] = geom_punto_snapped_i

      geom_punto_snapped_j = project_point(punto_j, calle_mas_cercana_punto_j)
      self.geometrias[punto_j_id]['geom_punto_snapped'] = geom_punto_snapped_j

      # -*- Calcular Distancia mas corta -*-
      distancia = calcular_distancia_mas_corta(
          self.geometrias[punto_i_id]['geom_punto_snapped'],
          self.geometrias[punto_j_id]['geom_punto_snapped'],
          self.road_layer)

      def get_attribute_safe(feature, attr_names):
          for attr_name in attr_names:
              try:
                  return feature[attr_name]
              except KeyError:
                  continue
          raise KeyError(f"No se encontró ninguno de los atributos: {', '.join(attr_names)}")

      tiempo_punto_i = get_attribute_safe(punto_i, [self.time_attribute])
      tiempo_punto_j = get_attribute_safe(punto_j, [self.time_attribute])

      velocidad_gps1_kmh = get_attribute_safe(punto_i, [self.speed_attribute])
      velocidad_gps2_kmh = get_attribute_safe(punto_j, [self.speed_attribute])

      route_validation = verificar_velocidad_en_rango(
          tiempo_punto_i,
          tiempo_punto_j,
          velocidad_gps1_kmh,
          velocidad_gps2_kmh,
          distancia,
          self.speed_tolerance_mph
      )

      if not route_validation:
        self.geometrias[punto_i_id]['geom_punto_snapped'] = None
        self.geometrias[punto_j_id]['geom_punto_snapped'] = None
        self.geometrias[punto_i_id]['assigned_route'] = None
        self.geometrias[punto_j_id]['assigned_route'] = None
        
      return route_validation

    def _visualize_data(self, gps_points_layer: QgsVectorLayer, puntos_gps_list: list, path_puntos_gps: str):
      buffer_style = {
          'fill_color': 'blue',
          'opacity': 0.2,
          'outline_color': 'transparent'
      }
      nombre_capa_buffers = "Buffers Visualización"
      tipo_capa_buffers = "Polygon"

      puntos_snapped_style = {
          'fill_color': 'red',
          'opacity': 1,
          'outline_color': 'black',
          'size': 4,
      }
      nombre_capa_puntos_snapped = "Puntos Snapped"
      tipo_capa_puntos_snapped = "Point"

      capa_destino_buffers = get_or_create_layer(
              nombre_capa_buffers, tipo_capa_buffers, gps_points_layer.crs(), buffer_style)

      capa_destino_puntos_snapped = get_or_create_layer(
          nombre_capa_puntos_snapped, tipo_capa_puntos_snapped, gps_points_layer.crs(), puntos_snapped_style)

      # -*- Pintar Puntos Snapped -*-
      for geom in self.geometrias:
          if geom['geom_punto_snapped'] is not None:
              paint_snapped_point(capa_destino_puntos_snapped, geom['geom_punto_snapped'])

      # -*- Visualizar Buffer -*-
      for geom in self.geometrias:
          if geom['geom_buffer'] is not None:
              paint_buffer(capa_destino_buffers, geom['geom_buffer'])

      # -*- Dibujar Ruta GPS con Flechas -*-
      dibujar_ruta_con_flechas(self.gps_points_path)

      # -*- Función para dibujar flechas GPS->Snapped --
      dibujar_flechas_gps_snapped(self.gps_points_layer, self.geometrias)



    def _save_results(self, puntos_gps_list: list):

      total_puntos = len(puntos_gps_list)
      puntos_no_asignados = []
      puntos_incorrectos = []
      puntos_correctos = 0
      recall = 0
      precision = 0
      F1 = 0

      for i, feature in enumerate(puntos_gps_list):
          if i < len(self.geometrias) and self.geometrias[i]['assigned_route'] is not None:
              fid_2 = feature[self.real_route_attribute]
              assigned_route_id = self.geometrias[i]['assigned_route'].id()
              
              if fid_2 == assigned_route_id:
                  puntos_correctos += 1
              else:
                  puntos_incorrectos.append(feature.id())
          else:
              puntos_no_asignados.append(feature.id())

      """Genera un archivo de resultados con los datos de la asignación."""
      base_name_for_output = os.path.basename(self.gps_points_path)
      file_name_without_ext_for_output = os.path.splitext(base_name_for_output)[0]
      # Determinar el directorio padre del archivo shp de entrada
      parent_dir_of_shp = os.path.dirname(self.gps_points_path)
      if not parent_dir_of_shp: # Maneja casos donde path es solo un nombre de archivo
          parent_dir_of_shp = "."
          
      # Definir el subdirectorio 'results'
      output_results_dir = os.path.join(parent_dir_of_shp, "results")
      
      # Crear el subdirectorio 'results' si no existe
      os.makedirs(output_results_dir, exist_ok=True)
      
      output_file_path = os.path.join(output_results_dir, f"{file_name_without_ext_for_output}_results_ORIGINAL_BUFF_{int(self.config['buffer_distance_ft'])}_FRECUENCY_{self.gps_points_frecuency}.txt")

      with open(output_file_path, 'w', encoding='utf-8') as outfile:
          outfile.write("\n\n-*- TMMA ORIGINAL -*-\n" + "\n")

          # Archivo usado
          outfile.write(f"Archivo usado: {self.gps_points_path}" + "\n")

          # Constantes
          outfile.write("\n-*- Constantes -*-\n" + "\n")
          outfile.write(f"RADIO BUFFER: {self.config['buffer_distance_ft']}" + "\n")
          outfile.write(f"EPSILON VELOCIDAD KMH: {self.config['speed_tolerance_mph']}" + "\n")
          outfile.write(f"LIMITE DE PUNTOS CONSECUTIVOS: {self.max_consecutive_points}" + "\n")
          outfile.write(f"FRECUENCIA DE MUESTREO: {self.gps_points_frecuency}" + "\n")

          # Resultados
          outfile.write("\n-*- Resultados de la asignación -*-\n" + "\n")
          outfile.write(f"Puntos mapeados correctamente: {puntos_correctos}/{total_puntos}" + "\n")
          outfile.write(f"Puntos no asignados ({len(puntos_no_asignados)}): {puntos_no_asignados}" + "\n")
          outfile.write(f"Porcentaje de puntos no asignados: {(len(puntos_no_asignados) / total_puntos) * 100:.2f}%" + "\n")
          outfile.write(f"Puntos asignados incorrectamente ({len(puntos_incorrectos)}): {puntos_incorrectos}" + "\n")
          outfile.write(f"Porcentaje de puntos asignados incorrectamente: {(len(puntos_incorrectos) / total_puntos) * 100:.2f}%" + "\n")

          precision = puntos_correctos / (puntos_correctos + len(puntos_incorrectos))
          outfile.write(f"Precision: {precision:.2f}%" + "\n")
          outfile.write(f"Precision en porcentaje: {precision*100:.2f}%" + "\n")

          recall = puntos_correctos / (puntos_correctos + len(puntos_no_asignados))
          outfile.write(f"Recall: {recall:.2f}%" + "\n")
          outfile.write(f"Recall en porcentaje: {recall*100:.2f}%" + "\n")

          F1 = 2 * (precision * recall) / (precision + recall)
          outfile.write(f"F1: {F1:.2f}%" + "\n")
          outfile.write(f"F1 en porcentaje: {F1*100:.2f}%" + "\n")

          # Tiempo de ejecución
          outfile.write("\n-*- Tiempo de ejecución -*-\n" + "\n")
          outfile.write(f"{self.end_time - self.start_time:.2f} segundos ({(self.end_time - self.start_time) / 60:.2f} minutos)" + "\n")

      print(f"Resultados para '{os.path.basename(self.gps_points_path)}' guardados en: {output_file_path}")