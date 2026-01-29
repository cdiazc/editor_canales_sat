# Guía de Contribución

¡Gracias por tu interés en contribuir al Editor de Canales SAT! Este documento te guiará en el proceso de contribución.

## Tabla de Contenidos

- [Configuración del Entorno de Desarrollo](#configuración-del-entorno-de-desarrollo)
- [Ejecutar el Proyecto](#ejecutar-el-proyecto)
- [Ejecutar las Pruebas](#ejecutar-las-pruebas)
- [Realizar Cambios](#realizar-cambios)
- [Enviar una Pull Request](#enviar-una-pull-request)
- [Estándares de Código](#estándares-de-código)

## Configuración del Entorno de Desarrollo

1. **Fork el repositorio** en GitHub

2. **Clona tu fork localmente**:
   ```bash
   git clone https://github.com/TU_USUARIO/editor_canales_sat.git
   cd editor_canales_sat
   ```

3. **Configura el repositorio upstream**:
   ```bash
   git remote add upstream https://github.com/cdiazc/editor_canales_sat.git
   ```

4. **Instala las dependencias de desarrollo**:
   ```bash
   pip install -r requirements-dev.txt
   ```

## Ejecutar el Proyecto

Para ejecutar la aplicación:

```bash
python3 editor_canales.py
```

## Ejecutar las Pruebas

Siempre ejecuta las pruebas antes de enviar tu Pull Request:

```bash
# Ejecutar todas las pruebas
pytest

# Ejecutar con verbosidad
pytest -v

# Ejecutar con cobertura
pytest --cov=channel_processor --cov-report=html

# Ejecutar pruebas específicas
pytest tests/unit/test_chl_parsing.py
```

## Realizar Cambios

1. **Crea una rama para tu cambio**:
   ```bash
   git checkout -b feature/mi-nueva-caracteristica
   ```
   o
   ```bash
   git checkout -b fix/mi-correccion
   ```

2. **Realiza tus cambios**

3. **Si añades nueva funcionalidad, añade pruebas**:
   - Las pruebas deben ir en `tests/unit/`
   - Sigue el formato existente de las pruebas
   - Asegúrate de que la cobertura se mantiene por encima del 90%

4. **Ejecuta las pruebas**:
   ```bash
   pytest -v
   ```

5. **Verifica la cobertura de código**:
   ```bash
   pytest --cov=channel_processor --cov-report=term-missing
   ```

## Enviar una Pull Request

1. **Confirma tus cambios**:
   ```bash
   git add .
   git commit -m "Descripción clara de los cambios"
   ```

2. **Sincroniza con upstream**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

3. **Push a tu fork**:
   ```bash
   git push origin feature/mi-nueva-caracteristica
   ```

4. **Abre una Pull Request** en GitHub desde tu fork al repositorio principal

5. **Describe tus cambios** en la Pull Request:
   - ¿Qué problema resuelve?
   - ¿Cómo lo probaste?
   - ¿Añadiste nuevas pruebas?

## Estándares de Código

### Python

- Usa **4 espacios** para la indentación (no tabs)
- Nombres de variables y funciones en **snake_case**
- Nombres de clases en **PascalCase**
- Incluye **docstrings** para funciones y clases públicas
- Longitud máxima de línea: **100 caracteres** (preferiblemente)

### Documentación

- Los comentarios deben ser claros y concisos
- Usa español para comentarios y documentación
- Actualiza el README.md si cambias la funcionalidad

### Pruebas

- **SIEMPRE** añade pruebas para nueva funcionalidad
- Las pruebas deben ser:
  - **Aisladas**: No depender de estado externo
  - **Rápidas**: Ejecutarse en menos de 1 segundo
  - **Deterministas**: Siempre producir el mismo resultado
  - **Descriptivas**: Nombres claros que expliquen qué prueban

Ejemplo de una buena prueba:

```python
def test_parse_chl_file_with_invalid_json(self, tmp_path):
    """Test parsing CHL file with some invalid JSON (should skip bad lines)."""
    invalid_file = tmp_path / "invalid.chl"
    content = '''{"Type": "sat", "Index": 0, "Name": "Test Sat"}
Invalid JSON line here
{"Type": "ch", "Index": 0, "Name": "Test Channel"}
'''
    invalid_file.write_text(content)
    
    result = ChannelDataProcessor.parse_chl_file(str(invalid_file))
    
    # Should still parse valid objects
    assert len(result['satellites']) == 1
    assert len(result['channels']) == 1
```

### Estructura del Módulo de Pruebas

Cuando añadas nuevas funciones al `channel_processor.py`:

1. Crea pruebas unitarias en el archivo apropiado en `tests/unit/`
2. Agrupa las pruebas relacionadas en clases
3. Usa fixtures de pytest para datos de prueba reutilizables
4. Prueba casos de éxito, casos de error y casos límite

## Tipos de Contribuciones

### 🐛 Reportar Bugs

- Usa el Issue Tracker de GitHub
- Describe el problema claramente
- Incluye pasos para reproducir
- Indica la versión de Python y sistema operativo
- Si es posible, proporciona un archivo de prueba

### ✨ Solicitar Características

- Abre un Issue describiendo la característica
- Explica el caso de uso
- Discute la implementación antes de comenzar a codificar

### 📝 Mejorar Documentación

- Corrige errores tipográficos
- Mejora explicaciones
- Añade ejemplos
- Traduce documentación

### 🧪 Añadir Pruebas

- Aumenta la cobertura de código
- Añade casos de prueba que faltan
- Mejora la calidad de las pruebas existentes

## Proceso de Revisión

1. Un mantenedor revisará tu Pull Request
2. Puede solicitar cambios o aclaraciones
3. Una vez aprobado, se fusionará a la rama principal
4. Tu contribución aparecerá en la próxima versión

## Código de Conducta

- Sé respetuoso con otros contribuidores
- Acepta críticas constructivas
- Enfócate en lo que es mejor para la comunidad
- Muestra empatía hacia otros miembros de la comunidad

## Preguntas

Si tienes preguntas, puedes:
- Abrir un Issue en GitHub
- Contactar a los mantenedores

¡Gracias por contribuir! 🎉
