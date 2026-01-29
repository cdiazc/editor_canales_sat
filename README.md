# Editor de canales SAT

> ⚠️ **Aviso**: Este proyecto es 100% vibe coding - desarrollado mediante programación asistida por IA con [Claude Code](https://claude.ai/code).

Editor gráfico para gestionar canales y listas de favoritos en receptores de satélite que utilizan archivos SDX y CHL. Esta herramienta te permite editar, reorganizar y gestionar tus canales de manera sencilla e intuitiva a través de una interfaz gráfica moderna.

## Descripción

Este editor ha sido desarrollado específicamente para trabajar con archivos de configuración SDX y CHL de receptores satelitales. Ofrece una interfaz visual que facilita la gestión de grandes listas de canales, permitiéndote organizar tus favoritos de forma eficiente sin necesidad de editar archivos manualmente.

## Capturas de Pantalla

![Interfaz Principal](1.png)
*Vista principal del editor mostrando la lista de canales*

![Gestión de Favoritos](2.png)
*Gestión y organización de listas de favoritos*

![Importación desde KingOfSat](3.png)
*Importación de canales desde KingOfSat*

## Funcionalidades

- 📂 **Soporte SDX y CHL**: Carga y guarda archivos en ambos formatos
- ✨ **Editor de favoritos**: Crea, edita y elimina listas de canales favoritos
- 🔄 **Reordenación intuitiva**: Arrastra y suelta canales para reorganizarlos fácilmente
- 📥 **Importación desde KingOfSat**: Importa paquetes de canales directamente desde KingOfSat
- ➕ **Gestión de listas**: Crea nuevas listas de favoritos o elimina las existentes
- 💾 **Conversión de formatos**: Convierte entre SDX y CHL fácilmente
- 🎯 **Interfaz gráfica moderna**: Trabaja con tus canales de forma visual y sencilla
- 🖥️ **Multiplataforma**: Compatible con Linux, macOS y Windows

## Instalación

### Requisitos Previos

- Python 3.6 o superior
- Tkinter (interfaz gráfica)
- Git (para descargar el repositorio)

### Instalación en Linux

#### 1. Instalar Git

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install git
```

**Fedora:**
```bash
sudo dnf install git
```

**Arch Linux:**
```bash
sudo pacman -S git
```

#### 2. Instalar Python y Tkinter

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-tk
```

**Fedora:**
```bash
sudo dnf install python3 python3-tkinter
```

**Arch Linux:**
```bash
sudo pacman -S python tk
```

#### 3. Descargar el repositorio

```bash
git clone https://github.com/cdiazc/editor_canales_sat.git
cd editor_canales_sat
```

#### 4. Ejecutar el editor

```bash
python3 editor_canales.py
```

### Instalación en Windows

#### 1. Instalar Git

1. Descarga Git desde [https://git-scm.com/download/win](https://git-scm.com/download/win)
2. Ejecuta el instalador descargado
3. Sigue el asistente de instalación (puedes dejar las opciones por defecto)
4. Una vez instalado, abre "Git Bash" o "Símbolo del sistema"

#### 2. Instalar Python

1. Descarga Python desde [https://www.python.org/downloads/windows/](https://www.python.org/downloads/windows/)
2. Ejecuta el instalador
3. **IMPORTANTE**: Marca la casilla "Add Python to PATH" durante la instalación
4. Haz clic en "Install Now"
5. Tkinter se incluye automáticamente con Python en Windows

#### 3. Descargar el repositorio

Abre "Símbolo del sistema" o "PowerShell" y ejecuta:

```bash
git clone https://github.com/cdiazc/editor_canales_sat.git
cd editor_canales_sat
```

#### 4. Ejecutar el editor

```bash
python editor_canales.py
```

O simplemente haz doble clic en el archivo `editor_canales.py` desde el Explorador de Windows.

### Instalación en macOS

#### 1. Instalar Homebrew (si no lo tienes)

Abre la Terminal y ejecuta:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### 2. Instalar Git

```bash
brew install git
```

O utiliza el Git que viene preinstalado con Xcode Command Line Tools:

```bash
xcode-select --install
```

#### 3. Instalar Python y Tkinter

```bash
brew install python-tk@3.12
```

O si ya tienes Python instalado:

```bash
brew install python-tk
```

#### 4. Descargar el repositorio

```bash
git clone https://github.com/cdiazc/editor_canales_sat.git
cd editor_canales_sat
```

#### 5. Ejecutar el editor

```bash
python3 editor_canales.py
```

## Uso

1. **Cargar un archivo**: Usa "📂 Cargar SDX" o "📂 Cargar CHL" para abrir tu archivo de canales
2. **Editar canales**: Navega por las pestañas de favoritos y edita los canales
3. **Reorganizar**: Arrastra y suelta canales para cambiar su orden
4. **Gestionar listas**: Usa "➕ Nueva Lista" para crear listas o "🗑️ Eliminar Lista" para borrarlas
5. **Importar desde KingOfSat**: Usa el botón para agregar paquetes de canales desde la web
6. **Guardar cambios**: Usa "💾 Guardar en SDX" o "💾 Guardar en CHL" según el formato deseado

## Notas Importantes

- El Viark Combo probablemente ignora los nombres de las listas de favoritos al importar y solo los lee cuando se renombran manualmente desde el menú del deco. Es una limitación del firmware.
- Se recomienda hacer una copia de seguridad de tus archivos SDX antes de editarlos.
- El editor muestra una advertencia si intentas cerrar la aplicación con cambios sin guardar.

## Testing

El proyecto incluye un conjunto completo de pruebas unitarias para validar la funcionalidad principal.

### Ejecutar las pruebas

```bash
# Instalar dependencias de desarrollo
pip install -r requirements-dev.txt

# Ejecutar todas las pruebas
pytest

# Ejecutar pruebas con más detalles
pytest -v

# Ejecutar pruebas con cobertura
pytest --cov=channel_processor --cov-report=html
```

### Estructura de pruebas

```
tests/
├── fixtures/           # Archivos de ejemplo para pruebas
│   ├── sample.chl
│   └── sample_kingofsat.html
└── unit/              # Pruebas unitarias
    ├── test_chl_parsing.py              # Parsing de archivos CHL
    ├── test_chl_to_sdx_conversion.py    # Conversión CHL a SDX
    ├── test_kingofsat_parsing.py        # Parsing de HTML de KingOfSat
    ├── test_sdx_processing.py           # Procesamiento de datos SDX
    └── test_utils.py                    # Funciones de utilidad
```

Las pruebas cubren:
- ✅ Parsing de archivos CHL y extracción de datos
- ✅ Conversión de formato CHL a SDX
- ✅ Parsing de HTML de KingOfSat
- ✅ Procesamiento de datos SDX
- ✅ Mapeo de tipos de servicio, codecs de video, y códigos de idioma
- ✅ Detección de canales HD, cifrados y UHD

## Licencia

Este proyecto es de código abierto. Siéntete libre de usarlo, modificarlo y compartirlo.

## Contribuciones

Las contribuciones son bienvenidas. Si encuentras algún error o tienes alguna sugerencia, no dudes en abrir un issue o enviar un pull request.
