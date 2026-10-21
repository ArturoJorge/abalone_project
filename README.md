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
