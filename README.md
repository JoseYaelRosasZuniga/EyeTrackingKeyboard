# EyeTracking 

Aplicación que permite escribir texto utilizando la mirada, empleando visión por computadora y sugerencias inteligentes de palabras en español. El sistema utiliza una webcam y la biblioteca MediaPipe para el seguimiento ocular, junto con una interfaz gráfica desarrollada en Pygame.

## Características

- **Teclado virtual** controlado por la mirada.
- **Sugerencias de palabras** en español, basadas en el texto actual.
- **Selección por parpadeo** o permanencia de la mirada (dwell).
- **Calibración interactiva** para adaptar el sistema a cada usuario y entorno.
- **Retroalimentación auditiva** (sonidos y síntesis de voz).
- **Soporte para síntesis de voz** (requiere `pyttsx3`).

## Uso y sugerencias 
Archivos principales
main.py: Punto de entrada de la aplicación.
eye_tracker.py: Seguimiento ocular usando MediaPipe.
keyboard_ui.py: Lógica y renderizado del teclado virtual.
word_suggester.py: Sugerencias de palabras en español.
calibration.py: Calibración personalizada del área de interacción.
config.py: Parámetros de configuración y constantes.
palabras_es.txt: Diccionario de palabras en español para sugerencias.
Uso
Ejecuta el programa principal:
python main.py
Sigue las instrucciones en pantalla para calibrar el sistema.
Utiliza tu mirada para seleccionar teclas o sugerencias.
Parpadea para confirmar la selección (o espera el tiempo de dwell, según configuración).

Personalización
Puedes modificar el archivo palabras_es.txt para agregar o quitar palabras sugeridas.
Ajusta parámetros visuales y de interacción en config.py.

Créditos
Basado en tecnologías de MediaPipe y Pygame.

## Requisitos

- Python 3.8 o superior
- Webcam funcional
- Dependencias Python:
  - `pygame`
  - `opencv-python`
  - `mediapipe`
  - `numpy`
  - `pyttsx3` (opcional, para síntesis de voz)
  - 
Instala las dependencias con:

```sh
pip install pygame opencv-python mediapipe numpy pyttsx3
