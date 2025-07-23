# Algoritmo de Map-Matching Topológico para QGIS

Este proyecto implementa y compara dos versiones de un algoritmo de Map-Matching Topológico (TMMA) diseñado para funcionar dentro del entorno de QGIS. El código cuenta con una arquitectura orientada a objetos utilizando el patrón de diseño Strategy, lo que facilita la extensibilidad, el mantenimiento y la comparación de diferentes lógicas de map-matching.

## Características Principales

- **Arquitectura Modular**: El código está organizado en módulos con responsabilidades claras (configuración, algoritmos, utilidades, visualización).
- **Patrón de Diseño Strategy**: Permite cambiar fácilmente entre el algoritmo "Original" y el "Modificado" con solo cambiar una línea de código en `main.py`.
- **Configuración Centralizada**: Todas las rutas de archivos y parámetros del algoritmo (distancia de buffer, tolerancia de velocidad, etc.) se gestionan en un único archivo, `config.py`.
- **Visualización Integrada**: Los resultados del proceso, como los puntos proyectados sobre la red vial, los buffers de búsqueda y las rutas generadas, se dibujan automáticamente en el lienzo de QGIS para su análisis.
- **Reutilización de Código**: Las funciones comunes para cálculos geométricos y manipulación de capas se han centralizado en módulos compartidos para evitar la duplicación.

## Estructura del Proyecto

```
memoria-qgis/
├── main.py                 # Punto de entrada para ejecutar el proceso.
├── config.py               # Archivo de configuración (rutas y parámetros).
|
├── algorithms/               # Contiene las implementaciones de los algoritmos.
│   ├── interface.py        # Define la clase base abstracta (Strategy).
│   ├── original.py         # Implementación del algoritmo TMM original.
│   └── modified.py         # Implementación del algoritmo TMM modificado.
|
├── shared/                   # Módulos con código compartido.
│   ├── helpers.py          # Funciones auxiliares para lógica y geometría.
│   └── paint.py            # Funciones para dibujar en el lienzo de QGIS.
|
├── data/                     # Directorio para los archivos de datos (Shapefiles).
│   └── ...
```

## Requisitos

- Una instalación de la aplicación **QGIS** (versión con la que se desarrolló: 3.42.1-Münster).

## Instrucciones de Uso

1.  **Abrir QGIS**: Inicia QGIS y abre un proyecto nuevo o existente.

2.  **Configuración**: Abre el archivo `config.py` y asegúrate de que las variables `road_network_path` y `gps_points_info -> "path"` apunten a la ubicación correcta de tus archivos Shapefile. Luego, modifica los parámetros de configuración según tus necesidades.

3.  **Seleccionar el Algoritmo**: Abre `main.py`. Selecciona la clase del algoritmo que deseas ejecutar. Por defecto, está configurado para `OriginalTMMA`.
    ```python
    # Para usar el algoritmo original:
    algorithm_to_use = OriginalTMMA 
    
    # Para usar el modificado:
    # algorithm_to_use = ModifiedTMMA
    ```

4.  **Abrir la Consola de Python**: Ve al menú `Complementos (plugins) -> Consola de Python`.

5.  **Ejecutar el Script**: En la consola, abre el archivo `main.py` y ejecútalo.

6.  **Ver los Resultados**: El script cargará las capas necesarias y ejecutará el algoritmo. Al finalizar, verás nuevas capas temporales en QGIS mostrando los resultados de la visualización (buffers, puntos proyectados, calles, etc.). En un archivo .txt se guardan los resultados del algoritmo. Cuando finaliza el algoritmo se imprime la ubicación del archivo .txt en la consola.

## Configuración

Todos los parámetros del proyecto se gestionan desde el diccionario `CONFIG` en el archivo `config.py`. Esta estructura centralizada permite modificar el comportamiento del algoritmo fácilmente.

Principales claves del diccionario `CONFIG`:

- **`road_network_path`**: Ruta al Shapefile de la red de carreteras.
- **`gps_points_info`**: Un diccionario que contiene la información de la traza GPS:
    - `path`: Ruta al Shapefile de los puntos GPS a procesar.
    - `frecuency`: Frecuencia de muestreo de los puntos (en segundos).
    - `name_attributes`: Mapeo de los nombres de los atributos en el Shapefile (`speed`, `time`, `real_route`). En el archivo `config.py` hay más información sobre los atributos.
- **`buffer_distance_ft`**: Distancia del buffer de búsqueda alrededor de cada punto GPS, en pies.
- **`speed_tolerance_mph`**: Tolerancia para la validación de velocidad, en millas por hora.
- **`max_consecutive_points`**: Número máximo de puntos consecutivos a analizar en la búsqueda de rutas válidas.
- **`visualize_data`**: Booleano (`True`/`False`) para activar o desactivar el pintado de resultados en el lienzo de QGIS.
- **`save_results`**: Booleano (`True`/`False`) para guardar los resultados del procesamiento en un archivo de texto.

## Datos de Ejemplo

- En el directorio `data` se encuentran los archivos Shapefile de ejemplo. En el directorio `data/calles_portage` se encuentra la red de carreteras y en el directorio `data/series_portage` se encuentra la traza GPS. La red de carreteras corresponde a la red de carreteras de Portage County, Wisconsin, y la traza GPS corresponde a una traza GPS de un camión quita nieves.

## Sugerencias

- En el desarrollo del algoritmo se utilizó un IDE fuera de QGIS, específicamente Windsurf (Un fork de Visual Studio Code), para facilitar la escritura del código. Pero la ejecución del algoritmo se debe hacer dentro de QGIS.
- Cuando el código fue refactorizado la recarga de los archivos (el importlib.reload que se encuentra en el archivo main.py) tarda en volver a detectar cambios en los archivos, por lo que se recomienda verificar bien que los cambios se hayan guardado correctamente.

## Contacto

Si tienes alguna pregunta o sugerencia, no dudes en contactarme en alejandro.astudilloh@gmail.com.

