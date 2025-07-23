from qgis.core import (QgsVectorLayer, QgsProject, QgsFeature, QgsGeometry, QgsPointXY, QgsSpatialIndex, QgsSymbol, QgsSingleSymbolRenderer,QgsFeatureRequest, QgsCoordinateReferenceSystem, QgsDistanceArea, QgsMapLayer)
from qgis.PyQt.QtGui import QColor
from qgis import processing
from typing import Union, Dict, Any
import re

def get_or_create_layer(
    layer_name: str,
    layer_type: str,
    crs: QgsCoordinateReferenceSystem,
    style_dict: Union[Dict[str, Any], None] = None
) -> Union[QgsVectorLayer, None]:
    project = QgsProject.instance()
    layers = project.mapLayersByName(layer_name)
    if layers:
        return layers[0]
    geom_type_str = layer_type.split('?')[0]
    layer_definition = f"{geom_type_str}?crs={crs.authid()}"
    new_layer = QgsVectorLayer(layer_definition, layer_name, "memory")
    if not new_layer.isValid():
        return None
    if style_dict:
        try:
            fill_color_str = style_dict.get(
                'fill_color', 'blue')
            opacity = style_dict.get('opacity', 0.4)
            outline_color_str = style_dict.get(
                'outline_color', 'transparent')
            point_size = style_dict.get('size', None)
            stroke_width = style_dict.get('stroke_width', None)
            alpha = int(opacity * 255)
            fill_color = QColor(fill_color_str)
            fill_color.setAlpha(alpha)
            outline_color = QColor(outline_color_str)
            symbol = QgsSymbol.defaultSymbol(new_layer.geometryType())
            if symbol:
                symbol.setColor(fill_color)
                if point_size is not None and new_layer.geometryType() == 0:
                    symbol.setSize(point_size)
                if symbol.symbolLayerCount() > 0:
                    symbol.symbolLayer(0).setStrokeColor(outline_color)
                    if stroke_width is not None:
                        symbol.symbolLayer(0).setStrokeWidth(stroke_width)
                renderer = QgsSingleSymbolRenderer(symbol)
                new_layer.setRenderer(renderer)
        except (TypeError, ValueError, AttributeError) as e:
            print(
                f"Advertencia: No se pudo aplicar estilo personalizado a '{layer_name}': {e}")

    project.addMapLayer(new_layer)
    return new_layer



def get_buffer_geom(
    punto_feature: QgsFeature,
    distancia_buffer: float = 50.0
) -> Union[QgsGeometry, None]:
    geom_punto = punto_feature.geometry()
    geom_buffer = geom_punto.buffer(
        distancia_buffer, 8)
    return geom_buffer



def found_closest_segments(geom_buffer, capa_calles):
    indice_calles = QgsSpatialIndex(capa_calles.getFeatures())
    ids_candidatos = indice_calles.intersects(geom_buffer.boundingBox())
    calles_intersectantes = []
    request = QgsFeatureRequest()
    for calle_id in ids_candidatos:
        request.setFilterFid(calle_id)
        calle_feature = next(capa_calles.getFeatures(request), None)
        if calle_feature:
            geom_calle = calle_feature.geometry()
            if geom_calle and geom_calle.isGeosValid() and geom_buffer.intersects(geom_calle):
                calles_intersectantes.append(calle_feature)
    return calles_intersectantes



def most_closest_segment(point, calles_intersectantes):
    geom_punto = point.geometry()
    calle_mas_cercana = None
    distancia_minima = float('inf')

    for calle_feature in calles_intersectantes:
        geom_calle = calle_feature.geometry()
        distancia_actual = geom_calle.distance(geom_punto)
        if distancia_actual < distancia_minima:
            distancia_minima = distancia_actual
            calle_mas_cercana = calle_feature

    return calle_mas_cercana



def project_point(point, calle_mas_cercana):
    point = point.geometry()
    geom_punto_snapped = None
    punto_xy_original = point.asPoint()

    geom_calle_cercana = calle_mas_cercana.geometry()

    if point.isGeosValid() and geom_calle_cercana.isGeosValid():
        resultado_closest = geom_calle_cercana.closestSegmentWithContext(
            punto_xy_original)
        _, punto_proyectado, _, _ = resultado_closest

        if isinstance(punto_proyectado, QgsPointXY):
            geom_punto_snapped = QgsGeometry.fromPointXY(
                punto_proyectado)
    return geom_punto_snapped



def calcular_distancia_mas_corta(punto_inicial_geom, punto_final_geom, red_vial):
    punto_inicial = punto_inicial_geom.asPoint()
    punto_final = punto_final_geom.asPoint()
    if punto_inicial == punto_final:
        return 0
    params = {
        'INPUT': red_vial,
        'START_POINT': f"{punto_inicial.x()},{punto_inicial.y()}",
        'END_POINT': f"{punto_final.x()},{punto_final.y()}",
        'STRATEGY': 0,
        'OUTPUT': 'memory:'
    }
    resultado = processing.run("qgis:shortestpathpointtopoint",params)
    ruta_layer = resultado['OUTPUT']
    longitud_elipsoidal = None
    for feature in ruta_layer.getFeatures():
        geometria = feature.geometry()
        distance_area = QgsDistanceArea()
        distance_area.setEllipsoid('WGS84')
        distance_area.setSourceCrs(
            ruta_layer.crs(), QgsProject.instance().transformContext())
        longitud_elipsoidal = distance_area.measureLength(geometria)
    return longitud_elipsoidal



def verificar_velocidad_en_rango(
    tiempo_str1: str,
    tiempo_str2: str,
    velocidad_gps1_kmh: float,
    velocidad_gps2_kmh: float,
    distancia_red_metros: float,
    epsilon_velocidad_kmh: float
) -> Union[bool, None]:
    segundos1 = parse_hms_to_seconds(tiempo_str1)
    segundos2 = parse_hms_to_seconds(tiempo_str2)
    delta_tiempo_seg = abs(segundos1 - segundos2)
    velocidad_promedio_gps_kmh = (
        abs(velocidad_gps1_kmh) + abs(velocidad_gps2_kmh)) / 2.0

    if distancia_red_metros < 0:
        return True
    velocidad_calculada_ms = distancia_red_metros / delta_tiempo_seg
    velocidad_calculada_mph = velocidad_calculada_ms * 2.23694
    diferencia_abs_velocidad = abs(
        velocidad_calculada_mph - velocidad_promedio_gps_kmh)
    if diferencia_abs_velocidad <= epsilon_velocidad_kmh:
        return True
    return False
  


def get_feature_by_id(layer: QgsVectorLayer, feature_id: int) -> Union[QgsFeature, None]:
    request = QgsFeatureRequest()
    request.setFilterFid(feature_id)
    feature = next(layer.getFeatures(request), None)
    return feature



def add_layer(layer_to_check: QgsMapLayer):
    project = QgsProject.instance()
    existing_layers = project.mapLayers().values()
    name_found = False
    for existing_layer in existing_layers:
        if existing_layer.name() == layer_to_check.name():
            name_found = True
            break
    if not name_found:
        project.addMapLayer(layer_to_check)



def parse_hms_to_seconds(tiempo_str: str) -> Union[float, None]:
    tiempo_match = re.search(r'(\d+:\d+:\d+)', tiempo_str)
    if tiempo_match:
        tiempo_str = tiempo_match.group(1)
    
    parts = tiempo_str.strip().split(':')
    if len(parts) != 3:
        raise ValueError("Formato debe ser H:MM:SS")
    horas = int(parts[0])
    minutos = int(parts[1])
    segundos = int(parts[2])
    if not (0 <= minutos < 60 and 0 <= segundos < 60 and horas >= 0):
        raise ValueError("Valores H/M/S fuera de rango")
    return float(horas * 3600 + minutos * 60 + segundos)
