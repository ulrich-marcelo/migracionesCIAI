# Google Trends Scraper 📈

Este es un script de Python para descargar datos de Google Trends utilizando la biblioteca pytrends. El script extrae los dos CSV principales que se ven en la interfaz de usuario de Google Trends:
    1. Interés a lo largo del tiempo (Interest over time)
    2. Interés por región (Interest by region)

Automatiza el proceso para múltiples términos de búsqueda, maneja los límites de tasa de Google (rate limits) con un backoff simple y guarda los resultados en archivos CSV limpios.

## Instalación
Se recomienda encarecidamente utilizar un entorno virtual (.venv) para gestionar las dependencias del proyecto y evitar conflictos.

### Clona o descarga el repositorio 
Puedes clonar el repositorio si tienes git instalado:
git clone [URL_DE_TU_REPOSITORIO]
cd [NOMBRE_DEL_REPOSITORIO]

O simplemente descarga el archivo trends_scraper.py en una carpeta.

### Crea un entorno virtual
En la carpeta del proyecto, ejecuta:
python -m venv .venv

#### Activa el entorno virtual

En Windows (cmd):
.venv\Scripts\activate

En macOS / Linux (bash/zsh):
source .venv/bin/activate

Verás (.venv) al principio de la línea de tu terminal si se activó correctamente.

### Instala las dependencias
Este script requiere pytrends, pandas y tqdm. Instálalas usando pip:

pip install pytrends pandas tqdm

## Uso
El script se ejecuta desde la línea de comandos. Debes proporcionar los términos de búsqueda y un rango de fechas.

python trends_scraper.py [OPCIONES]

### Parámetros del Script
Aquí están todos los argumentos de línea de comandos que puedes usar:

#### Fuente de Términos (Obligatorio)
Debes usar una (y solo una) de estas dos opciones:
--terms "termino1, termino2" Una cadena de texto con los términos de búsqueda separados por comas.
--input archivo.csv La ruta a un archivo CSV que contenga una columna llamada term. El script procesará un término por cada fila.

#### Rango de Fechas (Obligatorio)
--start YYYY-MM-DD La fecha de inicio para la consulta (ej. 2023-01-01).

--end YYYY-MM-DD La fecha de finalización para la consulta (ej. 2024-12-31).

#### Parámetros Opcionales de Búsqueda
--geo <CÓDIGO> Código de geografía (ej. AR para Argentina, US para Estados Unidos). Si se omite, la búsqueda es mundial ("").

--cat <ID> ID de la categoría de búsqueda (ej. 7 para "Finanzas"). El valor predeterminado es 0 (Todas las categorías). [No hay información disponible sobre qué codigo es para cada categoría, para ver eso, elegí la categoria que quieras en Google Trends y mirá el link, el parametro cat dirá el ID de categoría seleccionado. Salvo casos especificos, se recomienda dejar el valor por defecto]

--gprop <PROPIEDAD> La propiedad de Google donde buscar. El valor predeterminado es web. Opciones:
* web (Búsqueda web - predeterminado)
* images (Búsqueda de imágenes)
* news (Búsqueda de noticias)
* youtube (Búsqueda de YouTube)
* shopping (Google Shopping)

#### Parámetros Opcionales de Configuración
--hl <IDIOMA> Idioma del host (ej. es-AR, en-US). Predeterminado: es-AR.

--tz <MINUTOS> Desplazamiento de la zona horaria en minutos desde UTC. Predeterminado: 0 (UTC). Usa -180 para Argentina (GMT-3).

--outdir <CARPETA> Carpeta de destino para guardar los CSV. Predeterminado: trends_output.

--combine Si se incluye este flag, el script creará archivos CSV adicionales que combinan los resultados de todos los términos en un solo archivo (uno para "interés en el tiempo" y otro para "interés por región").

--sleep <SEGUNDOS> Tiempo base de espera (en segundos) entre cada solicitud a Google. Predeterminado: 1.5.

--retries <NÚMERO> Número máximo de reintentos por solicitud si falla (por ejemplo, por límite de tasa). Predeterminado: 4.

## Ejemplos
### Ejemplo 1: Básico
Buscar tres términos en la Búsqueda Web de Google en un rango de fechas específico.

python trends_scraper.py --terms "inteligencia artificial, machine learning, datos" --start 2022-01-01 --end 2025-08-31

### Ejemplo 2: Desde un archivo CSV
Leer los términos de un archivo llamado terminos.csv y combinar los resultados.

terminos.csv:
term
python
java
javascript

Comando:
python trends_scraper.py --input terminos.csv --start 2023-01-01 --end 2025-08-31 --combine

### Ejemplo 3: Búsqueda en YouTube
Buscar el interés de un término solo en YouTube.

python trends_scraper.py --terms "python" --start 2024-01-01 --end 2024-12-31 --gprop youtube

### Ejemplo 4: Búsqueda Regional (Subregiones)
Buscar el interés por el término "milei" dentro de Argentina (--geo AR) para obtener el detalle por provincia.

python trends_scraper.py --terms "milei" --start 2023-01-01 --end 2023-12-31 --geo AR

## Estructura de Salida
El script creará una carpeta (predeterminada: trends_output) con la siguiente estructura:

trends_output/
├── per_term/
│   ├── inteligencia artificial__interest_over_time.csv
│   ├── inteligencia artificial__interest_by_country.csv
│   ├── machine learning__interest_over_time.csv
│   ├── machine learning__interest_by_country.csv
│   └── ... (archivos para cada término)
│
└── combined/  (Solo si se usa --combine)
    ├── interest_over_time__combined.csv
    └── interest_by_country__combined.csv

Nota: Si usas el parámetro --geo (ej. --geo AR), los archivos de región se llamarán ...__interest_by_region.csv en lugar de ...__interest_by_country.csv, ya que contendrán subregiones (ej. provincias) en lugar de países.

## Notas Adicionales
* Límites de Tasa: Ten cuidado al consultar una gran cantidad de términos. Google puede bloquear temporalmente tu IP si detecta demasiadas solicitudes. El script implementa un reintento y un backoff exponencial simple, pero aun así es posible ser bloqueado.

* Precisión: Los datos de Google Trends son muestreados y normalizados. Los resultados pueden variar ligeramente entre ejecuciones.