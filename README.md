# ABALONE_PROJECT

## Cómo usar el proyecto

1. **Obtené el proyecto.** Clonalo con git (ver la sección "Clonar el repositorio") y abrí una terminal dentro de la carpeta raíz (la que contiene `preprocesamiento.py` y `requirements.txt`).
```bash
# HTTPS
git clone https://github.com/ArturoJorge/abalone_project.git

# entrar a la carpeta del proyecto
cd abalone_project
```

2. **Preparé el entorno**
### 1. Instalar Python 3.12.14

Verificá la versión instalada:

```bash
python --version
```

Debería mostrar `Python 3.12.14`. Si no es así, instalala desde [python.org](https://www.python.org/downloads/) (o con `pyenv install 3.12.14` si usás pyenv).

### 2. Crear un entorno virtual

Desde la carpeta raíz del proyecto:

```bash
python -m venv .venv
```

### 3. Activar el entorno virtual

- Linux / macOS:
  ```bash
  source .venv/bin/activate
  ```
- Windows (PowerShell):
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- Windows (cmd):
  ```cmd
  .venv\Scripts\activate.bat
  ```

Cuando el entorno está activo, la terminal muestra `(.venv)` al inicio de la línea.

### 4. Instalar las dependencias

Todas las librerías necesarias están en `requirements.txt`:

```bash
pip install -r requirements.txt
```

3. **Colocá los datos de entrada** verificar que los archivos .csv de los datos crudos están en `data/raw/`:
   - `abalone_raw.csv`: dataset crudo con las columnas `Sex`, `Length`, `Diameter`, `Height`, `Whole_weight`, `Shucked_weight`, `Viscera_weight`, `Shell_weight`.
   - `rings.csv`: archivo con la columna `Rings`.

4. **Ejecutá el preprocesamiento** con `python preprocesamiento.py`.

```bash
python preprocesamiento.py
```

## Notas

- Para recuperar una versión anterior, buscá en `data/processed/versions/` el archivo con el número de versión y el prefijo del hash correspondiente.
- El hash depende del contenido exacto del archivo. Si cambia la versión de pandas o scikit-learn, el formato de salida podría variar levemente y generar una versión nueva aunque los datos sean equivalentes. Por eso conviene usar siempre las versiones fijadas en `requirements.txt`.
- Editar `abalone_clean.csv` a mano genera una versión nueva en la próxima ejecución, pero esa modificación no queda descrita en `transformations`.
- Para salir del entorno virtual, ejecutá `deactivate`.