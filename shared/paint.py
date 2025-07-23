from qgis.core import (QgsFeature, QgsTextFormat, QgsPalLayerSettings,QgsVectorLayerSimpleLabeling, QgsGeometry, QgsPointXY, QgsVectorLayer, QgsProject, QgsLineSymbol, QgsMarkerSymbol, QgsMarkerLineSymbolLayer)
from qgis.PyQt.QtGui import QFont, QColor
import math



def dibujar_etiquetado(capa_puntos: QgsVectorLayer, field: str, additional_field: str = None):
    if not capa_puntos.isValid():
        return False
    layer_settings = QgsPalLayerSettings()
    if additional_field and additional_field in capa_puntos.fields().names():
        layer_settings.fieldName = f'concat("{field}", \' - \', "{additional_field}")'
        layer_settings.isExpression = True
    else:
        layer_settings.fieldName = field
        layer_settings.isExpression = False
    layer_settings.enabled = True
    text_format = QgsTextFormat()
    text_format.setFont(QFont("Arial", 15))
    text_format.setColor(QColor("black"))
    layer_settings.setFormat(text_format)
    labels = QgsVectorLayerSimpleLabeling(layer_settings)
    capa_puntos.setLabeling(labels)
    capa_puntos.setLabelsEnabled(True)
    capa_puntos.triggerRepaint()
    return True



def paint_buffer(buffer_layer, geom_buffer):
  provider = buffer_layer.dataProvider()
  feat_buffer = QgsFeature(buffer_layer.fields())
  feat_buffer.setGeometry(geom_buffer)
  provider.addFeatures([feat_buffer])
  buffer_layer.updateExtents()
  buffer_layer.triggerRepaint()



def paint_snapped_point(capa_destino_puntos_snapped, punto):
    if isinstance(punto, QgsPointXY):
        geom_punto = QgsGeometry.fromPointXY(punto)
    elif isinstance(punto, QgsGeometry):
        geom_punto = punto
    else:
        print(f"Error: El punto debe ser QgsPointXY o QgsGeometry, no {type(punto)}.")
        return
    prov_destino = capa_destino_puntos_snapped.dataProvider()
    feat_punto = QgsFeature()
    feat_punto.setGeometry(geom_punto)
    prov_destino.addFeatures([feat_punto])
    capa_destino_puntos_snapped.updateExtents()



def dibujar_ruta_con_flechas(puntos_gps_path):
    gps_layer = QgsVectorLayer(puntos_gps_path, 'Puntos GPS', 'ogr')
    if not gps_layer.isValid():
        print(f'Error al cargar capa de puntos GPS: {puntos_gps_path}')
        return
    field_names = gps_layer.fields().names()
    if 'timestamp' in field_names:
        feats = sorted(gps_layer.getFeatures(), key=lambda f: parse_hms_to_seconds(f['timestamp']))
    elif 'time' in field_names:
        feats = sorted(gps_layer.getFeatures(), key=lambda f: parse_hms_to_seconds(f['time']))
    else:
        feats = sorted(gps_layer.getFeatures(), key=lambda f: f.id())
    points = [f.geometry().asPoint() for f in feats]
    ruta_layer = QgsVectorLayer(f'LineString?crs={gps_layer.crs().authid()}', 'Ruta GPS', 'memory')
    ruta_pr = ruta_layer.dataProvider()
    if len(points) >= 2:
        geom_line = QgsGeometry.fromPolylineXY(points)
        feat_line = QgsFeature()
        feat_line.setGeometry(geom_line)
        ruta_pr.addFeatures([feat_line])
    ruta_layer.updateExtents()
    arrow_layer = QgsVectorLayer(f'LineString?crs={gps_layer.crs().authid()}', 'Flechas Ruta', 'memory')
    arrow_pr = arrow_layer.dataProvider()
    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i + 1]
        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        dist = math.hypot(dx, dy)
        if dist == 0:
            continue
        ux, uy = dx / dist, dy / dist
        arrow_len = 10
        angle = math.radians(30)
        def rot(vx, vy, ang):
            return vx * math.cos(ang) - vy * math.sin(ang), vx * math.sin(ang) + vy * math.cos(ang)
        v1x, v1y = rot(-ux, -uy, angle)
        v2x, v2y = rot(-ux, -uy, -angle)
        h1 = QgsPointXY(p2.x() + v1x * arrow_len, p2.y() + v1y * arrow_len)
        h2 = QgsPointXY(p2.x() + v2x * arrow_len, p2.y() + v2y * arrow_len)
        f1 = QgsFeature()
        f1.setGeometry(QgsGeometry.fromPolylineXY([p2, h1]))
        f2 = QgsFeature()
        f2.setGeometry(QgsGeometry.fromPolylineXY([p2, h2]))
        arrow_pr.addFeatures([f1, f2])
    arrow_layer.updateExtents()
    QgsProject.instance().addMapLayer(ruta_layer)
    QgsProject.instance().addMapLayer(arrow_layer)
    sym = ruta_layer.renderer().symbol()
    sym.setColor(QColor('blue'))
    sym.setWidth(1.0)
    ruta_layer.triggerRepaint()
    sym2 = arrow_layer.renderer().symbol()
    sym2.setColor(QColor('red'))
    sym2.setWidth(1.0)
    arrow_layer.triggerRepaint()



def dibujar_flechas_gps_snapped(puntos_layer: QgsVectorLayer, geometrias: list) -> QgsVectorLayer:
  """Crea una capa de flechas negras que van desde cada punto GPS al punto snapped almacenado en geometrias."""
  crs = puntos_layer.crs()
  arrow_layer = QgsVectorLayer(f"LineString?crs={crs.authid()}", "Flechas GPS-Snapped", "memory")
  pr = arrow_layer.dataProvider()
  arrow_layer.startEditing()
  for idx, feat in enumerate(puntos_layer.getFeatures()):
      snapped_geom = geometrias[idx].get('geom_punto_snapped')
      if snapped_geom is None:
          continue
      orig_pt = feat.geometry().asPoint()
      snap_pt = snapped_geom.asPoint()
      arrow_feat = QgsFeature()
      arrow_feat.setGeometry(QgsGeometry.fromPolylineXY([orig_pt, snap_pt]))
      pr.addFeature(arrow_feat)
  arrow_layer.commitChanges()
  line_sym = QgsLineSymbol.createSimple({'color':'black','width':'0.5'})
  arrow_marker = QgsMarkerSymbol.createSimple({'name':'filled_arrowhead','color':'black','size':'4'})
  marker_line = QgsMarkerLineSymbolLayer()
  marker_line.setSubSymbol(arrow_marker)
  marker_line.setPlacement(QgsMarkerLineSymbolLayer.LastVertex)
  line_sym.appendSymbolLayer(marker_line)
  arrow_layer.renderer().setSymbol(line_sym)
  QgsProject.instance().addMapLayer(arrow_layer)
  return arrow_layer